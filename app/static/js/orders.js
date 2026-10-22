const STATUS_LABELS = {
  created: "order_status_created",
  confirmed: "order_status_confirmed",
  assembling: "order_status_assembling",
  delivering: "order_status_delivering",
  delivered: "order_status_delivered",
  completed: "order_status_completed",
  cancelled: "order_status_cancelled",
};

const STATUS_FLOW = ["created", "confirmed", "assembling", "delivering", "delivered", "completed"];

function statusBadgeClass(s) {
  if (s === "completed" || s === "delivered") return "badge--green";
  if (s === "cancelled") return "badge--red";
  return "badge--blue";
}

function renderProgressBar(currentStatus) {
  if (currentStatus === "cancelled") {
    return '<div class="order-progress cancelled"><span class="progress-label">' + escapeHtml(t("order_status_cancelled")) + '</span></div>';
  }
  var idx = STATUS_FLOW.indexOf(currentStatus);
  if (idx === -1) idx = 0;
  var html = '<div class="order-progress">';
  for (var i = 0; i < STATUS_FLOW.length; i++) {
    var s = STATUS_FLOW[i];
    var cls = "progress-step";
    if (i < idx) cls += " done";
    else if (i === idx) cls += " active";
    html += '<div class="' + cls + '"><div class="progress-dot"></div><div class="progress-text">' + escapeHtml(t(STATUS_LABELS[s] || s)) + '</div></div>';
  }
  html += '</div>';
  return html;
}

function renderHistory(history) {
  if (!history || !history.length) return "";
  var html = '<details class="order-history"><summary>' + escapeHtml(t("order_history")) + '</summary><ul>';
  history.forEach(function (h) {
    var date = new Date(h.changed_at).toLocaleString();
    var from = h.old_status ? t(STATUS_LABELS[h.old_status] || h.old_status) : "—";
    var to = t(STATUS_LABELS[h.new_status] || h.new_status);
    html += '<li><span class="hist-date">' + date + '</span> ';
    html += from + ' → <strong>' + escapeHtml(to) + '</strong>';
    if (h.comment) html += ' <span class="hist-comment">(' + escapeHtml(h.comment) + ')</span>';
    html += '</li>';
  });
  html += '</ul></details>';
  return html;
}

function canCancel(status) {
  return ["created", "confirmed"].indexOf(status) !== -1;
}

async function cancelOrder(orderId) {
  if (!confirm(t("order_cancel_confirm"))) return;
  try {
    await API.request("/api/orders/" + orderId + "/status", {
      method: "PATCH",
      body: JSON.stringify({ status: "cancelled", comment: t("order_cancelled_by_user") }),
    });
    showToast(t("order_cancelled"), "success");
    loadOrders();
  } catch (e) {
    showToast(e.message, "error");
  }
}

// Admin: change status
async function changeStatus(orderId, newStatus) {
  try {
    await API.request("/api/orders/" + orderId + "/status", {
      method: "PATCH",
      body: JSON.stringify({ status: newStatus }),
    });
    showToast(t("order_status_updated"), "success");
    loadOrders();
  } catch (e) {
    showToast(e.message, "error");
  }
}

function adminControls(order) {
  var user = API._user;
  if (!user || user.role !== "admin") return "";
  var nextMap = {
    created: "confirmed",
    confirmed: "assembling",
    assembling: "delivering",
    delivering: "delivered",
    delivered: "completed",
  };
  var next = nextMap[order.status];
  if (!next && order.status !== "cancelled") return "";
  var html = '<div class="admin-order-controls">';
  if (next) {
    html += '<button class="btn btn-primary btn-sm" onclick="changeStatus(' + order.id + ',\'' + next + '\')">';
    html += '→ ' + escapeHtml(t(STATUS_LABELS[next])) + '</button>';
  }
  if (canCancel(order.status)) {
    html += ' <button class="btn btn-danger btn-sm" onclick="cancelOrder(' + order.id + ')">' + escapeHtml(t("order_cancel")) + '</button>';
  }
  html += '</div>';
  return html;
}

async function loadOrders() {
  var root = document.getElementById("orders-list");
  if (!API.token) {
    window.location.href = "/pages/auth.html";
    return;
  }
  try {
    var orders = await API.request("/api/orders");
    if (!orders.length) {
      root.innerHTML = '<div class="empty-state"><h3>' + escapeHtml(t("orders_empty")) + '</h3>' +
        '<a href="/pages/products.html" class="btn btn-primary" style="margin-top:16px">' + escapeHtml(t("nav_products")) + '</a></div>';
      return;
    }
    root.innerHTML = orders.map(function (order) {
      return '<article class="order-card slide-up">' +
        '<div class="order-card-head">' +
          '<strong>#' + order.id + '</strong>' +
          '<span class="badge ' + statusBadgeClass(order.status) + '">' + escapeHtml(t(STATUS_LABELS[order.status] || order.status)) + '</span>' +
        '</div>' +
        renderProgressBar(order.status) +
        '<p class="muted">' + escapeHtml(new Date(order.created_at).toLocaleString()) + '</p>' +
        '<p>' + escapeHtml(t("delivery_method_" + order.delivery_method)) + ': ' + escapeHtml(order.delivery_address) + '</p>' +
        (order.phone ? '<p>' + escapeHtml(t("phone")) + ': ' + escapeHtml(order.phone) + '</p>' : '') +
        (order.comment ? '<p>' + escapeHtml(t("comment")) + ': ' + escapeHtml(order.comment) + '</p>' : '') +
        '<ul class="order-items">' +
          order.items.map(function (item) { return '<li>' + item.quantity + ' × #' + item.product_id + ' — ' + money(item.unit_price * item.quantity) + '</li>'; }).join('') +
        '</ul>' +
        '<div class="order-total">' + escapeHtml(t("cart_total")) + ' ' + money(order.total_amount) + '</div>' +
        renderHistory(order.status_history) +
        (canCancel(order.status) && (!API._user || API._user.role !== "admin") ?
          '<button class="btn btn-danger btn-sm" style="margin-top:8px" onclick="cancelOrder(' + order.id + ')">' + escapeHtml(t("order_cancel")) + '</button>' : '') +
        adminControls(order) +
      '</article>';
    }).join('');
  } catch (e) {
    root.innerHTML = '<p class="muted">' + escapeHtml(e.message) + '</p>';
  }
}

loadOrders();
