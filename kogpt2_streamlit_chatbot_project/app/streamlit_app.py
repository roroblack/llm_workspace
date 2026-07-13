"""
Streamlit으로 KoGPT2 한국어 챗봇 화면을 구현하는 실행 파일입니다.

PyCharm 터미널에서 다음 명령으로 실행합니다.

streamlit run app/streamlit_app.py
"""

# 프로젝트 루트 경로를 파이썬 모듈 검색 경로에 추가하기 위한 기본 라이브러리입니다.
# app 폴더에서 실행해도 src 패키지를 안정적으로 import하기 위해 사용합니다.
import sys

# 파일 경로를 운영체제에 맞게 다루기 위한 pathlib 모듈입니다.
# Windows와 macOS/Linux에서 모두 안전하게 프로젝트 루트 경로를 계산할 수 있습니다.
from pathlib import Path

# Streamlit 웹 화면을 만들기 위한 라이브러리입니다.
# 채팅 UI, 입력창, 사이드바, 버튼, 표 등을 구현합니다.
import streamlit as st

# 현재 파일의 상위 폴더를 기준으로 프로젝트 루트 경로를 계산합니다.
# app/streamlit_app.py의 부모는 app이고, 그 부모가 프로젝트 루트입니다.
PROJECT_ROOT = Path(__file__).resolve().parents[1]

# 프로젝트 루트 경로가 sys.path에 없으면 추가합니다.
# 이렇게 해야 "from src..." 형태의 import가 정상 작동합니다.
if str(PROJECT_ROOT) not in sys.path:
    # 파이썬 모듈 검색 경로의 맨 앞에 프로젝트 루트를 추가합니다.
    # 같은 이름의 외부 패키지보다 현재 프로젝트의 src를 우선 찾게 됩니다.
    sys.path.insert(0, str(PROJECT_ROOT))

# 챗봇 모델 클래스와 생성 옵션 클래스를 불러옵니다.
# 실제 모델 로딩과 답변 생성은 src/chatbot.py에서 담당합니다.
from src.chatbot import GenerationOptions, KoGPT2Chatbot

# Streamlit 화면에 표시할 기본 환영 메시지를 불러옵니다.
# 안내 문구를 config.py에서 관리하면 문구 수정이 쉬워집니다.
from src.config import (
    DEFAULT_MAX_NEW_TOKENS,
    DEFAULT_NO_REPEAT_NGRAM_SIZE,
    DEFAULT_REPETITION_PENALTY,
    DEFAULT_TEMPERATURE,
    DEFAULT_TOP_K,
    DEFAULT_TOP_P,
    WELCOME_MESSAGE,
)


# Streamlit 페이지의 기본 설정을 지정합니다.
# 페이지 제목, 아이콘, 레이아웃을 앱 시작 시 한 번 설정합니다.
st.set_page_config(
    page_title="KoGPT2 한국어 챗봇",   # 브라우저 탭에 표시될 제목입니다.
    page_icon="🤖",                   # 브라우저 탭과 앱 상단에 표시될 아이콘입니다.
    layout="wide",                    # 넓은 화면 레이아웃을 사용합니다.
)


# Streamlit 캐시를 이용해 모델을 한 번만 로드하는 함수를 정의합니다.
# 모델은 용량이 크므로 매 화면 갱신마다 다시 로드하면 매우 느려집니다.
@st.cache_resource(show_spinner="KoGPT2 모델을 불러오는 중입니다. 처음 실행 시 시간이 걸릴 수 있습니다.")
def load_chatbot() -> KoGPT2Chatbot:
    # KoGPT2 챗봇 객체를 생성합니다.
    # 최초 실행 시 Hugging Face Hub에서 모델과 토크나이저를 다운로드합니다.
    chatbot = KoGPT2Chatbot()

    # 로드된 챗봇 객체를 반환합니다.
    # Streamlit은 이 객체를 캐시에 저장하여 재사용합니다.
    return chatbot


