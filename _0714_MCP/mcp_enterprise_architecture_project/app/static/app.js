// JSON API 호출을 공통으로 처리하는 비동기 함수를 정의합니다.
async function requestJson(url, options = {}) {
    // fetch로 지정한 URL을 호출합니다.
    const response = await fetch(url, options);

    // JSON 응답을 읽습니다.
    const data = await response.json();

    // HTTP 성공 상태가 아니면 상세 오류를 발생시킵니다.
    if (!response.ok) {
        throw new Error(data.detail || JSON.stringify(data));
    }

    // 정상 JSON 데이터를 반환합니다.
    return data;
}

// 값을 보기 좋은 JSON 문자열로 출력합니다.
function show(elementId, value) {
    // 지정한 출력 요소의 텍스트를 갱신합니다.
    document.getElementById(elementId).textContent = JSON.stringify(value, null, 2);
}

// 상태 확인 버튼 이벤트를 등록합니다.
document.getElementById("healthButton").addEventListener("click", async () => {
    try {
        show("healthOutput", await requestJson("/api/health"));
    } catch (error) {
        show("healthOutput", {error: error.message});
    }
});

// Tool 목록 버튼 이벤트를 등록합니다.
document.getElementById("toolsButton").addEventListener("click", async () => {
    try {
        show("toolsOutput", await requestJson("/api/mcp/tools"));
    } catch (error) {
        show("toolsOutput", {error: error.message});
    }
});

// Tool 직접 호출 버튼 이벤트를 등록합니다.
document.getElementById("callButton").addEventListener("click", async () => {
    try {
        // 입력된 JSON 인수를 객체로 변환합니다.
        const argumentsObject = JSON.parse(document.getElementById("toolArguments").value);

        // MCP Tool 호출 API를 실행합니다.
        const result = await requestJson("/api/mcp/call", {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({
                name: document.getElementById("toolName").value,
                arguments: argumentsObject
            })
        });

        // 호출 결과를 화면에 표시합니다.
        show("callOutput", result);
    } catch (error) {
        show("callOutput", {error: error.message});
    }
});

// Assistant 실행 버튼 이벤트를 등록합니다.
document.getElementById("assistantButton").addEventListener("click", async () => {
    try {
        // 자연어 요청을 Assistant API로 전송합니다.
        const result = await requestJson("/api/assistant", {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({
                message: document.getElementById("assistantMessage").value
            })
        });

        // Assistant 응답을 화면에 표시합니다.
        show("assistantOutput", result);
    } catch (error) {
        show("assistantOutput", {error: error.message});
    }
});
