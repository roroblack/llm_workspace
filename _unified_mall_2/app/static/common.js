// 공용 인증/요청 헬퍼 — 데모 프론트엔드 전 페이지가 공유한다.
// 토큰은 localStorage에 저장(로컬 데모 서버 전제, 프로덕션 보안모델 아님).

// --- 브랜드명 단일 소스(프론트엔드) ---
// 몰 이름을 바꾸려면 이 값 하나만 바꾸면 모든 페이지 타이틀/헤더에 반영된다.
// 백엔드(프롬프트·API 타이틀)는 app/core/config.py의 BRAND_NAME이 대응하는 단일 소스다.
const BRAND_NAME = "바로봄";

// 타이틀의 {{BRAND}} 토큰과 [data-brand] 요소에 브랜드명을 주입한다.
function applyBrand() {
  if (document.title.includes("{{BRAND}}")) {
    document.title = document.title.split("{{BRAND}}").join(BRAND_NAME);
  }
  document.querySelectorAll("[data-brand]").forEach((el) => {
    el.textContent = BRAND_NAME;
  });
}
document.addEventListener("DOMContentLoaded", applyBrand);

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

// --- 음성 STT/TTS 공용 헬퍼 (Phase 11) ---
// STT/TTS는 /api/voice/*를 그대로 호출한다 — 페이지마다 따로 구현하지 않고 여기서 공유.

function transcribeBlob(blob) {
  const form = new FormData();
  form.append("audio", blob, "recording.webm");
  return apiFetch("/api/voice/stt", { method: "POST", body: form });
}

async function synthesizeAndPlay(text) {
  const resp = await fetch("/api/voice/tts", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text }),
  });
  if (!resp.ok) {
    let body;
    try { body = await resp.json(); } catch { body = null; }
    const err = new Error((body && body.message) || `TTS 요청 실패: HTTP ${resp.status}`);
    err.status = resp.status;
    throw err;
  }
  const blob = await resp.blob();
  const url = URL.createObjectURL(blob);
  const audio = new Audio(url);
  audio.addEventListener("ended", () => URL.revokeObjectURL(url));
  await audio.play();
  return audio;
}

// 마이크 버튼 하나로 녹음 시작/종료를 토글하는 헬퍼.
// onResult(text)/onError(err)/onStateChange("idle"|"recording"|"transcribing")를 받는다.
// 마이크 권한 거부는 조용히 넘어가지 않고 onError로 명시 전달한다(무폴백).
function createVoiceRecorder({ onResult, onError, onStateChange }) {
  let mediaRecorder = null;
  let chunks = [];
  let recording = false;

  function setState(state) {
    if (onStateChange) onStateChange(state);
  }

  async function start() {
    let stream;
    try {
      stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    } catch (err) {
      onError(new Error("마이크 권한이 거부되었거나 사용할 수 없습니다: " + err.message));
      return;
    }
    chunks = [];
    mediaRecorder = new MediaRecorder(stream);
    mediaRecorder.ondataavailable = (e) => { if (e.data.size > 0) chunks.push(e.data); };
    mediaRecorder.onstop = async () => {
      stream.getTracks().forEach((t) => t.stop());
      setState("transcribing");
      try {
        const blob = new Blob(chunks, { type: mediaRecorder.mimeType || "audio/webm" });
        const { status, ok, body } = await transcribeBlob(blob);
        if (!ok) {
          throw new Error((body && body.message) || `STT 요청 실패: HTTP ${status}`);
        }
        onResult(body.text);
      } catch (err) {
        onError(err);
      } finally {
        setState("idle");
      }
    };
    mediaRecorder.start();
    recording = true;
    setState("recording");
  }

  function stop() {
    if (mediaRecorder && recording) {
      mediaRecorder.stop();
      recording = false;
    }
  }

  return {
    toggle() {
      if (recording) stop(); else start();
    },
    isRecording() { return recording; },
  };
}
