"""
KoGPT2 모델을 불러오고 한국어 답변을 생성하는 핵심 모듈입니다.

Streamlit 화면 코드는 UI에 집중하고, 모델 로딩과 추론 로직은 이 파일에 분리했습니다.
이렇게 분리하면 PyCharm 프로젝트에서 유지보수하기 쉽고, 나중에 FastAPI나 다른 UI로 바꾸기도 쉽습니다.
"""

# 운영체제 환경 변수 접근을 위한 파이썬 기본 라이브러리입니다.
# 토크나이저 병렬 처리 경고를 줄이기 위해 사용합니다.
import os

# 표준 출력 인코딩을 재설정하기 위한 파이썬 기본 라이브러리입니다.
# Windows 콘솔 환경에서 한글 출력이 깨지는 문제를 줄이는 보조 설정에 사용합니다.
import sys

# 타입 힌트를 위한 dataclass를 불러옵니다.
# 생성 옵션을 하나의 객체로 묶어 관리하기 위해 사용합니다.
from dataclasses import dataclass

# PyTorch 라이브러리입니다.
# Tensor 생성, GPU/CPU 장치 선택, 모델 추론에 사용합니다.
import torch

# KoGPT2 전용 특수 토큰을 명시하여 빠른 토크나이저를 불러오기 위한 클래스입니다.
# 노트북에서 한글 깨짐 문제를 줄이기 위해 사용한 방식과 동일합니다.
from transformers import PreTrainedTokenizerFast

# GPT2 계열 언어 모델을 불러오는 클래스입니다.
# KoGPT2는 GPT2 계열 구조이므로 GPT2LMHeadModel로 문장 생성을 수행할 수 있습니다.
from transformers import GPT2LMHeadModel

# 프로젝트 공통 설정값을 불러옵니다.
# 모델 이름과 기본 생성 옵션을 중앙에서 관리합니다.
from src.config import (
    DEFAULT_MAX_NEW_TOKENS,
    DEFAULT_NO_REPEAT_NGRAM_SIZE,
    DEFAULT_REPETITION_PENALTY,
    DEFAULT_TEMPERATURE,
    DEFAULT_TOP_K,
    DEFAULT_TOP_P,
    MODEL_NAME,
)

# 생성 결과 정리와 대화 프롬프트 생성을 위한 유틸리티 함수를 불러옵니다.
# UI와 모델 로직에서 문자열 후처리를 중복 작성하지 않도록 분리했습니다.
from src.utils.text_cleaner import (
    build_chat_prompt,
    clean_generated_text,
    extract_answer,
    fallback_answer,
    get_rule_based_reply,
    is_low_quality_answer,
)


# 토크나이저 병렬 처리 경고를 줄이기 위해 환경 변수를 설정합니다.
# Streamlit 재실행 과정에서 불필요한 경고가 반복 출력되는 것을 줄입니다.
os.environ["TOKENIZERS_PARALLELISM"] = "false"


# 현재 실행 환경이 표준 출력 인코딩 재설정을 지원하는지 확인합니다.
# 일부 Windows 콘솔에서는 기본 인코딩 때문에 한글 출력이 깨질 수 있습니다.
if hasattr(sys.stdout, "reconfigure"):
    # 표준 출력 인코딩을 UTF-8로 설정합니다.
    # print 로그에 한글이 포함될 때 깨짐을 줄이는 보조 설정입니다.
    sys.stdout.reconfigure(encoding="utf-8")


