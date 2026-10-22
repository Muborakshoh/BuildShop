(async function () {
  const user = await API.ensureRole(["admin", "manager"]);
  if (!user) return;

  const container = document.getElementById("dashboard-content");

  try {
    const [dashboard, orders, products] = await Promise.all([
      API.request("/api/cms/reports/dashboard"),
      API.request("/api/orders?limit=100"),
      API.request("/api/products?limit=500"),
    ]);

    // Calculate stats
    const totalRevenue = orders.reduce((s, o) => s + parseFloat(o.total_amount), 0);
    const avgCheck = orders.length ? totalRevenue / orders.length : 0;
    const completedOrders = orders.filter((o) => o.status === "completed").length;

    // Low stock products
    const lowStock = products.filter((p) => p.stock_quantity <= 5 && p.stock_quantity >= 0).sort((a, b) => a.stock_quantity - b.stock_quantity).slice(0, 10);

    // Revenue by day (last 30 days)
    const revenueByDay = {};
    const now = new Date();
    for (let i = 29; i >= 0; i--) {
      const d = new Date(now);
      d.setDate(d.getDate() - i);
      revenueByDay[d.toISOString().slice(0, 10)] = 0;
    }
    orders.forEach((o) => {
      const day = o.created_at.slice(0, 10);
      if (revenueByDay[day] !== undefined) revenueByDay[day] += parseFloat(o.total_amount);
    });

    // Orders by status
    const statusCounts = {};
    orders.forEach((o) => {
      statusCounts[o.status] = (statusCounts[o.status] || 0) + 1;
    });

    // Build HTML
    let html = `
    <div class="dashboard-grid">
      <div class="stat-card"><div class="stat-value">${dashboard.products}</div><div class="stat-label">Товаров</div></div>
      <div class="stat-card"><div class="stat-value">${orders.length}</div><div class="stat-label">Заказов</div></div>
      <div class="stat-card"><div class="stat-value">${money(totalRevenue)}</div><div class="stat-label">Выручка</div></div>
      <div class="stat-card"><div class="stat-value">${money(avgCheck)}</div><div class="stat-label">Средний чек</div></div>
      <div class="stat-card"><div class="stat-value">${dashboard.page_views}</div><div class="stat-label">Просмотров</div></div>
      <div class="stat-card"><div class="stat-value">${dashboard.products_without_stock}</div><div class="stat-label">Нет в наличии</div></div>
    </div>

    <div class="chart-container">
      <h3>📈 Выручка за 30 дней</h3>
      <canvas id="revenue-chart"></canvas>
    </div>

    <div class="two-cols">
      <div class="chart-container">
        <h3>🏆 Топ-10 товаров</h3>
        <ul class="top-list">
          ${dashboard.popular_products.map((p) => `<li><span>${escapeHtml(p.name)}</span><span class="count">${p.sold} шт</span></li>`).join("")}
        </ul>
      </div>
      <div class="chart-container">
        <h3>📦 Заказы по статусу</h3>
        <canvas id="status-chart" style="max-height:200px"></canvas>
      </div>
    </div>`;

    if (dashboard.search_queries.length) {
      html += `<div class="chart-container">
        <h3>🔍 Популярные запросы</h3>
        <ul class="top-list">
          ${dashboard.search_queries.map((q) => `<li><span>"${escapeHtml(q.query)}"</span><span class="count">${q.count}</span></li>`).join("")}
        </ul>
      </div>`;
    }

    if (lowStock.length) {
      html += `<div class="low-stock">
        <h3>⚠️ Мало на складе</h3>
        ${lowStock.map((p) => `<div class="low-stock-item"><span>${escapeHtml(ml(p, "name"))}</span><span class="stock-warn">${p.stock_quantity} шт</span></div>`).join("")}
      </div>`;
    }

    container.innerHTML = html;

    // Revenue chart
    const revenueCtx = document.getElementById("revenue-chart");
    if (revenueCtx) {
      new Chart(revenueCtx, {
        type: "line",
        data: {
          labels: Object.keys(revenueByDay).map((d) => d.slice(5)),
          datasets: [{
            label: "Выручка (TJS)",
            data: Object.values(revenueByDay),
            borderColor: "#2563eb",
            backgroundColor: "rgba(37,99,235,0.1)",
            fill: true,
            tension: 0.3,
          }],
        },
        options: {
          responsive: true,
          plugins: { legend: { display: false } },
          scales: { y: { beginAtZero: true } },
        },
      });
    }

    // Status pie chart
    const statusCtx = document.getElementById("status-chart");
    if (statusCtx && Object.keys(statusCounts).length) {
      const statusColors = {
        created: "#60a5fa", confirmed: "#34d399", assembling: "#fbbf24",
        delivering: "#a78bfa", delivered: "#818cf8", completed: "#22c55e", cancelled: "#ef4444",
      };
      new Chart(statusCtx, {
        type: "doughnut",
        data: {
          labels: Object.keys(statusCounts),
          datasets: [{
            data: Object.values(statusCounts),
            backgroundColor: Object.keys(statusCounts).map((s) => statusColors[s] || "#94a3b8"),
          }],
        },
        options: {
          responsive: true,
          plugins: { legend: { position: "bottom" } },
        },
      });
    }

  } catch (e) {
    container.innerHTML = `<p class="muted">${escapeHtml(e.message)}</p>`;
  }
})();