# 세션 상태에 대화 이력이 없으면 초기화합니다.
# Streamlit은 사용자 입력 때마다 스크립트를 다시 실행하므로 session_state가 필요합니다.
if "messages" not in st.session_state:
    # messages에는 {"role": "user" 또는 "assistant", "content": "..."} 형식의 딕셔너리를 저장합니다.
    st.session_state.messages = []

# 세션 상태에 마지막 토큰 분석 결과가 없으면 초기화합니다.
# 사용자가 입력한 문장의 토큰화 결과를 화면 아래에 보여주기 위해 사용합니다.
if "last_tokens" not in st.session_state:
    # 토큰 분석 결과는 처음에는 비어 있는 리스트입니다.
    st.session_state.last_tokens = []


# 화면 상단 제목을 출력합니다.
# 사용자가 현재 앱의 목적을 바로 알 수 있도록 합니다.
st.title("🤖 KoGPT2 한국어 챗봇")

# 화면 상단 설명 문구를 출력합니다.
# 이 앱이 업로드된 GPT KoGPT2 노트북 코드를 PyCharm 프로젝트 구조로 바꾼 것임을 설명합니다.
st.caption("PyTorch + Hugging Face Transformers + Streamlit 기반 한국어 문장 생성 챗봇 앱")


# 왼쪽 사이드바 영역을 구성합니다.
# 생성 옵션을 사용자가 직접 조절할 수 있도록 슬라이더를 배치합니다.
with st.sidebar:
    # 사이드바 제목을 표시합니다.
    st.header("생성 옵션")

    # 새로 생성할 토큰 수를 조절하는 슬라이더입니다.
    # 값이 커질수록 답변은 길어지지만 실행 시간이 증가할 수 있습니다.
    max_new_tokens = st.slider(
        "최대 생성 토큰 수",  # 슬라이더 라벨입니다.
        min_value=10,          # 최소 생성 토큰 수입니다.
        max_value=120,         # 최대 생성 토큰 수입니다.
        value=DEFAULT_MAX_NEW_TOKENS, # 기본 생성 토큰 수입니다.
        step=10,               # 한 번 움직일 때 증가/감소하는 단위입니다.
    )

    # temperature 값을 조절하는 슬라이더입니다.
    # 낮으면 안정적이고 높으면 다양한 답변이 생성됩니다.
    temperature = st.slider(
        "Temperature",         # 슬라이더 라벨입니다.
        min_value=0.20,        # 최소 temperature 값입니다.
        max_value=1.20,        # 최대 temperature 값입니다.
        value=DEFAULT_TEMPERATURE, # 기본 temperature 값입니다.
        step=0.05,             # 한 번 움직일 때 증가/감소하는 단위입니다.
    )

    # top_p 값을 조절하는 슬라이더입니다.
    # 확률이 높은 후보군 안에서 답변을 생성하도록 돕습니다.
    top_p = st.slider(
        "Top-p",               # 슬라이더 라벨입니다.
        min_value=0.50,        # 최소 top_p 값입니다.
        max_value=1.00,        # 최대 top_p 값입니다.
        value=DEFAULT_TOP_P,   # 기본 top_p 값입니다.
        step=0.01,             # 한 번 움직일 때 증가/감소하는 단위입니다.
    )

    # top_k 값을 조절하는 슬라이더입니다.
    # 상위 k개 후보 토큰만 선택 대상으로 사용합니다.
    top_k = st.slider(
        "Top-k",               # 슬라이더 라벨입니다.
        min_value=10,          # 최소 top_k 값입니다.
        max_value=100,         # 최대 top_k 값입니다.
        value=DEFAULT_TOP_K,   # 기본 top_k 값입니다.
        step=5,                # 한 번 움직일 때 증가/감소하는 단위입니다.
    )

    # repetition_penalty 값을 조절하는 슬라이더입니다.
    # 같은 말이 반복되는 현상을 줄이는 데 사용합니다.
    repetition_penalty = st.slider(
        "반복 패널티",          # 슬라이더 라벨입니다.
        min_value=1.00,        # 반복 패널티 최소값입니다.
        max_value=1.50,        # 반복 패널티 최대값입니다.
        value=DEFAULT_REPETITION_PENALTY, # 기본 반복 패널티 값입니다.
        step=0.01,             # 한 번 움직일 때 증가/감소하는 단위입니다.
    )

    # no_repeat_ngram_size 값을 조절하는 슬라이더입니다.
    # 같은 구절이 반복되는 것을 줄입니다.
    no_repeat_ngram_size = st.slider(
        "반복 금지 n-gram 크기", # 슬라이더 라벨입니다.
        min_value=0,             # 0이면 n-gram 반복 금지를 사용하지 않습니다.
        max_value=5,             # 최대 n-gram 크기입니다.
        value=DEFAULT_NO_REPEAT_NGRAM_SIZE, # 기본 n-gram 크기입니다.
        step=1,                  # 한 번 움직일 때 증가/감소하는 단위입니다.
    )

    # 대화 초기화 버튼을 만듭니다.
    # 버튼을 누르면 세션에 저장된 대화 이력을 삭제합니다.
    clear_clicked = st.button("대화 초기화")

    # 사용자가 대화 초기화 버튼을 누른 경우를 처리합니다.
    # messages와 토큰 분석 결과를 모두 비웁니다.
    if clear_clicked:
        # 저장된 대화 메시지를 빈 리스트로 초기화합니다.
        st.session_state.messages = []

        # 저장된 토큰 분석 결과를 빈 리스트로 초기화합니다.
        st.session_state.last_tokens = []

        # 화면을 즉시 다시 실행하여 초기화 결과를 반영합니다.
        st.rerun()


