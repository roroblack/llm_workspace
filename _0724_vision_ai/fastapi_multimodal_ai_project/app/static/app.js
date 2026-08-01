// HTML 요소를 ID로 간편하게 찾는 보조 함수를 정의합니다.
const byId = (id) => document.getElementById(id);

// 각 탭 버튼과 서비스 패널을 가져옵니다.
const captionTabButton = byId("captionTabButton");
const diffusionTabButton = byId("diffusionTabButton");
const captionPanel = byId("captionPanel");
const diffusionPanel = byId("diffusionPanel");

// 공통 상태 메시지 박스를 가져옵니다.
const messageBox = byId("messageBox");

// 사용자에게 진행 상황 또는 오류를 표시하는 함수를 정의합니다.
function showMessage(message, isError = false) {
    // 전달받은 문장을 메시지 박스에 넣습니다.
    messageBox.textContent = message;
    // 오류 여부에 따라 error 클래스를 추가하거나 제거합니다.
    messageBox.classList.toggle("error", isError);
    // 메시지 박스를 화면에 표시합니다.
    messageBox.classList.remove("hidden");
}

// 이전 메시지를 화면에서 숨기는 함수를 정의합니다.
function hideMessage() {
    // hidden 클래스를 추가하여 메시지 박스를 감춥니다.
    messageBox.classList.add("hidden");
}

// 서버 오류 응답에서 사람이 읽을 수 있는 detail을 추출합니다.
async function parseError(response) {
    // JSON 응답 파싱 실패까지 대비하여 try 블록을 사용합니다.
    try {
        // 서버 응답 본문을 JSON으로 변환합니다.
        const data = await response.json();
        // FastAPI의 detail 값이 있으면 우선 반환합니다.
        return data.detail || "요청 처리 중 오류가 발생했습니다.";
    } catch (error) {
        // JSON이 아닌 경우 HTTP 상태 텍스트를 반환합니다.
        return response.statusText || "요청 처리 중 오류가 발생했습니다.";
    }
}

// 탭 이름에 따라 현재 서비스 화면을 전환합니다.
function activateTab(tabName) {
    // 캡셔닝 탭 선택 여부를 계산합니다.
    const captionActive = tabName === "caption";
    // 각 버튼의 활성화 클래스를 갱신합니다.
    captionTabButton.classList.toggle("active", captionActive);
    diffusionTabButton.classList.toggle("active", !captionActive);
    // 각 패널의 표시 상태를 갱신합니다.
    captionPanel.classList.toggle("active", captionActive);
    diffusionPanel.classList.toggle("active", !captionActive);
    // 화면 전환 시 이전 상태 메시지를 숨깁니다.
    hideMessage();
}

// 캡셔닝 탭 버튼 클릭 이벤트를 등록합니다.
captionTabButton.addEventListener("click", () => activateTab("caption"));

// Stable Diffusion 탭 버튼 클릭 이벤트를 등록합니다.
diffusionTabButton.addEventListener("click", () => activateTab("diffusion"));

// 업로드 이미지가 바뀌면 브라우저에서 즉시 미리보기를 표시합니다.
byId("captionFile").addEventListener("change", (event) => {
    // 사용자가 선택한 첫 번째 파일을 가져옵니다.
    const file = event.target.files[0];
    // 파일을 선택하지 않았다면 미리보기를 숨깁니다.
    if (!file) {
        byId("captionPreview").classList.add("hidden");
        return;
    }
    // 로컬 파일의 임시 URL을 생성합니다.
    const previewUrl = URL.createObjectURL(file);
    // 이미지 요소에 임시 URL을 지정합니다.
    byId("captionPreview").src = previewUrl;
    // 미리보기 이미지를 표시합니다.
    byId("captionPreview").classList.remove("hidden");
});

