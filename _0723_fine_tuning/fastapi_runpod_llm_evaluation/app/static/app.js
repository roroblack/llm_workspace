/*
 * FastAPI 평가 API를 브라우저에서 호출하는 프론트엔드 코드입니다.
 */

/**
 * JSON API를 호출하고 성공 또는 오류 결과를 반환합니다.
 */
async function requestJson(url, options = {}) {
    // fetch 함수를 사용하여 지정한 API로 HTTP 요청을 전송합니다.
    const response = await fetch(url, options);

    // 서버 응답 본문을 JSON으로 변환합니다.
    const data = await response.json();

    // HTTP 상태 코드가 성공 범위가 아니면 서버의 detail 메시지로 오류를 발생시킵니다.
    if (!response.ok) {
        throw new Error(data.detail || "API 요청 중 오류가 발생했습니다.");
    }

    // 정상 응답 데이터를 반환합니다.
    return data;
}

/**
 * 결과 객체를 읽기 쉬운 JSON 문자열로 화면에 표시합니다.
 */
function showResult(elementId, data) {
    // 대상 pre 요소를 ID로 찾습니다.
    const element = document.getElementById(elementId);

    // JSON 데이터를 두 칸 들여쓰기 문자열로 변환하여 표시합니다.
    element.textContent = JSON.stringify(data, null, 2);
}

/**
 * 실행 중 상태 메시지를 표시합니다.
 */
function showLoading(elementId, message) {
    // 결과를 표시할 요소를 찾습니다.
    const element = document.getElementById(elementId);

    // 현재 수행 중인 작업을 사용자에게 표시합니다.
    element.textContent = message;
}

// 상태 확인 버튼 클릭 이벤트를 등록합니다.
document.getElementById("healthButton").addEventListener("click", async () => {
    try {
        // 상태 확인 중 메시지를 표시합니다.
        showLoading("healthResult", "서버와 GPU 상태를 확인하고 있습니다.");

        // 시스템 상태 API를 호출합니다.
        const data = await requestJson("/api/system/health");

        // 결과를 화면에 표시합니다.
        showResult("healthResult", data);
    } catch (error) {
        // 오류 메시지를 화면에 표시합니다.
        showResult("healthResult", { error: error.message });
    }
});

// 답변 생성 버튼 클릭 이벤트를 등록합니다.
document.getElementById("generateButton").addEventListener("click", async () => {
    try {
        // 선택한 모델 종류를 읽습니다.
        const modelKind = document.getElementById("modelKind").value;

        // 입력한 질문 문자열을 읽습니다.
        const prompt = document.getElementById("prompt").value.trim();

        // 최대 생성 토큰 값을 숫자로 변환합니다.
        const maxNewTokens = Number(
            document.getElementById("maxNewTokens").value
        );

        // 빈 질문은 서버에 보내지 않고 즉시 오류를 발생시킵니다.
        if (!prompt) {
            throw new Error("질문을 입력하세요.");
        }

        // 실제 모델에서는 시간이 걸릴 수 있음을 표시합니다.
        showLoading(
            "generateResult",
            "모델 답변을 생성하고 있습니다."
        );

        // 단일 추론 API를 JSON 방식으로 호출합니다.
        const data = await requestJson("/api/inference/generate", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                model_kind: modelKind,
                prompt: prompt,
                max_new_tokens: maxNewTokens,
                do_sample: false,
                temperature: 0.7,
                top_p: 0.9
            })
        });

        // 생성 결과를 화면에 표시합니다.
        showResult("generateResult", data);
    } catch (error) {
        // 오류 메시지를 표시합니다.
        showResult("generateResult", { error: error.message });
    }
});

// 한 모델 평가 버튼 클릭 이벤트를 등록합니다.
document.getElementById("runEvaluationButton").addEventListener("click", async () => {
    try {
        // 평가할 모델 종류를 읽습니다.
        const modelKind = document.getElementById(
            "evaluationModelKind"
        ).value;

        // BERTScore 체크 여부를 읽습니다.
        const useBertScore = document.getElementById(
            "useBertScore"
        ).checked;

        // 평가 개수 입력값을 읽습니다.
        const limitText = document.getElementById(
            "evaluationLimit"
        ).value;

        // 빈 값은 null, 값이 있으면 숫자로 변환합니다.
        const limit = limitText ? Number(limitText) : null;

        // 평가 수행 중 메시지를 표시합니다.
        showLoading(
            "evaluationResult",
            "평가 데이터를 순서대로 실행하고 있습니다."
        );

        // 평가 실행 API를 호출합니다.
        const data = await requestJson("/api/evaluation/run", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                model_kind: modelKind,
                use_bertscore: useBertScore,
                limit: limit
            })
        });

        // 평가 결과를 화면에 표시합니다.
        showResult("evaluationResult", data);
    } catch (error) {
        // 오류 메시지를 표시합니다.
        showResult("evaluationResult", { error: error.message });
    }
});

// 두 모델 비교 버튼 클릭 이벤트를 등록합니다.
document.getElementById("compareButton").addEventListener("click", async () => {
    try {
        // BERTScore 체크 여부를 읽습니다.
        const useBertScore = document.getElementById(
            "useBertScore"
        ).checked;

        // 평가 개수 입력값을 읽습니다.
        const limitText = document.getElementById(
            "evaluationLimit"
        ).value;

        // 값이 없으면 null, 있으면 숫자로 변환합니다.
        const limit = limitText ? Number(limitText) : null;

        // 두 모델을 순차 실행한다는 상태를 표시합니다.
        showLoading(
            "evaluationResult",
            "Base 모델과 Fine-tuned 모델을 순차 평가하고 있습니다."
        );

        // 모델 비교 API를 호출합니다.
        const data = await requestJson("/api/evaluation/compare", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                use_bertscore: useBertScore,
                limit: limit
            })
        });

        // 비교 결과를 화면에 표시합니다.
        showResult("evaluationResult", data);
    } catch (error) {
        // 오류 결과를 화면에 표시합니다.
        showResult("evaluationResult", { error: error.message });
    }
});
