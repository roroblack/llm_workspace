// 얼굴인식 백엔드 성능 비교 페이지
// A(기준)·B(비교) 얼굴을 웹캠 촬영 또는 파일 업로드 → /api/face/benchmark → 3백엔드 실측 표.

const slots = { A: { blob: null, stream: null }, B: { blob: null, stream: null } };

function el(id) { return document.getElementById(id); }

function setSlot(which, blob, label) {
  slots[which].blob = blob;
  el("status" + which).textContent = label;
  const url = URL.createObjectURL(blob);
  const t = el("thumb" + which);
  t.src = url;
  t.hidden = false;
  updateRunEnabled();
}

function updateRunEnabled() {
  const ready = slots.A.blob && slots.B.blob;
  el("runBtn").disabled = !ready;
  el("runHint").textContent = ready ? "준비 완료 — 실행하세요." : "A·B 둘 다 준비되면 활성화됩니다.";
}

async function startCam(which) {
  const video = el("video" + which);
  try {
    const stream = await navigator.mediaDevices.getUserMedia({ video: true });
    slots[which].stream = stream;
    video.srcObject = stream;
    el("shot" + which).hidden = false;
    el("status" + which).textContent = "카메라 켜짐 — 촬영하세요.";
  } catch (err) {
    let msg = "카메라 오류: " + err.name;
    if (err.name === "NotAllowedError") msg = "카메라 권한 거부됨 — 파일 업로드를 쓰세요.";
    else if (err.name === "NotReadableError") msg = "카메라 사용 중 — 파일 업로드를 쓰세요.";
    el("status" + which).textContent = msg;
  }
}

async function shoot(which) {
  const blob = await captureFrameBlob(el("video" + which));
  if (!blob) { el("status" + which).textContent = "프레임 캡처 실패"; return; }
  setSlot(which, blob, "촬영됨(웹캠)");
}

["A", "B"].forEach((w) => {
  el("cam" + w).addEventListener("click", () => startCam(w));
  el("shot" + w).addEventListener("click", () => shoot(w));
  el("file" + w).addEventListener("change", (e) => {
    const f = e.target.files[0];
    if (f) setSlot(w, f, "업로드됨: " + f.name);
  });
});

el("runBtn").addEventListener("click", async () => {
  el("runBtn").disabled = true;
  el("runHint").textContent = "실측 중… (모델 최초 호출은 로딩 포함으로 느릴 수 있음)";
  try {
    const fd = new FormData();
    fd.append("image_a", slots.A.blob, "a.jpg");
    fd.append("image_b", slots.B.blob, "b.jpg");
    const resp = await fetch("/api/face/benchmark", { method: "POST", body: fd });
    const body = await resp.json().catch(() => null);
    if (!resp.ok) {
      el("runHint").textContent = (body && body.message) || `실패 (HTTP ${resp.status})`;
      return;
    }
    renderResults(body);
    el("runHint").textContent = "완료.";
  } catch (err) {
    el("runHint").textContent = "요청 실패: " + err.message;
  } finally {
    el("runBtn").disabled = false;
  }
});

function renderResults(body) {
  const tbody = el("resultBody");
  tbody.innerHTML = "";
  const labels = { insightface: "insightface (r50)", adaface: "AdaFace (IR-101)", lvface: "LVFace (ViT-S)" };
  // 코사인 최고 백엔드 강조
  const valid = body.results.filter((r) => r.cosine != null);
  const best = valid.length ? Math.max(...valid.map((r) => r.cosine)) : null;
  for (const r of body.results) {
    const tr = document.createElement("tr");
    if (r.error) {
      tr.innerHTML = `<td>${labels[r.backend] || r.backend}</td><td colspan="4" class="err-cell">모델 없음/오류: ${r.error}</td>`;
    } else {
      const isBest = r.cosine === best;
      const verdict = r.match ? '<span class="badge ok">동일인 판정</span>' : '<span class="badge warn">불일치</span>';
      tr.innerHTML =
        `<td>${labels[r.backend] || r.backend}${r.backend === body.active_backend ? " ⭐(현재 사용)" : ""}</td>` +
        `<td><strong>${r.cosine.toFixed(4)}</strong>${isBest ? " 🏆" : ""}</td>` +
        `<td>${verdict}</td>` +
        `<td>${r.ms_per_embed} ms</td>` +
        `<td>${r.backend === "adaface" ? "저품질 강함" : r.backend === "lvface" ? "고품질·빠름" : "기준선"}</td>`;
    }
    tbody.appendChild(tr);
  }
  el("resultTable").hidden = false;
  el("resultMeta").textContent =
    `현재 로그인 사용 백엔드: ${body.active_backend} · 매칭 임계값: ${body.match_threshold} ` +
    `(코사인이 임계값 이상이면 동일인 판정). 지연은 최초 호출 시 모델 로딩 포함.`;
}

window.addEventListener("pagehide", () => {
  ["A", "B"].forEach((w) => { if (slots[w].stream) slots[w].stream.getTracks().forEach((t) => t.stop()); });
});