// 이미지 캡셔닝 폼 제출 이벤트를 처리합니다.
byId("captionForm").addEventListener("submit", async (event) => {
    // HTML 폼의 기본 페이지 이동을 막습니다.
    event.preventDefault();
    // 폼 제출 버튼을 가져옵니다.
    const submitButton = event.submitter;
    // 선택된 파일을 가져옵니다.
    const file = byId("captionFile").files[0];
    // 파일이 없으면 서버 요청을 보내지 않습니다.
    if (!file) {
        showMessage("먼저 사진 파일을 선택하세요.", true);
        return;
    }
    // multipart/form-data 전송을 위한 FormData를 생성합니다.
    const formData = new FormData();
    // FastAPI의 file 매개변수 이름과 동일하게 파일을 추가합니다.
    formData.append("file", file);
    // 중복 요청을 막기 위해 버튼을 비활성화합니다.
    submitButton.disabled = true;
    // 모델 최초 다운로드가 오래 걸릴 수 있음을 안내합니다.
    showMessage("사진을 분석하고 있습니다. 최초 실행은 모델 다운로드 때문에 오래 걸릴 수 있습니다.");
    try {
        // 이미지 캡셔닝 API에 POST 요청을 보냅니다.
        const response = await fetch("/api/caption", { method: "POST", body: formData });
        // HTTP 오류이면 상세 오류를 읽어 예외로 전환합니다.
        if (!response.ok) throw new Error(await parseError(response));
        // 성공 JSON을 읽습니다.
        const data = await response.json();
        // 영어 캡션을 화면에 표시합니다.
        byId("captionEnglish").textContent = data.caption_en;
        // 한국어 보조 설명을 화면에 표시합니다.
        byId("captionKorean").textContent = data.caption_ko;
        // 결과 카드를 화면에 표시합니다.
        byId("captionResult").classList.remove("hidden");
        // 완료 메시지를 표시합니다.
        showMessage("이미지 캡셔닝이 완료되었습니다.");
    } catch (error) {
        // 네트워크 또는 서버 오류를 표시합니다.
        showMessage(error.message, true);
    } finally {
        // 성공 여부와 관계없이 제출 버튼을 다시 활성화합니다.
        submitButton.disabled = false;
    }
});

// 서버 측 TTS API를 호출하고 생성된 음성을 재생하는 공통 함수입니다.
async function playServerTts(text, audioElement) {
    // 비어 있는 문장은 서버로 보내지 않습니다.
    if (!text.trim()) {
        showMessage("음성으로 읽을 문장이 없습니다.", true);
        return;
    }
    // 폼 형식의 TTS 요청 데이터를 만듭니다.
    const formData = new FormData();
    // FastAPI의 text 매개변수와 동일한 이름으로 문장을 추가합니다.
    formData.append("text", text);
    // 현재 처리 상태를 표시합니다.
    showMessage("TTS 음성을 생성하고 있습니다.");
    try {
        // 서버 측 TTS API를 호출합니다.
        const response = await fetch("/api/tts", { method: "POST", body: formData });
        // 오류 상태이면 상세 메시지를 예외로 변환합니다.
        if (!response.ok) throw new Error(await parseError(response));
        // 생성된 WAV URL을 읽습니다.
        const data = await response.json();
        // 브라우저 캐시를 피하기 위해 현재 시간을 쿼리에 추가합니다.
        audioElement.src = `${data.audio_url}?t=${Date.now()}`;
        // 오디오 재생 컨트롤을 표시합니다.
        audioElement.classList.remove("hidden");
        // 사용자 클릭 이벤트 안에서 음성 재생을 시작합니다.
        await audioElement.play();
        // 성공 상태를 표시합니다.
        showMessage("TTS 음성을 재생합니다.");
    } catch (error) {
        // 서버 음성 엔진이 없는 경우에도 브라우저 TTS 사용 가능함을 안내합니다.
        showMessage(`${error.message} 브라우저 음성 재생 버튼을 사용할 수 있습니다.`, true);
    }
}

// 캡션 서버 TTS 버튼 클릭 이벤트를 등록합니다.
byId("captionTtsButton").addEventListener("click", () => {
    // 화면에 표시된 한국어 설명을 서버 TTS로 읽습니다.
    playServerTts(byId("captionKorean").textContent, byId("captionAudio"));
});

