// HTML 문서에서 실행 버튼 요소를 찾습니다.
const runButton = document.getElementById("runButton");

// HTML 문서에서 결과 출력 영역을 찾습니다.
const resultBox = document.getElementById("result");

// 실행 버튼을 클릭했을 때 LLM API를 호출합니다.
runButton.addEventListener("click", async () => {
    // 사용자가 선택한 API 공급자를 읽습니다.
    const provider = document.getElementById("provider").value;

    // 사용자가 선택한 기능 유형을 읽습니다.
    const taskType = document.getElementById("taskType").value;

    // 사용자가 직접 입력한 모델명을 읽습니다.
    const model = document.getElementById("model").value.trim();

    // 시스템 지시문을 읽습니다.
    const systemInstruction = document.getElementById("systemInstruction").value;

    // temperature 값을 숫자로 변환합니다.
    const temperature = Number(document.getElementById("temperature").value);

    // top_p 값을 숫자로 변환합니다.
    const topP = Number(document.getElementById("topP").value);

    // max_output_tokens 값을 숫자로 변환합니다.
    const maxOutputTokens = Number(document.getElementById("maxOutputTokens").value);

    // 사용자 프롬프트를 읽습니다.
    const prompt = document.getElementById("prompt").value;

    // API 호출 전 사용자에게 진행 상태를 표시합니다.
    resultBox.textContent = "LLM API 호출 중입니다...";

    // FastAPI 서버로 전달할 JSON 요청 본문을 만듭니다.
    const payload = {
        prompt: prompt,
        system_instruction: systemInstruction,
        task_type: taskType,
        model: model || null,
        temperature: temperature,
        top_p: topP,
        max_output_tokens: maxOutputTokens
    };

    try {
        // 공급자와 기능 유형에 맞는 FastAPI 엔드포인트를 호출합니다.
        const response = await fetch(`/api/llm/${provider}/${taskType}`, {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify(payload)
        });

        // HTTP 응답이 실패이면 오류 메시지를 생성합니다.
        if (!response.ok) {
            throw new Error(await response.text());
        }

        // JSON 응답을 JavaScript 객체로 변환합니다.
        const data = await response.json();

        // 결과를 화면에 보기 좋게 출력합니다.
        resultBox.textContent = `[Provider] ${data.provider}\n[Model] ${data.model}\n[Task] ${data.task_type}\n\n${data.result}`;
    } catch (error) {
        // 오류가 발생하면 결과 영역에 오류 내용을 출력합니다.
        resultBox.textContent = `오류 발생:\n${error.message}`;
    }
});