# 문장 생성 옵션을 하나의 객체로 묶기 위한 데이터 클래스를 정의합니다.
# 함수 인자가 많아지는 것을 줄이고, Streamlit 슬라이더 값 전달을 단순하게 만듭니다.
@dataclass
class GenerationOptions:
    # 새로 생성할 최대 토큰 수입니다.
    # 토큰 수가 많을수록 답변이 길어지지만 속도는 느려질 수 있습니다.
    max_new_tokens: int = DEFAULT_MAX_NEW_TOKENS

    # 생성 다양성을 조절하는 temperature 값입니다.
    # 낮으면 안정적이고, 높으면 창의적이지만 문장이 흔들릴 수 있습니다.
    temperature: float = DEFAULT_TEMPERATURE

    # nucleus sampling의 누적 확률 기준입니다.
    # 확률이 높은 후보군 안에서 자연스럽게 샘플링하도록 돕습니다.
    top_p: float = DEFAULT_TOP_P

    # 상위 k개 후보 토큰만 선택 대상으로 사용하는 값입니다.
    # 후보 범위를 제한하여 너무 엉뚱한 토큰이 선택되는 것을 줄입니다.
    top_k: int = DEFAULT_TOP_K

    # 반복 표현을 줄이기 위한 패널티 값입니다.
    # 1.0보다 큰 값을 사용하면 이미 나온 표현의 반복 가능성이 낮아집니다.
    repetition_penalty: float = DEFAULT_REPETITION_PENALTY

    # 같은 n-gram 구절 반복을 막는 값입니다.
    # 3이면 같은 3토큰 묶음이 반복되지 않도록 제한합니다.
    no_repeat_ngram_size: int = DEFAULT_NO_REPEAT_NGRAM_SIZE


