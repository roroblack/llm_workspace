const tabs = document.querySelectorAll(".tab");
const panels = document.querySelectorAll(".tab-panel");

tabs.forEach((tab) => {
    tab.addEventListener("click", () => {
        tabs.forEach((item) => {
            const active = item === tab;
            item.classList.toggle("active", active);
            item.setAttribute("aria-selected", String(active));
        });
        panels.forEach((panel) => {
            const active = panel.id === `tab-${tab.dataset.tab}`;
            panel.classList.toggle("active", active);
            panel.hidden = !active;
        });
    });
});

async function postJson(url, body) {
    const response = await fetch(url, {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify(body),
    });
    const payload = await response.json();
    if (!response.ok) throw new Error(payload.detail || "요청 처리에 실패했습니다.");
    return payload;
}

function setBusy(button, busy, runningText, idleText) {
    button.disabled = busy;
    button.textContent = busy ? runningText : idleText;
}

const chatForm = document.querySelector("#chatForm");
const messageInput = document.querySelector("#message");
const messagesBox = document.querySelector("#messages");
const traceBox = document.querySelector("#trace");

function appendMessage(role, text) {
    const article = document.createElement("article");
    article.className = `message ${role}`;
    const title = document.createElement("b");
    title.textContent = role === "user" ? "고객" : "상담원";
    const body = document.createElement("p");
    body.textContent = text;
    article.append(title, body);
    messagesBox.appendChild(article);
    messagesBox.scrollTop = messagesBox.scrollHeight;
}

function renderTrace(items) {
    traceBox.innerHTML = "";
    items.forEach((item) => {
        const row = document.createElement("div");
        row.className = "trace-item";
        const stage = document.createElement("b");
        stage.textContent = item.stage;
        const detail = document.createElement("span");
        detail.textContent = item.detail;
        row.append(stage, detail);
        traceBox.appendChild(row);
    });
}

chatForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    const message = messageInput.value.trim();
    if (!message) return;
    const button = chatForm.querySelector("button");
    appendMessage("user", message);
    messageInput.value = "";
    setBusy(button, true, "처리 중...", "통합 워크플로우 실행");
    try {
        const data = await postJson("/api/v1/chat", {
            message,
            thread_id: document.querySelector("#threadId").value.trim() || "web-user",
            provider: document.querySelector("#provider").value,
        });
        appendMessage("assistant", data.answer);
        renderTrace(data.trace || []);
    } catch (error) {
        appendMessage("assistant", `오류: ${error.message}`);
    } finally {
        setBusy(button, false, "처리 중...", "통합 워크플로우 실행");
        messageInput.focus();
    }
});

document.querySelector("#complaintForm").addEventListener("submit", async (event) => {
    event.preventDefault();
    const form = event.currentTarget;
    const button = form.querySelector("button");
    const result = document.querySelector("#complaintResult");
    setBusy(button, true, "MySQL 저장 중...", "담당 부서로 전달");
    result.textContent = "담당 부서 큐에 등록하고 있습니다...";
    try {
        const dept = document.querySelector("#complaintDepartment").value;
        const data = await postJson("/api/v1/complaints/connect", {
            custum_id: document.querySelector("#complaintCustomer").value.trim(),
            dept_id: dept || null,
            message: document.querySelector("#complaintMessage").value.trim(),
        });
        result.textContent = `${data.answer}\n\n접수 대기 번호: ${data.cc_id}\n담당 부서: ${data.dept_id}\n문의 시각: ${data.inquiry_date}\n접수 여부: ${data.receipt_status ? "접수" : "미접수"}\n처리 여부: ${data.resolution_status ? "완료" : "미완료"}`;
    } catch (error) {
        result.textContent = `오류: ${error.message}`;
    } finally {
        setBusy(button, false, "MySQL 저장 중...", "담당 부서로 전달");
    }
});

document.querySelector("#summaryForm").addEventListener("submit", async (event) => {
    event.preventDefault();
    const form = event.currentTarget;
    const button = form.querySelector("button");
    const result = document.querySelector("#summaryResult");
    const download = document.querySelector("#summaryDownload");
    setBusy(button, true, "요약 중...", "요약 보고서 생성");
    result.textContent = "map-reduce 요약을 실행하고 있습니다...";
    download.hidden = true;
    try {
        const data = await postJson("/api/v1/reports/summary", {
            title: document.querySelector("#summaryTitle").value.trim(),
            text: document.querySelector("#summaryText").value.trim(),
            provider: document.querySelector("#summaryProvider").value,
        });
        result.textContent = data.content + (data.used_fallback ? "\n\n[기본 요약 템플릿 사용]" : "");
        download.href = data.download_url;
        download.download = data.report_path;
        download.hidden = false;
    } catch (error) {
        result.textContent = `오류: ${error.message}`;
    } finally {
        setBusy(button, false, "요약 중...", "요약 보고서 생성");
    }
});

document.querySelector("#salesForm").addEventListener("submit", async (event) => {
    event.preventDefault();
    const form = event.currentTarget;
    const button = form.querySelector("button");
    const result = document.querySelector("#salesResult");
    const facts = document.querySelector("#salesFacts");
    const download = document.querySelector("#salesDownload");
    setBusy(button, true, "집계·작성 중...", "임원용 매출 보고서 생성");
    result.textContent = "확정 수치를 집계하고 있습니다...";
    facts.textContent = "집계 중...";
    download.hidden = true;
    try {
        const month = document.querySelector("#salesMonth").value;
        const data = await postJson("/api/v1/reports/sales", {
            month: month || null,
            provider: document.querySelector("#salesProvider").value,
        });
        facts.textContent = JSON.stringify(data.facts, null, 2);
        result.textContent = data.content + (data.used_fallback ? "\n\n[확정 수치 기본 템플릿 사용]" : "");
        download.href = data.download_url;
        download.download = data.report_path;
        download.hidden = false;
    } catch (error) {
        facts.textContent = "-";
        result.textContent = `오류: ${error.message}`;
    } finally {
        setBusy(button, false, "집계·작성 중...", "임원용 매출 보고서 생성");
    }
});
