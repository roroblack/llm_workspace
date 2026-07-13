// 브라우저가 HTML 문서를 모두 읽은 뒤 실행되도록 이벤트를 등록합니다.
document.addEventListener("DOMContentLoaded", () => {
    // 채팅 메시지가 출력될 영역을 가져옵니다.
    const chatWindow = document.getElementById("chatWindow");

    // 사용자가 메시지를 입력하는 폼을 가져옵니다.
    const chatForm = document.getElementById("chatForm");

    // 사용자 메시지 입력창을 가져옵니다.
    const messageInput = document.getElementById("messageInput");

    // 예측 의도를 표시할 요소를 가져옵니다.
    const intentText = document.getElementById("intentText");

    // 신뢰도를 텍스트로 표시할 요소를 가져옵니다.
    const confidenceText = document.getElementById("confidenceText");

    // 신뢰도 진행률 바를 가져옵니다.
    const confidenceBar = document.getElementById("confidenceBar");

    // 설문 진행 단계를 표시할 요소를 가져옵니다.
    const stepText = document.getElementById("stepText");

    // 브라우저 로컬 저장소에서 세션 ID를 가져오거나 새로 만듭니다.
    const sessionId = localStorage.getItem("survey_session_id") || crypto.randomUUID();

    // 새로 만든 세션 ID를 로컬 저장소에 저장합니다.
    localStorage.setItem("survey_session_id", sessionId);

    // 채팅창에 메시지를 추가하는 함수입니다.
    function addMessage(role, text) {
        // 메시지 전체를 감싸는 div를 생성합니다.
        const message = document.createElement("div");

        // 사용자 또는 봇 역할에 맞는 CSS 클래스를 지정합니다.
        message.className = `message ${role}`;

        // 사용자 메시지는 오른쪽 정렬이므로 아바타를 생략합니다.
        if (role === "user") {
            // 사용자 말풍선 HTML을 구성합니다.
            message.innerHTML = `<div class="bubble"></div>`;
        } else {
            // 봇 메시지는 아바타와 말풍선을 함께 구성합니다.
            message.innerHTML = `<div class="avatar">🤖</div><div class="bubble"></div>`;
        }

        // 말풍선 요소를 찾습니다.
        const bubble = message.querySelector(".bubble");

        // XSS를 막기 위해 textContent로 텍스트를 삽입합니다.
        bubble.textContent = text;

        // 채팅창에 메시지를 추가합니다.
        chatWindow.appendChild(message);

        // 최신 메시지가 보이도록 스크롤을 맨 아래로 이동합니다.
        chatWindow.scrollTop = chatWindow.scrollHeight;
    }

    // 오른쪽 분석 패널을 갱신하는 함수입니다.
    function updatePanel(data) {
        // 의도명을 화면에 표시합니다.
        intentText.textContent = data.intent;

        // 신뢰도를 퍼센트로 변환합니다.
        const percent = Math.round(data.confidence * 100);

        // 신뢰도 텍스트를 갱신합니다.
        confidenceText.textContent = `${percent}%`;

        // 진행률 바 너비를 갱신합니다.
        confidenceBar.style.width = `${percent}%`;

        // 설문 진행 단계를 갱신합니다.
        stepText.textContent = `${data.step} / ${data.total_steps}`;
    }

    // 서버 API로 메시지를 전송하는 비동기 함수입니다.
    async function sendMessage(message) {
        // 사용자 메시지를 채팅창에 먼저 표시합니다.
        addMessage("user", message);

        // 입력창을 비웁니다.
        messageInput.value = "";

        // 봇이 처리 중임을 표시합니다.
        addMessage("bot", "응답을 생성하는 중입니다...");

        // 마지막 봇 메시지 요소를 저장합니다.
        const loadingBubble = chatWindow.querySelector(".message:last-child .bubble");

        try {
            // FastAPI 채팅 API를 호출합니다.
            const response = await fetch("/api/chat", {
                // POST 방식으로 요청합니다.
                method: "POST",

                // JSON 요청임을 헤더에 표시합니다.
                headers: { "Content-Type": "application/json" },

                // 요청 본문에 사용자 메시지와 세션 ID를 담습니다.
                body: JSON.stringify({ message, session_id: sessionId }),
            });

            // 서버 응답이 실패 상태이면 예외를 발생시킵니다.
            if (!response.ok) {
                throw new Error("서버 응답 오류가 발생했습니다.");
            }

            // JSON 응답을 파싱합니다.
            const data = await response.json();

            // 로딩 말풍선을 실제 답변으로 교체합니다.
            loadingBubble.textContent = data.reply;

            // 분석 패널을 갱신합니다.
            updatePanel(data);
        } catch (error) {
            // 오류 발생 시 사용자에게 안내합니다.
            loadingBubble.textContent = "오류가 발생했습니다. 서버 실행 상태와 API 설정을 확인해 주세요.";

            // 개발자 콘솔에 상세 오류를 출력합니다.
            console.error(error);
        }
    }

    // 입력 폼 제출 이벤트를 처리합니다.
    chatForm.addEventListener("submit", (event) => {
        // 기본 새로고침 동작을 막습니다.
        event.preventDefault();

        // 입력값의 앞뒤 공백을 제거합니다.
        const message = messageInput.value.trim();

        // 빈 문자열이면 전송하지 않습니다.
        if (!message) return;

        // 메시지 전송 함수를 호출합니다.
        sendMessage(message);
    });

    // 빠른 입력 버튼 전체를 순회합니다.
    document.querySelectorAll(".chip").forEach((button) => {
        // 각 버튼에 클릭 이벤트를 등록합니다.
        button.addEventListener("click", () => {
            // 버튼의 data-text 값을 가져옵니다.
            const text = button.dataset.text;

            // 입력창에 빠른 입력 텍스트를 넣습니다.
            messageInput.value = text;

            // 입력창에 포커스를 줍니다.
            messageInput.focus();
        });
    });
});
