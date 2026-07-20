// 공용 인증/요청 헬퍼 — 데모 프론트엔드 전 페이지가 공유한다.
// 토큰은 localStorage에 저장(로컬 데모 서버 전제, 프로덕션 보안모델 아님).

const AUTH_KEY = "mall_demo_token";
const USER_KEY = "mall_demo_username";

function getToken() { return localStorage.getItem(AUTH_KEY) || ""; }
function getUsername() { return localStorage.getItem(USER_KEY) || ""; }
function setAuth(token, username) {
  localStorage.setItem(AUTH_KEY, token);
  localStorage.setItem(USER_KEY, username);
}
function clearAuth() {
  localStorage.removeItem(AUTH_KEY);
  localStorage.removeItem(USER_KEY);
}

function authHeaders(extra) {
  const h = Object.assign({}, extra || {});
  const t = getToken();
  if (t) h["Authorization"] = "Bearer " + t;
  return h;
}

async function apiFetch(path, opts) {
  opts = opts || {};
  const resp = await fetch(path, opts);
  let body;
  try { body = await resp.json(); } catch { body = null; }
  return { status: resp.status, ok: resp.ok, body };
}

function renderResult(el, status, body) {
  const badgeClass = status < 300 ? "ok" : status < 500 ? "warn" : "err";
  el.innerHTML = "";
  const badge = document.createElement("span");
  badge.className = "badge " + badgeClass;
  badge.textContent = "HTTP " + status;
  el.appendChild(badge);
  const pre = document.createElement("pre");
  pre.className = "result";
  pre.textContent = JSON.stringify(body, null, 2);
  el.appendChild(pre);
}

function updateAuthStatusBar() {
  const bar = document.getElementById("authStatusBar");
  if (!bar) return;
  const u = getUsername();
  bar.innerHTML = u
    ? `로그인됨: <strong>${u}</strong> · <a href="#" id="logoutLink">로그아웃</a>`
    : `로그인 안 됨 (각 페이지의 로그인 폼 이용)`;
  const logout = document.getElementById("logoutLink");
  if (logout) {
    logout.addEventListener("click", (e) => {
      e.preventDefault();
      clearAuth();
      updateAuthStatusBar();
    });
  }
}

document.addEventListener("DOMContentLoaded", updateAuthStatusBar);
