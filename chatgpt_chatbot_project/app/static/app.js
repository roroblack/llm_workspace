// app/static/app.js
// ------------------------------------------------------------
// 챗봇 프론트엔드 동작을 담당하는 스크립트입니다.
// - 챗봇 창 열기/닫기
// - 설정 패널(모델, temperature, top_p, top_k, max_output_tokens, system instruction)
// - 이전 대화 기록을 포함한 문맥 유지
// - /api/chat 호출 및 응답 표시
// ------------------------------------------------------------

// localStorage에 설정을 저장할 때 사용할 키 이름입니다.
const SETTINGS_KEY = "chatgpt_chatbot_settings";

// 화면 요소들을 미리 찾아둡니다.
const chatIcon = document.getElementById("chatIcon");
const chatModal = document.getElementById("chatModal");
const closeButton = document.getElementById("closeButton");
const settingsButton = document.getElementById("settingsButton");
const settingsPanel = document.getElementById("settingsPanel");

const chatMessages = document.getElementById("chatMessages");
const chatForm = document.getElementById("chatForm");
const chatInput = document.getElementById("chatInput");
const sendButton = document.getElementById("sendButton");

// 설정 입력 요소들입니다.
const systemInstructionEl = document.getElementById("systemInstruction");
const modelSelectEl = document.getElementById("modelSelect");
const temperatureEl = document.getElementById("temperature");
const temperatureValueEl = document.getElementById("temperatureValue");
const topPEl = document.getElementById("topP");
const topPValueEl = document.getElementById("topPValue");
const topKEl = document.getElementById("topK");
const maxTokensEl = document.getElementById("maxTokens");
const reasoningEffortEl = document.getElementById("reasoningEffort");
const resetSettingsBtn = document.getElementById("resetSettings");
const saveSettingsBtn = document.getElementById("saveSettings");
const settingsStatusEl = document.getElementById("settingsStatus");

// 대화 기록을 담는 배열입니다. ({ role, content } 형태)
// 이 배열을 /api/chat 요청의 history로 보내 문맥을 유지합니다.
let history = [];

// 서버에서 받아온 기본 설정 정보를 저장합니다.
let serverConfig = {
    default_model: "gpt-4o-mini",
    available_models: ["gpt-4o-mini"],
    default_system_instruction: "",
    has_api_key: false,
};

// ------------------------------------------------------------
// 창 열기 / 닫기
// ------------------------------------------------------------

// 챗봇 열기 버튼을 누르면 모달을 표시하고 입력창에 포커스를 줍니다.
chatIcon.addEventListener("click", () => {
    chatModal.classList.remove("hidden");
    chatInput.focus();
});

// 닫기 버튼을 누르면 모달을 숨깁니다.
closeButton.addEventListener("click", () => {
    chatModal.classList.add("hidden");
});

// 설정 버튼을 누르면 설정 패널을 토글합니다.
settingsButton.addEventListener("click", () => {
    settingsPanel.classList.toggle("hidden");
});

// ------------------------------------------------------------
// 설정 값 읽기 / 쓰기
// ------------------------------------------------------------

// 현재 설정 입력값을 하나의 객체로 모아 반환합니다.
// 빈 값은 null로 처리하여 서버에서 기본값을 사용하도록 합니다.
function collectSettings() {
    // 숫자 입력을 안전하게 변환하는 도우미입니다. 비어 있으면 null을 반환합니다.
    const toNumberOrNull = (value) => {
        if (value === "" || value === null || value === undefined) return null;
        const n = Number(value);
        return Number.isNaN(n) ? null : n;
    };

    return {
        system_instruction: systemInstructionEl.value.trim() || null,
        model: modelSelectEl.value || null,
        temperature: toNumberOrNull(temperatureEl.value),
        top_p: toNumberOrNull(topPEl.value),
        top_k: toNumberOrNull(topKEl.value),
        max_output_tokens: toNumberOrNull(maxTokensEl.value),
        reasoning_effort: reasoningEffortEl.value || null,
    };
}

// 설정 객체를 화면 입력 요소에 반영합니다.
function applySettingsToForm(settings) {
    if (!settings) return;

    if (settings.system_instruction != null) {
        systemInstructionEl.value = settings.system_instruction;
    }
    if (settings.model) {
        modelSelectEl.value = settings.model;
    }
    if (settings.temperature != null) {
        temperatureEl.value = settings.temperature;
        temperatureValueEl.textContent = Number(settings.temperature).toFixed(1);
    }
    if (settings.top_p != null) {
        topPEl.value = settings.top_p;
        topPValueEl.textContent = Number(settings.top_p).toFixed(2);
    }
    if (settings.top_k != null) {
        topKEl.value = settings.top_k;
    }
    if (settings.max_output_tokens != null) {
        maxTokensEl.value = settings.max_output_tokens;
    }
    if (settings.reasoning_effort != null) {
        reasoningEffortEl.value = settings.reasoning_effort;
    }
}

// 설정을 localStorage에 저장합니다.
function saveSettings() {
    const settings = collectSettings();
    localStorage.setItem(SETTINGS_KEY, JSON.stringify(settings));
    showSettingsStatus("설정을 저장했습니다.");
}

// localStorage에서 설정을 불러옵니다. 없으면 null을 반환합니다.
function loadSettings() {
    const raw = localStorage.getItem(SETTINGS_KEY);
    if (!raw) return null;
    try {
        return JSON.parse(raw);
    } catch (e) {
        return null;
    }
}

