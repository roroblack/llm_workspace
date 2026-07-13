// JSON 응답을 보기 좋게 출력하는 공통 함수입니다.
function pretty(data) {
    return JSON.stringify(data, null, 2);
}

// GET 요청을 보내는 공통 함수입니다.
async function getJson(url) {
    const response = await fetch(url);
    return await response.json();
}

// POST JSON 요청을 보내는 공통 함수입니다.
async function postJson(url, body) {
    const response = await fetch(url, {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify(body)
    });
    return await response.json();
}

// 서버 상태를 확인합니다.
async function callHealth() {
    const data = await getJson("/api/health");
    document.getElementById("healthResult").textContent = pretty(data);
}

// Vector DB를 재생성합니다.
async function rebuildVector() {
    const data = await postJson("/api/vector/rebuild", {});
    document.getElementById("vectorResult").textContent = pretty(data);
}

// Vector DB를 검색합니다.
async function searchVector() {
    const query = document.getElementById("vectorQuery").value;
    const data = await postJson("/api/vector/search", {query: query, top_k: 3});
    document.getElementById("vectorResult").textContent = pretty(data);
}

// Torch 분석 API를 호출합니다.
async function callTorch() {
    const data = await getJson("/api/torch/stock-summary");
    document.getElementById("torchResult").textContent = pretty(data);
}

// 로컬 도구 데모 API를 호출합니다.
async function callLocalTools() {
    const data = await getJson("/api/tools/local-demo");
    document.getElementById("toolsResult").textContent = pretty(data);
}

// OpenAI ReAct 에이전트를 실행합니다.
async function callReact() {
    const question = document.getElementById("question").value;
    const data = await postJson("/api/react/openai", {question: question, max_steps: 6});
    document.getElementById("reactResult").textContent = pretty(data);
}

// Gemini 보조 답변 API를 호출합니다.
async function callGemini() {
    const question = document.getElementById("question").value;
    const data = await postJson("/api/gemini/ask", {question: question, max_steps: 3});
    document.getElementById("geminiResult").textContent = pretty(data);
}