// 브라우저 내장 SpeechSynthesis로 캡션을 읽는 대체 기능입니다.
byId("captionBrowserTtsButton").addEventListener("click", () => {
    // 현재 합성 중인 음성이 있다면 먼저 중지합니다.
    window.speechSynthesis.cancel();
    // 화면의 한국어 캡션으로 발화 객체를 생성합니다.
    const utterance = new SpeechSynthesisUtterance(byId("captionKorean").textContent);
    // 한국어 음성을 우선 사용하도록 언어를 지정합니다.
    utterance.lang = "ko-KR";
    // 정상적인 속도로 발화합니다.
    utterance.rate = 1.0;
    // 브라우저 음성 엔진을 실행합니다.
    window.speechSynthesis.speak(utterance);
});

// 마이크 PCM 녹음에 필요한 Web Audio 객체와 상태 변수를 선언합니다.
let microphoneStream = null;
let recordingAudioContext = null;
let recordingSourceNode = null;
let recordingProcessorNode = null;
let recordingSilenceNode = null;
let recordedPcmChunks = [];
let isRecording = false;
let recordingStartedAt = 0;

// DataView에 ASCII 문자열을 한 글자씩 기록하는 WAV 헤더 보조 함수입니다.
function writeAscii(view, offset, text) {
    // 문자열의 각 문자를 1바이트 문자 코드로 변환해 지정 위치에 기록합니다.
    for (let index = 0; index < text.length; index += 1) {
        view.setUint8(offset + index, text.charCodeAt(index));
    }
}

// 여러 Float32Array 조각을 하나의 연속된 Float32Array로 합칩니다.
function mergeFloat32Chunks(chunks) {
    // 모든 조각의 전체 샘플 수를 계산합니다.
    const totalLength = chunks.reduce((sum, chunk) => sum + chunk.length, 0);

    // 전체 길이의 결과 배열을 생성합니다.
    const merged = new Float32Array(totalLength);

    // 각 조각을 앞에서부터 순서대로 복사합니다.
    let offset = 0;
    for (const chunk of chunks) {
        merged.set(chunk, offset);
        offset += chunk.length;
    }

    // 하나로 합친 PCM 파형을 반환합니다.
    return merged;
}

// 선형 보간을 사용하여 임의 샘플링 주파수의 파형을 Whisper 표준 16kHz로 변환합니다.
function resampleTo16k(input, sourceRate) {
    // 이미 16kHz이면 원본 배열의 복사본을 반환합니다.
    if (sourceRate === 16000) return new Float32Array(input);

    // 비정상적인 입력 주파수는 명확한 오류로 처리합니다.
    if (!Number.isFinite(sourceRate) || sourceRate <= 0) {
        throw new Error("마이크 샘플링 주파수를 확인할 수 없습니다.");
    }

    // 주파수 비율에 따라 변환 후 필요한 샘플 수를 계산합니다.
    const outputLength = Math.max(1, Math.round(input.length * 16000 / sourceRate));

    // 계산한 크기의 출력 파형 배열을 만듭니다.
    const output = new Float32Array(outputLength);

    // 각 출력 샘플이 원본 파형의 어느 실수 위치에 대응하는지 계산해 보간합니다.
    for (let index = 0; index < outputLength; index += 1) {
        const sourcePosition = index * sourceRate / 16000;
        const leftIndex = Math.floor(sourcePosition);
        const rightIndex = Math.min(leftIndex + 1, input.length - 1);
        const fraction = sourcePosition - leftIndex;
        output[index] = input[leftIndex] * (1 - fraction) + input[rightIndex] * fraction;
    }

    // 16kHz PCM 파형을 반환합니다.
    return output;
}