// 설정을 서버 기본값으로 되돌립니다.
function resetSettings() {
    systemInstructionEl.value = serverConfig.default_system_instruction || "";
    modelSelectEl.value = serverConfig.default_model || "";
    temperatureEl.value = 0.7;
    temperatureValueEl.textContent = "0.7";
    topPEl.value = 1;
    topPValueEl.textContent = "1.00";
    topKEl.value = "";
    maxTokensEl.value = "";
    reasoningEffortEl.value = "";
    localStorage.removeItem(SETTINGS_KEY);
    showSettingsStatus("기본값으로 되돌렸습니다.");
}

// 설정 상태 안내 문구를 잠시 표시합니다.
let settingsStatusTimer = null;
function showSettingsStatus(text) {
    settingsStatusEl.textContent = text;
    if (settingsStatusTimer) clearTimeout(settingsStatusTimer);
    settingsStatusTimer = setTimeout(() => {
        settingsStatusEl.textContent = "";
    }, 2000);
}

// 슬라이더 값이 바뀔 때 옆의 숫자 표시를 갱신합니다.
temperatureEl.addEventListener("input", () => {
    temperatureValueEl.textContent = Number(temperatureEl.value).toFixed(1);
});
topPEl.addEventListener("input", () => {
    topPValueEl.textContent = Number(topPEl.value).toFixed(2);
});

// 저장 / 기본값 버튼 이벤트를 연결합니다.
saveSettingsBtn.addEventListener("click", saveSettings);
resetSettingsBtn.addEventListener("click", resetSettings);

// ------------------------------------------------------------
// 메시지 표시
// ------------------------------------------------------------

// 화면에 메시지 말풍선을 추가합니다.
// role: "user" 또는 "assistant"
function appendMessage(role, content) {
    const bubble = document.createElement("div");
    bubble.className = `message ${role}`;
    bubble.textContent = content;
    chatMessages.appendChild(bubble);
    // 항상 최신 메시지가 보이도록 스크롤을 맨 아래로 내립니다.
    chatMessages.scrollTop = chatMessages.scrollHeight;
    return bubble;
}

// ------------------------------------------------------------
// 채팅 전송 처리
// ------------------------------------------------------------

chatForm.addEventListener("submit", async (event) => {
    // 폼 기본 동작(새로고침)을 막습니다.
    event.preventDefault();

    const message = chatInput.value.trim();
    if (!message) return;

    // 사용자 메시지를 화면과 기록에 추가합니다.
    appendMessage("user", message);
    history.push({ role: "user", content: message });

    // 입력창을 비우고 전송 버튼을 잠시 비활성화합니다.
    chatInput.value = "";
    sendButton.disabled = true;

    // "입력 중..." 임시 말풍선을 표시합니다.
    const pending = appendMessage("assistant", "입력 중...");

    try {
        // 서버로 보낼 요청 본문을 구성합니다. (질문 + 이전 기록 + 설정)
        const body = {
            message,
            history,
            settings: collectSettings(),
        };

        const response = await fetch("/api/chat", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(body),
        });

        if (!response.ok) {
            // 서버가 오류를 반환하면 상세 메시지를 표시합니다.
            const errText = await response.text();
            pending.textContent = `오류가 발생했습니다 (${response.status}).\n${errText}`;
            // 실패한 사용자 메시지는 기록에서 제거합니다.
            history.pop();
            return;
        }

        const data = await response.json();

        // 응답 내용을 임시 말풍선에 채우고 기록에 추가합니다.
        pending.textContent = data.reply;
        history.push({ role: "assistant", content: data.reply });

        // 데모 모드일 때는 안내를 덧붙입니다.
        if (data.used_demo_mode) {
            pending.textContent += "\n\n(데모 모드 응답입니다.)";
        }
    } catch (error) {
        pending.textContent = `요청 중 오류가 발생했습니다: ${error}`;
        history.pop();
    } finally {
        // 전송 버튼을 다시 활성화하고 입력창에 포커스를 줍니다.
        sendButton.disabled = false;
        chatInput.focus();
    }
});

// ------------------------------------------------------------
// 초기화: 서버 설정을 불러와 화면을 준비합니다.
// ------------------------------------------------------------

async function init() {
    try {
        const response = await fetch("/api/config");
        if (response.ok) {
            serverConfig = await response.json();
        }
    } catch (e) {
        // 설정 조회에 실패해도 기본값으로 계속 진행합니다.
    }

    // 모델 선택 목록을 채웁니다.
    modelSelectEl.innerHTML = "";
    (serverConfig.available_models || []).forEach((name) => {
        const option = document.createElement("option");
        option.value = name;
        option.textContent = name;
        modelSelectEl.appendChild(option);
    });

    // 기본 System Instruction과 기본 모델을 placeholder/기본값으로 반영합니다.
    if (serverConfig.default_system_instruction) {
        systemInstructionEl.placeholder = serverConfig.default_system_instruction;
    }
    if (serverConfig.default_model) {
        modelSelectEl.value = serverConfig.default_model;
    }

    // 저장된 설정이 있으면 화면에 반영합니다.
    const saved = loadSettings();
    if (saved) {
        applySettingsToForm(saved);
    }

    // 첫 인사 메시지를 표시합니다.
    const greeting = serverConfig.has_api_key
        ? "안녕하세요! 무엇을 도와드릴까요?"
        : "안녕하세요! 현재 데모 모드입니다. (.env에 OPENAI_API_KEY를 설정하면 실제 답변을 받을 수 있어요.)";
    appendMessage("assistant", greeting);
}

// 페이지 로드 시 초기화를 실행합니다.
init();