# 모델을 캐시에서 불러오거나 최초 한 번 로드합니다.
# 이 시점에 모델 다운로드 또는 로딩이 수행될 수 있습니다.
chatbot = load_chatbot()

# 사이드바에 모델 정보를 표시합니다.
# 사용자가 어떤 모델과 장치로 실행 중인지 확인할 수 있습니다.
with st.sidebar:
    # 구분선을 표시합니다.
    st.divider()

    # 모델 정보 섹션 제목을 표시합니다.
    st.header("모델 정보")

    # 챗봇 객체에서 모델 실행 정보를 가져옵니다.
    model_info = chatbot.get_model_info()

    # 사용 중인 Hugging Face 모델 이름을 표시합니다.
    st.write("모델:", model_info["model_name"])

    # 현재 실행 장치를 표시합니다.
    st.write("실행 장치:", model_info["device"])

    # 종료 토큰 정보를 표시합니다.
    st.write("종료 토큰:", model_info["eos_token"])


# 대화가 아직 없으면 환영 안내 메시지를 표시합니다.
# 첫 화면이 비어 있지 않도록 기본 설명을 제공합니다.
if not st.session_state.messages:
    # assistant 역할로 환영 메시지를 채팅 영역에 표시합니다.
    with st.chat_message("assistant"):
        # 기본 환영 문구를 출력합니다.
        st.write(WELCOME_MESSAGE)


# 저장된 모든 대화 메시지를 화면에 다시 출력합니다.
# Streamlit은 매 입력마다 전체 스크립트를 재실행하므로 이 과정이 필요합니다.
for message in st.session_state.messages:
    # 메시지 역할에 맞는 채팅 말풍선을 만듭니다.
    with st.chat_message(message["role"]):
        # 메시지 내용을 화면에 출력합니다.
        st.write(message["content"])


# 사용자가 새 메시지를 입력할 수 있는 채팅 입력창을 만듭니다.
# 입력 후 Enter를 누르면 prompt 변수에 문자열이 들어옵니다.
prompt = st.chat_input("질문이나 시작 문장을 입력하세요.")