// Float32 모노 파형을 서버가 바로 읽을 수 있는 16비트 PCM WAV Blob으로 인코딩합니다.
function encodePcmWav(samples, sampleRate = 16000) {
    // WAV 헤더 44바이트와 샘플당 2바이트를 합친 버퍼를 생성합니다.
    const buffer = new ArrayBuffer(44 + samples.length * 2);

    // WAV 헤더와 PCM 정수를 기록할 DataView를 생성합니다.
    const view = new DataView(buffer);

    // RIFF/WAVE 표준 헤더를 순서대로 기록합니다.
    writeAscii(view, 0, "RIFF");
    view.setUint32(4, 36 + samples.length * 2, true);
    writeAscii(view, 8, "WAVE");
    writeAscii(view, 12, "fmt ");
    view.setUint32(16, 16, true);
    view.setUint16(20, 1, true);
    view.setUint16(22, 1, true);
    view.setUint32(24, sampleRate, true);
    view.setUint32(28, sampleRate * 2, true);
    view.setUint16(32, 2, true);
    view.setUint16(34, 16, true);
    writeAscii(view, 36, "data");
    view.setUint32(40, samples.length * 2, true);

    // 부동소수점 파형을 -32768~32767 범위의 16비트 PCM으로 변환합니다.
    let offset = 44;
    for (let index = 0; index < samples.length; index += 1) {
        const clipped = Math.max(-1, Math.min(1, samples[index]));
        const pcmValue = clipped < 0 ? clipped * 0x8000 : clipped * 0x7fff;
        view.setInt16(offset, pcmValue, true);
        offset += 2;
    }

    // MIME 형식과 실제 파일 내용이 모두 WAV인 Blob을 반환합니다.
    return new Blob([view], { type: "audio/wav" });
}

// 녹음에 사용한 마이크와 Web Audio 노드를 안전하게 해제합니다.
async function releaseRecordingResources() {
    // ScriptProcessor 콜백을 제거하고 오디오 그래프에서 분리합니다.
    if (recordingProcessorNode) {
        recordingProcessorNode.onaudioprocess = null;
        recordingProcessorNode.disconnect();
    }

    // 마이크 입력 노드를 오디오 그래프에서 분리합니다.
    if (recordingSourceNode) recordingSourceNode.disconnect();

    // 무음 출력 노드를 분리합니다.
    if (recordingSilenceNode) recordingSilenceNode.disconnect();

    // 마이크 스트림의 모든 트랙을 중지하여 브라우저의 마이크 사용 표시를 끕니다.
    if (microphoneStream) microphoneStream.getTracks().forEach((track) => track.stop());

    // AudioContext가 열려 있으면 비동기로 닫습니다.
    if (recordingAudioContext && recordingAudioContext.state !== "closed") {
        await recordingAudioContext.close();
    }

    // 다음 녹음을 위해 모든 객체 참조를 초기화합니다.
    microphoneStream = null;
    recordingAudioContext = null;
    recordingSourceNode = null;
    recordingProcessorNode = null;
    recordingSilenceNode = null;
}

// 수집한 PCM 데이터를 표준 WAV로 만들어 FastAPI STT 엔드포인트에 전송합니다.
async function sendRecordedPcmToStt() {
    // 녹음 시간이 지나치게 짧으면 모델 요청 전에 사용자에게 다시 녹음하도록 안내합니다.
    const recordedSeconds = (Date.now() - recordingStartedAt) / 1000;
    if (recordedSeconds < 0.8 || recordedPcmChunks.length === 0) {
        throw new Error("1초 이상 또렷하게 말한 뒤 녹음을 종료하세요.");
    }

    // 녹음 중 수집한 모든 PCM 조각을 하나의 연속 파형으로 합칩니다.
    const mergedPcm = mergeFloat32Chunks(recordedPcmChunks);

    // 마이크의 실제 샘플링 주파수에서 Whisper 표준 16kHz로 변환합니다.
    const pcm16k = resampleTo16k(mergedPcm, recordingAudioContext.sampleRate);

    // 변환된 파형을 실제 16비트 PCM WAV 파일로 인코딩합니다.
    const wavBlob = encodePcmWav(pcm16k, 16000);

    // WAV 파일의 크기가 비정상적으로 작으면 빈 녹음으로 처리합니다.
    if (wavBlob.size <= 44) {
        throw new Error("녹음된 음성 데이터가 없습니다.");
    }

    // FastAPI 파일 업로드 요청을 위한 FormData를 생성합니다.
    const formData = new FormData();

    // 브라우저가 임의의 WebM 형식으로 바꾸지 못하도록 명시적인 WAV 파일 객체를 추가합니다.
    formData.append("file", new File([wavBlob], "recording.wav", { type: "audio/wav" }));

    // 사용자에게 서버 STT 변환이 진행 중임을 표시합니다.
    byId("recordStatus").textContent = "음성을 텍스트로 변환 중...";
    showMessage("PyTorch Whisper가 한국어 음성을 분석하고 있습니다.");

    // FastAPI STT 엔드포인트로 WAV 파일을 전송합니다.
    const response = await fetch("/api/stt", { method: "POST", body: formData });

    // 서버 오류가 있으면 JSON의 상세 원인을 읽어 예외로 전환합니다.
    if (!response.ok) throw new Error(await parseError(response));

    // 정상 응답의 한국어 인식 결과를 읽습니다.
    const data = await response.json();

    // STT 결과를 Stable Diffusion 프롬프트 입력창에 자동 입력합니다.
    byId("prompt").value = data.text;

    // 완료 상태와 인식 결과를 화면에 표시합니다.
    byId("recordStatus").textContent = "STT 변환 완료";
    showMessage(`인식 결과: ${data.text}`);
}

