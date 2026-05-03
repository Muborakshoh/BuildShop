const shiftStateNode = document.getElementById("shift-state");
const productsNode = document.getElementById("cash-products");
const receiptNode = document.getElementById("receipt-items");
const totalNode = document.getElementById("receipt-total");
const messageNode = document.getElementById("message");
const summaryNode = document.getElementById("shift-summary");

let currentShift = null;
let receipt = [];

function showMessage(text) {
  messageNode.textContent = text || "";
}

function receiptTotal() {
  return receipt.reduce((sum, item) => sum + Number(item.price) * item.quantity, 0);
}

function renderShift() {
  if (!currentShift) {
    shiftStateNode.textContent = "Смена закрыта или не открыта";
    return;
  }
  shiftStateNode.textContent = `${currentShift.register_name}: открыта ${new Date(currentShift.opened_at).toLocaleString("ru-RU")}, ожидаемые наличные ${money(currentShift.expected_cash)}`;
}

function renderReceipt() {
  if (!receipt.length) {
    receiptNode.innerHTML = '<p class="muted">Чек пуст.</p>';
    totalNode.textContent = money(0);
    return;
  }
  receiptNode.innerHTML = receipt
    .map(
      (item) => `
        <div class="cart-item">
          <strong>${item.name}</strong>
          <input type="number" min="1" value="${item.quantity}" data-id="${item.product_id}" />
          <span>${money(item.price)}</span>
          <button data-remove="${item.product_id}">Убрать</button>
        </div>
      `,
    )
    .join("");
  totalNode.textContent = money(receiptTotal());

  receiptNode.querySelectorAll("input[data-id]").forEach((input) => {
    input.addEventListener("change", () => {
      receipt = receipt.map((item) =>
        item.product_id === Number(input.dataset.id) ? { ...item, quantity: Math.max(1, Number(input.value)) } : item,
      );
      renderReceipt();
    });
  });
  receiptNode.querySelectorAll("button[data-remove]").forEach((button) => {
    button.addEventListener("click", () => {
      receipt = receipt.filter((item) => item.product_id !== Number(button.dataset.remove));
      renderReceipt();
    });
  });
}

function addProduct(product) {
  const existing = receipt.find((item) => item.product_id === product.id);
  if (existing) {
    existing.quantity += 1;
  } else {
    receipt.push({ product_id: product.id, name: product.name, price: product.price, quantity: 1 });
  }
  renderReceipt();
}

async function loadCurrentShift() {
  try {
    currentShift = await API.request("/api/cashier/shifts/current");
  } catch {
    currentShift = null;
  }
  renderShift();
}

async function findProducts() {
  const query = document.getElementById("product-search").value;
  const products = await API.request(`/api/products?search=${encodeURIComponent(query)}&in_stock=true&limit=12`);
  if (!products.length) {
    productsNode.innerHTML = '<p class="muted">Ничего не найдено.</p>';
    return;
  }
  productsNode.innerHTML = products
    .map(
      (product) => `
        <button class="cash-product" data-id="${product.id}">
          <strong>${product.name}</strong>
          <span>${money(product.price)}</span>
          <small>Остаток: ${product.stock_quantity}</small>
        </button>
      `,
    )
    .join("");
  productsNode.querySelectorAll("button[data-id]").forEach((button) => {
    button.addEventListener("click", () => {
      const product = products.find((item) => item.id === Number(button.dataset.id));
      addProduct(product);
    });
  });
}

document.getElementById("open-shift").addEventListener("click", async () => {
  showMessage("");
  try {
    currentShift = await API.request("/api/cashier/shifts/open", {
      method: "POST",
      body: JSON.stringify({
        register_name: document.getElementById("register-name").value,
        opening_cash: document.getElementById("opening-cash").value || "0",
      }),
    });
    renderShift();
  } catch (error) {
    showMessage(error.message);
  }
});

document.getElementById("find-product").addEventListener("click", () => {
  findProducts().catch((error) => showMessage(error.message));
});

document.getElementById("product-search").addEventListener("keydown", (event) => {
  if (event.key === "Enter") findProducts().catch((error) => showMessage(error.message));
});

document.getElementById("submit-receipt").addEventListener("click", async () => {
  showMessage("");
  if (!currentShift) {
    showMessage("Сначала откройте смену.");
    return;
  }
  const total = receiptTotal();
  const method = document.getElementById("payment-method").value;
  const payload = {
    payment_method: method,
    cash_amount: method === "cash" ? String(total) : document.getElementById("cash-amount").value || "0",
    card_amount: method === "card" ? String(total) : document.getElementById("card-amount").value || "0",
    comment: document.getElementById("cash-comment").value || null,
    items: receipt.map((item) => ({ product_id: item.product_id, quantity: item.quantity })),
  };
  try {
    const operation = document.getElementById("operation-type").value;
    const transaction = await API.request(`/api/cashier/${operation}`, {
      method: "POST",
      body: JSON.stringify(payload),
    });
    receipt = [];
    renderReceipt();
    await loadCurrentShift();
    showMessage(`Чек ${transaction.receipt_number} создан.`);
  } catch (error) {
    showMessage(error.message);
  }
});

document.getElementById("close-shift").addEventListener("click", async () => {
  showMessage("");
  if (!currentShift) {
    showMessage("Нет открытой смены.");
    return;
  }
  try {
    const closed = await API.request(`/api/cashier/shifts/${currentShift.id}/close`, {
      method: "POST",
      body: JSON.stringify({ actual_cash: document.getElementById("actual-cash").value || "0" }),
    });
    currentShift = closed;
    renderShift();
    const summary = await API.request(`/api/cashier/shifts/${closed.id}/summary`);
    summaryNode.innerHTML = `
      <p>Продажи: <strong>${money(summary.sales_total)}</strong></p>
      <p>Возвраты: <strong>${money(summary.refunds_total)}</strong></p>
      <p>Наличные: <strong>${money(summary.cash_total)}</strong></p>
      <p>Карта: <strong>${money(summary.card_total)}</strong></p>
      <p>Чеков: <strong>${summary.receipt_count}</strong></p>
    `;
  } catch (error) {
    showMessage(error.message);
  }
});

loadCurrentShift();
renderReceipt();
