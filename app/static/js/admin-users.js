const usersBody = document.getElementById("users-body");
const messageNode = document.getElementById("message");
const modalRoot = document.getElementById("modal-root");

const ROLE_BADGES = {
  admin: "badge--purple",
  manager: "badge--blue",
  seller: "badge--orange",
  buyer: "badge--green",
  user: "badge--gray",
};

function roleName(role) {
  return t("role_" + role) || role;
}

async function loadUsers() {
  try {
    const users = await API.request("/api/users");
    usersBody.innerHTML = users.map((u) => `
      <tr>
        <td>${u.id}</td>
        <td>${u.full_name}</td>
        <td>${u.email}</td>
        <td><span class="badge ${ROLE_BADGES[u.role] || "badge--gray"}">${roleName(u.role)}</span></td>
        <td><span class="badge ${u.is_active ? "badge--green" : "badge--danger"}">${u.is_active ? t("active") : t("blocked")}</span></td>
        <td class="actions-cell">
          <button class="btn-outline btn-sm" onclick="editUser(${u.id})">${t("edit")}</button>
          <button class="btn-danger btn-sm" onclick="deleteUser(${u.id})">${t("delete_btn")}</button>
        </td>
      </tr>
    `).join("");
  } catch (e) {
    messageNode.textContent = e.message;
  }
}

function showModal(html) {
  modalRoot.innerHTML = `<div class="modal-overlay" onclick="if(event.target===this)closeModal()"><div class="modal">${html}</div></div>`;
}

function closeModal() {
  modalRoot.innerHTML = "";
}

document.getElementById("add-user-btn").addEventListener("click", () => {
  showModal(`
    <h2>${t("add_user")}</h2>
    <input id="m-name" placeholder="${t("name")}" />
    <input id="m-email" type="email" placeholder="${t("email")}" />
    <input id="m-password" type="password" placeholder="${t("password_min")}" />
    <select id="m-role">
      <option value="buyer">${t("role_buyer")}</option>
      <option value="seller">${t("role_seller")}</option>
      <option value="manager">${t("role_manager")}</option>
      <option value="admin">${t("role_admin")}</option>
    </select>
    <div class="modal-actions">
      <button class="btn-outline" onclick="closeModal()">${t("cancel")}</button>
      <button onclick="createUser()">${t("save")}</button>
    </div>
  `);
});

async function createUser() {
  try {
    await API.request("/api/users", {
      method: "POST",
      body: JSON.stringify({
        full_name: document.getElementById("m-name").value,
        email: document.getElementById("m-email").value,
        password: document.getElementById("m-password").value,
        role: document.getElementById("m-role").value,
      }),
    });
    closeModal();
    messageNode.textContent = t("user_created");
    loadUsers();
  } catch (e) {
    messageNode.textContent = e.message;
  }
}

async function editUser(id) {
  const users = await API.request("/api/users");
  const u = users.find((x) => x.id === id);
  if (!u) return;
  showModal(`
    <h2>${t("edit")} — ${u.full_name}</h2>
    <input id="m-name" value="${u.full_name}" placeholder="${t("name")}" />
    <select id="m-role">
      ${["admin","manager","seller","buyer","user"].map((r) => `<option value="${r}" ${r===u.role?"selected":""}>${t("role_"+r)}</option>`).join("")}
    </select>
    <select id="m-active">
      <option value="true" ${u.is_active?"selected":""}>${t("active")}</option>
      <option value="false" ${!u.is_active?"selected":""}>${t("blocked")}</option>
    </select>
    <div class="modal-actions">
      <button class="btn-outline" onclick="closeModal()">${t("cancel")}</button>
      <button onclick="saveUser(${id})">${t("save")}</button>
    </div>
  `);
}

async function saveUser(id) {
  try {
    await API.request(`/api/users/${id}`, {
      method: "PATCH",
      body: JSON.stringify({
        full_name: document.getElementById("m-name").value,
        role: document.getElementById("m-role").value,
        is_active: document.getElementById("m-active").value === "true",
      }),
    });
    closeModal();
    messageNode.textContent = t("user_updated");
    loadUsers();
  } catch (e) {
    messageNode.textContent = e.message;
  }
}

async function deleteUser(id) {
  if (!confirm(t("confirm_delete_user"))) return;
  try {
    await API.request(`/api/users/${id}`, { method: "DELETE" });
    messageNode.textContent = t("user_deleted");
    loadUsers();
  } catch (e) {
    messageNode.textContent = e.message;
  }
}

loadUsers();