// 마이크 녹음 버튼 클릭 시 PCM 녹음을 시작하거나 종료합니다.
byId("recordButton").addEventListener("click", async () => {
    // 현재 녹음 중이면 PCM 수집을 중지하고 WAV 변환 및 STT 요청을 실행합니다.
    if (isRecording) {
        isRecording = false;
        byId("recordButton").disabled = true;
        byId("recordStatus").textContent = "WAV 파일 생성 중...";

        try {
            // AudioContext를 닫기 전에 현재 샘플링 주파수를 사용하여 STT 요청을 완료합니다.
            await sendRecordedPcmToStt();
        } catch (error) {
            // WAV 생성 또는 STT 처리 오류를 사용자에게 표시합니다.
            byId("recordStatus").textContent = "STT 변환 실패";
            showMessage(`STT 변환 실패: ${error.message}`, true);
        } finally {
            // 마이크와 오디오 노드를 반드시 해제합니다.
            await releaseRecordingResources();

            // 다음 녹음을 시작할 수 있도록 버튼 상태를 복원합니다.
            recordedPcmChunks = [];
            byId("recordButton").disabled = false;
            byId("recordButton").classList.remove("recording");
            byId("recordButton").textContent = "● 음성 녹음 시작";
        }
        return;
    }

    try {
        // HTTPS 또는 localhost 환경에서 브라우저 마이크 권한을 요청합니다.
        microphoneStream = await navigator.mediaDevices.getUserMedia({
            audio: {
                channelCount: 1,
                echoCancellation: true,
                noiseSuppression: true,
                autoGainControl: true,
            },
        });

        // 브라우저의 Web Audio API 클래스를 가져옵니다.
        const AudioContextClass = window.AudioContext || window.webkitAudioContext;
        if (!AudioContextClass) {
            throw new Error("이 브라우저는 Web Audio API를 지원하지 않습니다.");
        }

        // 마이크 원본 주파수로 AudioContext를 생성합니다.
        recordingAudioContext = new AudioContextClass();

        // 브라우저 정책으로 일시 중지된 경우 사용자 클릭 안에서 다시 시작합니다.
        if (recordingAudioContext.state === "suspended") {
            await recordingAudioContext.resume();
        }

        // 마이크 MediaStream을 Web Audio 입력 노드로 연결합니다.
        recordingSourceNode = recordingAudioContext.createMediaStreamSource(microphoneStream);

        // PCM 샘플을 안정적으로 수집할 ScriptProcessorNode를 생성합니다.
        recordingProcessorNode = recordingAudioContext.createScriptProcessor(4096, 1, 1);

        // 스피커로 마이크 소리가 들리지 않게 gain 값을 0으로 설정한 출력 노드를 만듭니다.
        recordingSilenceNode = recordingAudioContext.createGain();
        recordingSilenceNode.gain.value = 0;

        // 새로운 녹음 전에 이전 PCM 데이터를 제거합니다.
        recordedPcmChunks = [];

        // 오디오 콜백마다 첫 번째 채널의 PCM을 복사하여 보관합니다.
        recordingProcessorNode.onaudioprocess = (event) => {
            if (!isRecording) return;
            const inputChannel = event.inputBuffer.getChannelData(0);
            recordedPcmChunks.push(new Float32Array(inputChannel));
        };

        // 마이크 → PCM 처리 노드 → 무음 출력 → 스피커 목적지 순서로 연결합니다.
        recordingSourceNode.connect(recordingProcessorNode);
        recordingProcessorNode.connect(recordingSilenceNode);
        recordingSilenceNode.connect(recordingAudioContext.destination);

        // 녹음 상태와 시작 시간을 기록합니다.
        isRecording = true;
        recordingStartedAt = Date.now();

        // 버튼과 상태 영역을 녹음 중 화면으로 변경합니다.
        byId("recordButton").classList.add("recording");
        byId("recordButton").textContent = "■ 녹음 종료";
        byId("recordStatus").textContent = "마이크 PCM 녹음 중";
        showMessage("1초 이상 또렷하게 말한 뒤 녹음 종료 버튼을 누르세요.");
    } catch (error) {
        // 권한 거부나 오디오 장치 오류가 발생하면 사용한 리소스를 정리합니다.
        isRecording = false;
        await releaseRecordingResources();
        showMessage(`마이크를 사용할 수 없습니다: ${error.message}`, true);
    }
});

