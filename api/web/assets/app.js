const $ = (id) => document.getElementById(id);
const views = ["login-view", "dashboard-view", "setup-view"];
function show(view) { views.forEach((id) => { $(id).hidden = id !== view; }); }
async function request(path, options = {}) {
  const response = await fetch(path, {
    credentials: "same-origin",
    ...options,
    headers: { "Content-Type": "application/json", ...(options.headers || {}) }
  });
  const data = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(data.detail || "Request gagal");
  return data;
}
async function init() {
  try {
    const state = await request("/api/auth/me");
    if (!state.configured) return show("setup-view");
    show(state.authenticated ? "dashboard-view" : "login-view");
  } catch { show("setup-view"); }
}
$("login-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  $("login-error").textContent = "";
  const button = $("login-form").querySelector("button");
  button.disabled = true;
  try {
    await request("/api/auth/login", {
      method: "POST",
      body: JSON.stringify({ password: $("password").value })
    });
    $("password").value = "";
    show("dashboard-view");
  } catch (error) {
    $("login-error").textContent = error.message;
  } finally { button.disabled = false; }
});
$("logout-button").addEventListener("click", async () => {
  try { await request("/api/auth/logout", { method: "POST", body: "{}" }); }
  finally { show("login-view"); }
});
init();