# KoGPT2 챗봇 클래스를 정의합니다.
# 모델과 토크나이저를 한 번 로드한 뒤 여러 번 재사용하도록 구성합니다.
class KoGPT2Chatbot:
    # 클래스 생성자입니다.
    # model_name을 바꾸면 다른 GPT2 계열 한국어 모델로 교체할 수 있습니다.
    def __init__(self, model_name: str = MODEL_NAME) -> None:
        # 사용할 Hugging Face 모델 이름을 인스턴스 변수에 저장합니다.
        # 이후 모델 로딩과 화면 표시에서 같은 값을 재사용합니다.
        self.model_name = model_name

        # GPU가 가능하면 cuda를 사용하고, 아니면 CPU를 사용합니다.
        # PyTorch 모델과 입력 Tensor는 반드시 같은 장치에 있어야 합니다.
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

        # KoGPT2 토크나이저를 노트북에서 사용한 방식 그대로 불러옵니다.
        # 특수 토큰을 명시하면 디코딩 안정성과 generate 설정이 좋아집니다.
        self.tokenizer = PreTrainedTokenizerFast.from_pretrained(
            self.model_name,          # Hugging Face Hub에서 불러올 모델 이름입니다.
            bos_token="</s>",         # 문장 시작 토큰입니다.
            eos_token="</s>",         # 문장 종료 토큰입니다.
            unk_token="<unk>",        # 알 수 없는 토큰입니다.
            pad_token="<pad>",        # 패딩 토큰입니다.
            mask_token="<mask>",      # 마스크 토큰입니다.
        )

        # KoGPT2 언어 모델을 GPT2LMHeadModel 클래스로 불러옵니다.
        # 이 모델은 입력 토큰 뒤에 이어질 다음 토큰을 예측하여 문장을 생성합니다.
        self.model = GPT2LMHeadModel.from_pretrained(self.model_name)

        # 모델을 선택된 장치로 이동합니다.
        # GPU가 있으면 GPU 메모리로, 없으면 CPU 메모리로 이동합니다.
        self.model = self.model.to(self.device)

        # 추론 전용으로 모델을 평가 모드로 전환합니다.
        # Dropout 같은 학습 전용 동작을 비활성화하여 결과를 안정화합니다.
        self.model.eval()

        # generate() 함수가 패딩 토큰을 정확히 알 수 있도록 설정합니다.
        # 이 설정이 없으면 attention mask 관련 경고가 발생할 수 있습니다.
        self.model.config.pad_token_id = self.tokenizer.pad_token_id

        # generate() 함수가 문장 종료 토큰을 정확히 알 수 있도록 설정합니다.
        # 종료 토큰이 생성되면 답변 생성을 멈출 수 있습니다.
        self.model.config.eos_token_id = self.tokenizer.eos_token_id

        # generate() 함수가 문장 시작 토큰도 참조할 수 있도록 설정합니다.
        # GPT 계열 모델 설정의 완성도를 높이는 역할을 합니다.
        self.model.config.bos_token_id = self.tokenizer.bos_token_id

    # 챗봇 답변을 생성하는 메서드입니다.
    # user_message에는 사용자가 Streamlit 입력창에 입력한 문장이 들어옵니다.
    def reply(
        self,
        user_message: str,
        history: list[dict[str, str]] | None = None,
        options: GenerationOptions | None = None,
    ) -> str:
        # 생성 옵션이 전달되지 않으면 기본 옵션 객체를 생성합니다.
        # 이렇게 하면 호출 코드에서 매번 모든 옵션을 지정하지 않아도 됩니다.
        options = options or GenerationOptions()

        # 사용자가 입력한 문장의 앞뒤 공백을 제거합니다.
        # 빈 공백만 입력되는 경우를 처리하기 위해 필요합니다.
        user_message = user_message.strip()

        # 입력 문장이 비어 있으면 안내 문장을 반환합니다.
        # 모델에 빈 문자열을 넣으면 의미 없는 결과가 생성될 수 있습니다.
        if not user_message:
            return "질문이나 시작 문장을 입력해 주세요."

        # 짧은 인사처럼 base 모델이 문맥을 잡기 어려운 입력은 안정적인 답변을 먼저 사용합니다.
        rule_reply = get_rule_based_reply(user_message)
        if rule_reply:
            return rule_reply

        # 대화 이력과 현재 입력을 이용해 모델에 넣을 프롬프트를 만듭니다.
        # KoGPT2가 대화 형식으로 답변하도록 역할 라벨을 포함합니다.
        prompt = build_chat_prompt(user_message=user_message, history=history)

        # 프롬프트를 토크나이저로 정수 ID Tensor로 변환합니다.
        # return_tensors="pt"는 PyTorch Tensor로 반환하라는 의미입니다.
        encoded = self.tokenizer(
            prompt,                         # 모델에 입력할 대화 프롬프트입니다.
            return_tensors="pt",            # PyTorch Tensor 형태로 인코딩 결과를 받습니다.
            add_special_tokens=False,       # KoGPT2 프롬프트에는 별도 특수 토큰을 자동 추가하지 않습니다.
        )

        # input_ids를 모델이 올라간 장치로 이동합니다.
        # 장치가 다르면 PyTorch에서 RuntimeError가 발생합니다.
        input_ids = encoded["input_ids"].to(self.device)

        # attention_mask를 모델이 올라간 장치로 이동합니다.
        # attention_mask는 실제 토큰과 패딩 토큰을 구분하는 역할을 합니다.
        attention_mask = encoded["attention_mask"].to(self.device)

        # 추론 과정에서는 기울기 계산이 필요 없으므로 비활성화합니다.
        # 메모리 사용량이 줄고 실행 속도가 좋아집니다.
        with torch.no_grad():
            # KoGPT2 generate() 함수로 답변 토큰을 생성합니다.
            # 샘플링 옵션을 사용하여 너무 단조로운 답변을 줄입니다.
            generated_ids = self.model.generate(
                input_ids=input_ids,                                      # 인코딩된 입력 토큰 ID입니다.
                attention_mask=attention_mask,                            # 패딩 여부를 알려주는 마스크입니다.
                max_new_tokens=options.max_new_tokens,                    # 새로 생성할 토큰 수입니다.
                do_sample=True,                                           # 확률적 샘플링을 사용합니다.
                temperature=options.temperature,                          # 생성 다양성을 조절합니다.
                top_p=options.top_p,                                      # 누적 확률 기준 후보 제한 값입니다.
                top_k=options.top_k,                                      # 상위 k개 후보 제한 값입니다.
                repetition_penalty=options.repetition_penalty,            # 반복 표현을 줄이는 값입니다.
                no_repeat_ngram_size=options.no_repeat_ngram_size,        # 같은 구절 반복을 막는 값입니다.
                eos_token_id=self.tokenizer.eos_token_id,                 # 문장 종료 토큰 ID입니다.
                pad_token_id=self.tokenizer.pad_token_id,                 # 패딩 토큰 ID입니다.
                use_cache=True,                                           # 이전 계산 결과를 재사용하여 속도를 높입니다.
            )

        # 입력 프롬프트를 제외하고 새로 생성된 토큰만 디코딩합니다.
        # 전체를 디코딩하면 "사용자:", "챗봇:" 같은 프롬프트 문장이 답변에 섞일 수 있습니다.
        new_token_ids = generated_ids[0][input_ids.shape[-1]:]
        full_text = self.tokenizer.decode(new_token_ids, skip_special_tokens=False)

        # 전체 생성 문자열에서 실제 챗봇 답변 부분만 추출합니다.
        # 입력 프롬프트와 불필요한 역할 라벨을 제거합니다.
        answer = extract_answer(full_text=full_text, prompt="")

        # KoGPT2 base 모델이 웹문서식 잡문을 생성하면 화면에 내보내지 않고 안내 답변으로 바꿉니다.
        if is_low_quality_answer(answer=answer, user_message=user_message):
            return fallback_answer(user_message)

        # 최종 답변 문자열을 반환합니다.
        return answer

    # 입력 문장의 토큰 분석 결과를 반환하는 메서드입니다.
    # Streamlit 화면에서 교육용으로 토큰 ID와 토큰 문자열을 보여줄 때 사용합니다.
    def analyze_tokens(self, text: str) -> list[tuple[int, str]]:
        # 입력 문장을 KoGPT2 토큰 ID 리스트로 변환합니다.
        # add_special_tokens=False는 자동 특수 토큰 추가를 막습니다.
        token_ids = self.tokenizer.encode(text, add_special_tokens=False)

        # 토큰 ID 리스트를 실제 토큰 문자열 리스트로 변환합니다.
        # KoGPT2가 문장을 어떤 조각으로 나누는지 확인할 수 있습니다.
        tokens = self.tokenizer.convert_ids_to_tokens(token_ids)

        # 토큰 ID와 토큰 문자열을 튜플로 묶어 반환합니다.
        # zip 결과를 list로 바꾸어 Streamlit에서 표 형태로 다루기 쉽게 합니다.
        return list(zip(token_ids, tokens))

    # 현재 모델 실행 정보를 딕셔너리로 반환하는 메서드입니다.
    # Streamlit 사이드바에서 모델 이름과 장치 정보를 표시할 때 사용합니다.
    def get_model_info(self) -> dict[str, str]:
        # 모델 정보 딕셔너리를 생성합니다.
        # 문자열 값으로 변환하여 화면 출력이 간단하도록 만듭니다.
        info = {
            "model_name": self.model_name,              # 사용 중인 Hugging Face 모델 이름입니다.
            "device": str(self.device),                 # 현재 실행 장치입니다.
            "pad_token": str(self.tokenizer.pad_token), # 패딩 토큰 문자열입니다.
            "eos_token": str(self.tokenizer.eos_token), # 종료 토큰 문자열입니다.
        }

        # 완성된 모델 정보 딕셔너리를 반환합니다.
        return info


# 간단한 문장 생성 함수도 제공합니다.
# Streamlit 외부에서 파이썬 코드로 빠르게 테스트할 때 사용할 수 있습니다.
def generate_once(prompt: str) -> str:
    # 챗봇 객체를 생성합니다.
    # 최초 실행 시 Hugging Face 모델 파일이 다운로드될 수 있습니다.
    chatbot = KoGPT2Chatbot()

    # 기본 옵션으로 답변을 생성합니다.
    # 사용자가 전달한 prompt를 챗봇 입력으로 사용합니다.
    answer = chatbot.reply(user_message=prompt)

    # 정리된 답변을 한 번 더 clean 처리하여 반환합니다.
    # 외부 호출에서도 출력이 깔끔하게 유지됩니다.
    return clean_generated_text(answer)