// Stable Diffusion 폼 제출 이벤트를 처리합니다.
byId("diffusionForm").addEventListener("submit", async (event) => {
    // 브라우저의 기본 폼 이동을 차단합니다.
    event.preventDefault();
    // 제출 버튼을 가져옵니다.
    const submitButton = event.submitter;
    // 현재 폼 값을 그대로 multipart/form-data로 구성합니다.
    const formData = new FormData(event.currentTarget);
    // 빈 시드는 FastAPI 정수 변환 오류를 피하기 위해 전송 데이터에서 제거합니다.
    if (!byId("seed").value.trim()) formData.delete("seed");
    // 중복 생성을 막기 위해 버튼을 비활성화합니다.
    submitButton.disabled = true;
    // 모델 다운로드와 CPU 생성 시간이 길 수 있음을 안내합니다.
    showMessage("이미지를 생성하고 있습니다. CPU에서는 수 분 이상 걸릴 수 있습니다.");
    try {
        // Stable Diffusion API에 생성 요청을 보냅니다.
        const response = await fetch("/api/generate", { method: "POST", body: formData });
        // 오류 상태이면 상세 메시지를 읽습니다.
        if (!response.ok) throw new Error(await parseError(response));
        // 결과 JSON을 읽습니다.
        const data = await response.json();
        // 생성 이미지 URL을 이미지 요소에 지정합니다.
        byId("generatedImage").src = `${data.image_url}?t=${Date.now()}`;
        // 재현에 사용할 시드를 화면에 표시합니다.
        byId("generatedSeed").textContent = data.seed;
        // 한국어 입력이 실제로 어떤 영어 장면 설명으로 변환됐는지 표시합니다.
        byId("generatedEnglishPrompt").textContent = data.prompt_english || data.prompt_original;
        // 결과 카드를 표시합니다.
        byId("diffusionResult").classList.remove("hidden");
        // 완료 메시지를 표시합니다.
        showMessage("Stable Diffusion 이미지 생성이 완료되었습니다.");
    } catch (error) {
        // 다운로드, 메모리 또는 서버 오류를 표시합니다.
        showMessage(error.message, true);
    } finally {
        // 다음 요청을 위해 버튼을 다시 활성화합니다.
        submitButton.disabled = false;
    }
});

// 현재 Stable Diffusion 프롬프트를 서버 TTS로 읽습니다.
byId("promptTtsButton").addEventListener("click", () => {
    // 프롬프트 입력값과 전용 오디오 요소를 전달합니다.
    playServerTts(byId("prompt").value, byId("promptAudio"));
});
