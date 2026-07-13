// 브라우저 화면에서 채팅창 요소를 가져옵니다.
const chatWindow = document.getElementById("chatWindow");

// 사용자 입력 폼 요소를 가져옵니다.
const chatForm = document.getElementById("chatForm");

// 사용자 메시지 입력창 요소를 가져옵니다.
const messageInput = document.getElementById("messageInput");

// 추천 개수 선택 요소를 가져옵니다.
const topKSelect = document.getElementById("topK");

// 이전 대화 기록을 저장하는 배열입니다.
const conversationHistory = [];

/**
 * 채팅창에 메시지를 추가하는 함수입니다.
 *
 * @param {string} role - "user" 또는 "bot" 값입니다.
 * @param {string} content - 화면에 표시할 메시지입니다.
 */
function addMessage(role, content) {
    // 메시지 전체를 감싸는 div를 생성합니다.
    const messageElement = document.createElement("div");

    // role에 따라 CSS 클래스를 다르게 지정합니다.
    messageElement.className = `message ${role}`;

    // 말풍선 div를 생성합니다.
    const bubbleElement = document.createElement("div");

    // 말풍선 CSS 클래스를 지정합니다.
    bubbleElement.className = "bubble";

    // XSS 방지를 위해 innerHTML 대신 textContent를 사용합니다.
    bubbleElement.textContent = content;

    // 메시지 div 안에 말풍선 div를 넣습니다.
    messageElement.appendChild(bubbleElement);

    // 채팅창에 메시지를 추가합니다.
    chatWindow.appendChild(messageElement);

    // 새 메시지가 보이도록 스크롤을 맨 아래로 이동합니다.
    chatWindow.scrollTop = chatWindow.scrollHeight;
}

/**
 * 음악 추천 API를 호출하는 비동기 함수입니다.
 *
 * @param {string} message - 사용자 입력 문장입니다.
 */
async function requestMusicRecommendation(message) {
    // 추천 중임을 사용자에게 보여주기 위해 임시 메시지를 출력합니다.
    addMessage("bot", "추천 음악을 찾고 있습니다...");

    // 서버에 보낼 요청 데이터를 구성합니다.
    const payload = {
        message: message,
        conversation_history: conversationHistory,
        top_k: Number(topKSelect.value)
    };

    try {
        // FastAPI 음악 추천 엔드포인트로 POST 요청을 보냅니다.
        const response = await fetch("/api/chat/music", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify(payload)
        });

        // HTTP 상태 코드가 200번대가 아니면 오류를 발생시킵니다.
        if (!response.ok) {
            throw new Error(`HTTP 오류: ${response.status}`);
        }

        // JSON 응답을 JavaScript 객체로 변환합니다.
        const data = await response.json();

        // 방금 표시한 "추천 음악을 찾고 있습니다..." 메시지를 제거합니다.
        chatWindow.lastChild.remove();

        // 봇 답변을 화면에 표시합니다.
        addMessage("bot", data.answer);

        // 사용자 입력과 봇 응답을 대화 기록에 저장합니다.
        conversationHistory.push({ role: "user", content: message });
        conversationHistory.push({ role: "assistant", content: data.answer });
    } catch (error) {
        // 임시 메시지를 제거합니다.
        chatWindow.lastChild.remove();

        // 오류 메시지를 화면에 표시합니다.
        addMessage("bot", `오류가 발생했습니다: ${error.message}`);
    }
}

// 입력 폼 제출 이벤트를 처리합니다.
chatForm.addEventListener("submit", async (event) => {
    // 브라우저의 기본 form 제출 동작을 막습니다.
    event.preventDefault();

    // 사용자가 입력한 메시지 앞뒤 공백을 제거합니다.
    const message = messageInput.value.trim();

    // 빈 문자열이면 처리하지 않습니다.
    if (!message) {
        return;
    }

    // 사용자 메시지를 화면에 표시합니다.
    addMessage("user", message);

    // 입력창을 비웁니다.
    messageInput.value = "";

    // 서버에 음악 추천을 요청합니다.
    await requestMusicRecommendation(message);
});

// 예시 버튼을 모두 찾아 클릭 이벤트를 연결합니다.
document.querySelectorAll(".chip").forEach((button) => {
    // 각 버튼을 클릭하면 data-example 값을 입력창에 넣습니다.
    button.addEventListener("click", () => {
        messageInput.value = button.dataset.example;
        messageInput.focus();
    });
});