# 사용자가 실제로 메시지를 입력했을 때만 답변 생성을 수행합니다.
# 입력이 없으면 None이므로 아래 코드는 실행되지 않습니다.
if prompt:
    # 사용자 메시지를 세션 대화 이력에 추가합니다.
    # 이후 화면 재실행 시에도 이전 대화가 유지됩니다.
    st.session_state.messages.append({"role": "user", "content": prompt})

    # 사용자 메시지를 화면에 즉시 표시합니다.
    # 답변 생성 전에 사용자의 입력을 채팅 영역에 보여줍니다.
    with st.chat_message("user"):
        # 사용자가 입력한 문장을 출력합니다.
        st.write(prompt)

    # Streamlit 슬라이더 값을 GenerationOptions 객체로 묶습니다.
    # 모델 생성 함수에 여러 옵션을 깔끔하게 전달하기 위한 처리입니다.
    options = GenerationOptions(
        max_new_tokens=max_new_tokens,                         # 최대 생성 토큰 수입니다.
        temperature=temperature,                               # 생성 다양성 값입니다.
        top_p=top_p,                                           # nucleus sampling 누적 확률입니다.
        top_k=top_k,                                           # 상위 후보 토큰 수입니다.
        repetition_penalty=repetition_penalty,                 # 반복 표현 패널티입니다.
        no_repeat_ngram_size=no_repeat_ngram_size,             # 반복 금지 n-gram 크기입니다.
    )

    # 답변 생성 중임을 알려주는 스피너를 표시합니다.
    # 모델 추론 시간이 걸릴 수 있으므로 사용자에게 진행 상태를 보여줍니다.
    with st.spinner("KoGPT2가 답변을 생성하는 중입니다..."):
        # 현재 사용자 입력의 토큰 분석 결과를 저장합니다.
        # 화면 하단에서 토큰 ID와 토큰 문자열을 확인할 수 있습니다.
        st.session_state.last_tokens = chatbot.analyze_tokens(prompt)

        # 최근 대화 이력을 모델에 전달합니다.
        # 방금 추가한 사용자 메시지는 reply 내부에서 새 입력으로 처리하므로 history에서는 제외합니다.
        history = st.session_state.messages[:-1]

        # KoGPT2 모델을 사용하여 챗봇 답변을 생성합니다.
        # 생성 옵션은 사이드바 슬라이더 값이 반영됩니다.
        answer = chatbot.reply(user_message=prompt, history=history, options=options)

    # 챗봇 답변을 세션 대화 이력에 추가합니다.
    # 이후 화면 재실행 시에도 답변이 유지됩니다.
    st.session_state.messages.append({"role": "assistant", "content": answer})

    # 챗봇 답변을 화면에 표시합니다.
    # assistant 역할의 채팅 말풍선으로 출력합니다.
    with st.chat_message("assistant"):
        # 생성된 답변 문장을 출력합니다.
        st.write(answer)


# 화면 아래쪽에 토큰 분석 섹션을 만듭니다.
# 교육용 프로젝트이므로 사용자가 입력 문장이 어떻게 토큰화되는지 확인할 수 있게 합니다.
with st.expander("마지막 입력 문장의 토큰 분석 보기"):
    # 토큰 분석 결과가 있으면 표로 표시합니다.
    # 각 행은 토큰 ID와 토큰 문자열로 구성됩니다.
    if st.session_state.last_tokens:
        # Streamlit 표에 표시할 딕셔너리 리스트를 만듭니다.
        token_rows = [
            {"token_id": token_id, "token": token}  # 각 토큰의 ID와 문자열입니다.
            for token_id, token in st.session_state.last_tokens
        ]

        # 토큰 분석 결과를 표 형태로 출력합니다.
        st.dataframe(token_rows, use_container_width=True)

    # 아직 분석할 입력이 없으면 안내 문구를 표시합니다.
    # 사용자가 먼저 채팅 입력을 해야 토큰 분석이 가능합니다.
    else:
        # 토큰 분석 결과가 없다는 메시지를 출력합니다.
        st.write("아직 분석할 입력 문장이 없습니다.")
