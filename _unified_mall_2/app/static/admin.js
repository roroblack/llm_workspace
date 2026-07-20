document.getElementById("adminLoginBtn").addEventListener("click", async () => {
  const username = document.getElementById("adminUsername").value.trim();
  const password = document.getElementById("adminPassword").value;
  const form = new URLSearchParams({ username, password });
  const { status, body } = await apiFetch("/auth/login", { method: "POST", body: form });
  if (body && body.access_token) {
    setAuth(body.access_token, username);
    updateAuthStatusBar();
  }
  renderResult(document.getElementById("loginResult"), status, body);
});

document.getElementById("logoutBtn").addEventListener("click", () => {
  clearAuth();
  updateAuthStatusBar();
  document.getElementById("loginResult").textContent = "로그아웃됨 — 다음 호출은 401(미인증)이 됩니다.";
});

document.querySelectorAll("[data-path]").forEach((btn) => {
  btn.addEventListener("click", async () => {
    const { status, body } = await apiFetch(btn.dataset.path, { headers: authHeaders() });
    renderResult(document.getElementById("adminResult"), status, body);
  });
});
