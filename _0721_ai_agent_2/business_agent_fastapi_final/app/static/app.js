// 통합 에이전트 실행 버튼 요소를 가져옵니다.
const button = document.getElementById("sendButton");
// 사용자 질문 입력 요소를 가져옵니다.
const message = document.getElementById("message");
// 최종 답변을 표시할 요소를 가져옵니다.
const answer = document.getElementById("answer");
// 선택된 실행 경로를 표시할 요소를 가져옵니다.
const route = document.getElementById("route");
// LangGraph 실행 추적을 표시할 요소를 가져옵니다.
const trace = document.getElementById("trace");

// 사용자가 실행 버튼을 눌렀을 때 비동기 요청을 수행합니다.
button.addEventListener("click", async () => {
    // 입력 질문의 앞뒤 공백을 제거합니다.
    const text = message.value.trim();
    // 질문이 비어 있으면 API를 호출하지 않고 안내합니다.
    if (!text) {
        answer.textContent = "질문을 입력하세요.";
        return;
    }
    // 중복 요청을 막기 위해 버튼을 비활성화합니다.
    button.disabled = true;
    // 실행 상태를 답변 영역에 표시합니다.
    answer.textContent = "실행 중...";
    // 이전 실행 경로를 초기화합니다.
    route.textContent = "-";
    // 이전 실행 추적을 초기화합니다.
    trace.textContent = "-";
    try {
        // FastAPI 통합 채팅 엔드포인트에 JSON POST 요청을 전송합니다.
        const response = await fetch("/api/v1/chat", {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({
                message: text,
                provider: document.getElementById("provider").value,
                thread_id: document.getElementById("threadId").value.trim() || "business-session"
            })
        });
        // 응답 본문을 JSON 객체로 변환합니다.
        const data = await response.json();
        // HTTP 오류이면 FastAPI의 detail 메시지를 예외로 변환합니다.
        if (!response.ok) {
            throw new Error(data.detail || "요청 실패");
        }
        // 최종 답변을 화면에 표시합니다.
        answer.textContent = data.answer || "답변 없음";
        // LangGraph 분류 경로와 A2A 대상을 표시합니다.
        route.textContent = `${data.route || "-"} → ${data.target_agent || "-"}`;
        // 단계별 실행 추적을 줄바꿈 문자열로 변환해 표시합니다.
        trace.textContent = (data.trace || []).map((item) => `[${item.stage}] ${item.detail}`).join("\n") || "-";
    } catch (error) {
        // 네트워크 또는 서버 오류 메시지를 답변 영역에 표시합니다.
        answer.textContent = `오류: ${error.message}`;
    } finally {
        // 성공 또는 실패와 관계없이 다시 요청할 수 있도록 버튼을 활성화합니다.
        button.disabled = false;
    }
});

// ---------------------------------------------------------------------------
// Prompt Engineering 실습
// ---------------------------------------------------------------------------

// 프롬프트 유형 선택 요소를 가져옵니다.
const promptType = document.getElementById("promptType");
// System Prompt 입력 요소를 가져옵니다.
const systemPrompt = document.getElementById("systemPrompt");
// 수행 지시문 입력 요소를 가져옵니다.
const customInstruction = document.getElementById("customInstruction");
// 실습 실행 버튼을 가져옵니다.
const labButton = document.getElementById("labSendButton");
// 실습 질문 입력 요소를 가져옵니다.
const labMessage = document.getElementById("labMessage");
// 실습 답변 표시 요소를 가져옵니다.
const labAnswer = document.getElementById("labAnswer");
// 적용된 설정 표시 요소를 가져옵니다.
const labSettings = document.getElementById("labSettings");

// 5종 프롬프트 유형별 System Prompt 와 수행 지시문 프리셋입니다.
const promptPresets = [
    {
        value: "basic",
        system_prompt: "너는 비즈니스 데이터를 다루는 도우미다. 질문에 사실 위주로 간단히 답하라.",
        instruction: "질문에 대해 핵심만 간단히 답해줘."
    },
    {
        value: "expert",
        system_prompt: "너는 10년 경력의 데이터 분석 전문가다. 근거와 지표를 들어 정확하고 전문적으로 설명하되 추측을 사실처럼 말하지 마라.",
        instruction: "전문가 관점에서 원인과 시사점을 함께 분석해줘."
    },
    {
        value: "friendly",
        system_prompt: "너는 친절한 설명가다. 비전문가도 이해할 수 있도록 쉬운 말과 비유로 따뜻하게 설명하라.",
        instruction: "처음 접하는 사람도 이해할 수 있게 쉽게 풀어서 설명해줘."
    },
    {
        value: "step_by_step",
        system_prompt: "너는 단계별로 사고하는 분석가다. 결론을 내기 전에 생각의 흐름을 순서대로 나눠 정리하라.",
        instruction: "1단계, 2단계, 3단계처럼 사고 과정을 단계별로 나눠서 설명하고 마지막에 결론을 제시해줘."
    },
    {
        value: "json",
        system_prompt: "너는 항상 유효한 JSON만 출력하는 API다. 설명 문장이나 코드블록 표시 없이 JSON 객체만 반환하라.",
        instruction: "결과를 {\"summary\": \"...\", \"key_points\": [\"...\"], \"recommendation\": \"...\"} 형식의 JSON으로만 답해줘."
    }
];

// 선택된 유형에 맞춰 System Prompt 와 지시문을 자동 입력합니다.
function applySelectedPreset() {
    // 현재 선택값과 일치하는 프리셋을 찾습니다.
    const preset = promptPresets.find((item) => item.value === promptType.value);
    // 일치하는 프리셋이 없으면 아무것도 하지 않습니다.
    if (!preset) {
        return;
    }
    // 두 텍스트영역에 프리셋 내용을 채웁니다.
    systemPrompt.value = preset.system_prompt;
    customInstruction.value = preset.instruction;
}

// 유형이 바뀌면 자동으로 프리셋을 적용합니다.
promptType.addEventListener("change", applySelectedPreset);
// 페이지 로드 시 기본 유형(basic) 프리셋을 미리 채워둡니다.
applySelectedPreset();

// 실습 실행 버튼 클릭 시 지정한 프롬프트 설정으로 LLM 을 직접 호출합니다.
labButton.addEventListener("click", async () => {
    // 질문의 앞뒤 공백을 제거합니다.
    const text = labMessage.value.trim();
    // 질문이 비어 있으면 안내 후 종료합니다.
    if (!text) {
        labAnswer.textContent = "질문을 입력하세요.";
        return;
    }
    // 중복 요청 방지를 위해 버튼을 비활성화합니다.
    labButton.disabled = true;
    // 실행 상태를 표시합니다.
    labAnswer.textContent = "실행 중...";
    labSettings.textContent = "-";
    try {
        // Prompt 실습 전용 엔드포인트에 현재 설정을 전송합니다.
        const response = await fetch("/api/v1/prompt-lab", {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({
                message: text,
                provider: document.getElementById("labProvider").value,
                prompt_type: promptType.value,
                system_prompt: systemPrompt.value,
                instruction: customInstruction.value,
                temperature: parseFloat(document.getElementById("temperature").value) || 0,
                top_p: parseFloat(document.getElementById("topP").value) || 1,
                few_shot: document.getElementById("fewShot").value === "on"
            })
        });
        // 응답 본문을 JSON 으로 변환합니다.
        const data = await response.json();
        // HTTP 오류이면 detail 메시지를 예외로 변환합니다.
        if (!response.ok) {
            throw new Error(data.detail || "요청 실패");
        }
        // 최종 답변을 표시합니다.
        labAnswer.textContent = data.answer || "답변 없음";
        // 실제 적용된 설정을 보기 좋게 표시해 비교를 돕습니다.
        labSettings.textContent = JSON.stringify(data.settings || {}, null, 2);
    } catch (error) {
        // 네트워크 또는 서버 오류 메시지를 표시합니다.
        labAnswer.textContent = `오류: ${error.message}`;
    } finally {
        // 다시 실행할 수 있도록 버튼을 활성화합니다.
        labButton.disabled = false;
    }
});
