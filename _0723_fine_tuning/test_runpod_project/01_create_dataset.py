"""
한국어 상담용 Supervised Fine-Tuning 데이터셋을 생성하는 파일입니다.

생성되는 데이터 형식은 다음과 같습니다.

{
    "messages": [
        {"role": "system", "content": "시스템 지시사항"},
        {"role": "user", "content": "사용자 질문"},
        {"role": "assistant", "content": "학습 대상 답변"}
    ]
}
"""

# json 모듈은 파이썬 객체를 JSON 문자열로 변환하거나
# JSON 문자열을 파이썬 객체로 변환할 때 사용합니다.
import json

# Path 클래스는 운영체제에 독립적인 방식으로
# 파일과 디렉터리 경로를 처리할 수 있게 합니다.
from pathlib import Path

# random 모듈은 데이터의 순서를 무작위로 섞을 때 사용합니다.
import random


# 현재 파일이 있는 디렉터리를 프로젝트의 기준 디렉터리로 지정합니다.
BASE_DIR = Path(__file__).resolve().parent

# 학습 데이터가 저장될 data 디렉터리 경로를 설정합니다.
DATA_DIR = BASE_DIR / "data"

# 학습 데이터 파일 경로를 지정합니다.
TRAIN_FILE = DATA_DIR / "train.jsonl"

# 검증 데이터 파일 경로를 지정합니다.
VALID_FILE = DATA_DIR / "valid.jsonl"

# 동일한 결과를 재현할 수 있도록 난수 시드를 고정합니다.
RANDOM_SEED = 42


# 모델에게 공통으로 적용할 시스템 프롬프트를 정의합니다.
SYSTEM_PROMPT = """
당신은 온라인 쇼핑몰의 고객 상담 AI입니다.
고객의 질문을 정확하게 이해하고 친절하고 간결하게 답변합니다.
확인되지 않은 정책이나 정보를 임의로 만들지 않습니다.
추가 정보가 필요한 경우 고객에게 필요한 정보를 요청합니다.
답변은 원칙적으로 한국어로 작성합니다.
""".strip()


# SFT 학습에 사용할 상담 데이터를 리스트로 정의합니다.
# 각 항목에서 user는 모델 입력이고 assistant는 학습할 정답입니다.
RAW_SAMPLES = [
    {
        "user": "주문한 상품을 취소하고 싶습니다.",
        "assistant": (
            "상품이 아직 배송 준비 전이라면 주문 내역에서 직접 취소할 수 있습니다. "
            "이미 배송이 시작된 경우에는 상품 수령 후 반품을 신청해야 합니다. "
            "정확한 상태를 확인하려면 주문번호를 알려주세요."
        ),
    },
    {
        "user": "배송은 보통 얼마나 걸리나요?",
        "assistant": (
            "일반 배송은 결제 완료 후 평균 2~3영업일 정도 소요됩니다. "
            "도서산간 지역이나 주문량이 많은 기간에는 배송이 지연될 수 있습니다."
        ),
    },
    {
        "user": "상품을 받았는데 파손되어 있습니다.",
        "assistant": (
            "불편을 드려 죄송합니다. 파손된 상품과 포장 상태를 확인할 수 있는 사진을 준비한 뒤 "
            "주문번호와 함께 교환 또는 반품을 신청해 주세요. "
            "상품 확인 후 교환이나 환불 절차를 안내해 드리겠습니다."
        ),
    },
    {
        "user": "반품 배송비는 누가 부담하나요?",
        "assistant": (
            "단순 변심에 의한 반품은 일반적으로 고객이 반품 배송비를 부담합니다. "
            "상품 불량, 오배송 또는 파손과 같이 판매자 책임이 있는 경우에는 "
            "판매자가 반품 배송비를 부담합니다."
        ),
    },
    {
        "user": "환불은 언제 처리되나요?",
        "assistant": (
            "반품 상품이 판매자에게 도착하고 검수가 완료된 후 환불이 진행됩니다. "
            "카드 결제는 카드사에 따라 승인 취소 반영까지 추가로 3~7영업일이 걸릴 수 있습니다."
        ),
    },
    {
        "user": "주문번호를 모르는데 주문 조회가 가능한가요?",
        "assistant": (
            "회원 주문이라면 로그인 후 주문 내역에서 확인할 수 있습니다. "
            "비회원 주문이라면 주문자 이름, 연락처 또는 결제 정보를 이용해 조회할 수 있습니다."
        ),
    },
    {
        "user": "결제는 완료됐는데 주문 상태가 결제 대기로 나옵니다.",
        "assistant": (
            "결제 정보가 주문 시스템에 반영되는 데 일시적으로 시간이 걸릴 수 있습니다. "
            "잠시 후 주문 내역을 다시 확인해 주세요. "
            "계속 결제 대기로 표시된다면 주문번호와 결제 시간을 알려주세요."
        ),
    },
    {
        "user": "배송지를 잘못 입력했습니다.",
        "assistant": (
            "상품이 배송 준비 전이라면 주문 내역 또는 고객센터를 통해 배송지 변경을 요청할 수 있습니다. "
            "이미 출고된 경우에는 배송지 변경이 제한될 수 있으므로 빠르게 문의해 주세요."
        ),
    },
    {
        "user": "교환하고 싶은데 어떻게 해야 하나요?",
        "assistant": (
            "주문 내역에서 교환할 상품을 선택한 후 교환 사유와 원하는 옵션을 입력해 신청해 주세요. "
            "상품 상태 확인 후 회수 및 재배송 절차가 진행됩니다."
        ),
    },
    {
        "user": "회원 탈퇴 후 주문 내역도 삭제되나요?",
        "assistant": (
            "회원 탈퇴 후에도 전자상거래 관련 법령에 따라 거래 기록 일부는 일정 기간 보관될 수 있습니다. "
            "보관 기간이 종료되면 관련 정책에 따라 안전하게 삭제됩니다."
        ),
    },
    {
        "user": "쿠폰을 사용하지 못하고 결제했습니다.",
        "assistant": (
            "결제가 완료된 주문에는 일반적으로 쿠폰을 추가 적용할 수 없습니다. "
            "상품이 아직 배송 준비 전이라면 기존 주문을 취소한 뒤 쿠폰을 적용하여 다시 주문할 수 있습니다."
        ),
    },
    {
        "user": "품절된 상품은 언제 다시 입고되나요?",
        "assistant": (
            "재입고 일정은 상품과 공급 상황에 따라 달라집니다. "
            "상품 페이지에 재입고 알림 기능이 있다면 신청해 주세요. "
            "정확한 확인을 위해 상품명을 알려주시면 확인 방법을 안내해 드리겠습니다."
        ),
    },
    {
        "user": "다른 상품이 배송되었습니다.",
        "assistant": (
            "오배송으로 불편을 드려 죄송합니다. "
            "받으신 상품의 사진과 주문번호를 준비하여 교환 또는 반품을 신청해 주세요. "
            "확인 후 올바른 상품을 받을 수 있도록 안내해 드리겠습니다."
        ),
    },
    {
        "user": "현금영수증을 발급받고 싶습니다.",
        "assistant": (
            "현금 결제 과정에서 현금영수증 발급 정보를 입력할 수 있습니다. "
            "결제 후 발급이 필요한 경우 주문번호와 결제 정보를 확인한 뒤 고객센터에 요청해 주세요."
        ),
    },
    {
        "user": "고객센터 운영 시간이 궁금합니다.",
        "assistant": (
            "고객센터 운영 시간은 쇼핑몰 정책에 따라 다를 수 있습니다. "
            "사이트의 고객센터 또는 이용 안내 페이지에서 정확한 운영 시간을 확인해 주세요."
        ),
    },
    {
        "user": "상품 사용 후에도 반품할 수 있나요?",
        "assistant": (
            "상품을 사용하여 가치가 감소했거나 재판매가 어려운 상태라면 반품이 제한될 수 있습니다. "
            "다만 상품 자체의 하자가 확인되는 경우에는 별도 절차로 처리될 수 있습니다."
        ),
    },
    {
        "user": "배송 완료라고 나오는데 상품을 받지 못했습니다.",
        "assistant": (
            "먼저 가족, 경비실, 무인 택배함 또는 문 앞에 상품이 보관되었는지 확인해 주세요. "
            "상품이 확인되지 않으면 배송 조회에 표시된 택배사와 기사에게 문의한 뒤 "
            "주문번호를 고객센터에 알려주세요."
        ),
    },
    {
        "user": "결제 수단을 변경하고 싶습니다.",
        "assistant": (
            "결제가 완료된 주문의 결제 수단은 직접 변경하기 어렵습니다. "
            "배송 준비 전이라면 주문을 취소한 후 원하는 결제 수단으로 다시 주문해 주세요."
        ),
    },
    {
        "user": "부분 환불도 가능한가요?",
        "assistant": (
            "여러 상품을 함께 주문했다면 일부 상품만 선택하여 반품 및 환불을 신청할 수 있습니다. "
            "다만 할인이나 쿠폰 조건이 변경되면 최종 환불 금액이 달라질 수 있습니다."
        ),
    },
    {
        "user": "문의 글을 남겼는데 답변이 없습니다.",
        "assistant": (
            "문의량이 많으면 답변이 지연될 수 있습니다. "
            "문의 내역에서 접수 상태를 확인해 주세요. "
            "오랫동안 답변이 없다면 문의 날짜와 제목을 알려주시면 확인 방법을 안내해 드리겠습니다."
        ),
    },
]


def convert_to_messages(sample: dict) -> dict:
    """
    user와 assistant로 구성된 원본 샘플을
    Hugging Face 대화형 messages 형식으로 변환합니다.

    Args:
        sample: user와 assistant 키를 가진 원본 데이터입니다.

    Returns:
        system, user, assistant 메시지를 포함한 딕셔너리입니다.
    """

    # SFTTrainer가 인식할 수 있도록 messages 키를 사용합니다.
    return {
        "messages": [
            # system 메시지는 모델의 역할과 답변 원칙을 지정합니다.
            {
                "role": "system",
                "content": SYSTEM_PROMPT,
            },

            # user 메시지는 모델이 입력으로 받는 고객 질문입니다.
            {
                "role": "user",
                "content": sample["user"],
            },

            # assistant 메시지는 모델이 학습해야 하는 정답입니다.
            {
                "role": "assistant",
                "content": sample["assistant"],
            },
        ]
    }


def validate_sample(sample: dict) -> None:
    """
    한 개의 학습 데이터가 올바른 messages 구조인지 검사합니다.

    구조에 문제가 있으면 ValueError를 발생시켜
    잘못된 데이터가 학습에 사용되는 것을 방지합니다.
    """

    # 최상위 객체에 messages 키가 존재하는지 검사합니다.
    if "messages" not in sample:
        raise ValueError("데이터에 messages 키가 없습니다.")

    # messages 값이 리스트인지 검사합니다.
    if not isinstance(sample["messages"], list):
        raise ValueError("messages 값은 리스트여야 합니다.")

    # system, user, assistant 메시지 3개가 있는지 검사합니다.
    if len(sample["messages"]) != 3:
        raise ValueError("각 데이터는 system, user, assistant 메시지를 포함해야 합니다.")

    # 예상하는 역할 순서를 리스트로 정의합니다.
    expected_roles = ["system", "user", "assistant"]

    # 실제 메시지와 예상 역할을 한 개씩 비교합니다.
    for message, expected_role in zip(sample["messages"], expected_roles):

        # 각 메시지가 딕셔너리인지 검사합니다.
        if not isinstance(message, dict):
            raise ValueError("각 메시지는 딕셔너리여야 합니다.")

        # role 값이 예상 역할과 일치하는지 검사합니다.
        if message.get("role") != expected_role:
            raise ValueError(
                f"잘못된 역할 순서입니다. 예상={expected_role}, 실제={message.get('role')}"
            )

        # content 값이 비어 있지 않은 문자열인지 검사합니다.
        content = message.get("content")

        if not isinstance(content, str) or not content.strip():
            raise ValueError(f"{expected_role} 메시지의 content가 비어 있습니다.")


def save_jsonl(samples: list[dict], file_path: Path) -> None:
    """
    데이터 리스트를 JSON Lines 형식으로 저장합니다.

    JSON Lines는 한 줄에 JSON 객체 하나를 저장하는 형식으로,
    대규모 학습 데이터를 순차적으로 처리하기 편리합니다.
    """

    # UTF-8 인코딩으로 출력 파일을 엽니다.
    # ensure_ascii=False와 함께 사용하면 한글이 그대로 저장됩니다.
    with file_path.open("w", encoding="utf-8") as file:

        # 데이터 한 개씩 반복합니다.
        for sample in samples:

            # 파이썬 딕셔너리를 JSON 문자열로 변환합니다.
            json_line = json.dumps(
                sample,
                ensure_ascii=False,
            )

            # JSON 객체 하나를 한 줄에 기록합니다.
            file.write(json_line + "\n")


def main() -> None:
    """
    데이터 변환, 검증, 분할 및 저장을 수행하는 메인 함수입니다.
    """

    # data 디렉터리가 없으면 새로 생성합니다.
    # parents=True는 상위 디렉터리까지 생성합니다.
    # exist_ok=True는 이미 존재해도 오류를 발생시키지 않습니다.
    DATA_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    # 원본 데이터를 messages 형식으로 변환합니다.
    converted_samples = [
        convert_to_messages(sample)
        for sample in RAW_SAMPLES
    ]

    # 변환된 모든 데이터를 검사합니다.
    for sample in converted_samples:
        validate_sample(sample)

    # 동일한 데이터 분할 결과가 나오도록 Random 객체를 생성합니다.
    random_generator = random.Random(RANDOM_SEED)

    # 원본 목록을 변경하지 않도록 복사본을 만듭니다.
    shuffled_samples = converted_samples.copy()

    # 데이터 순서를 무작위로 섞습니다.
    random_generator.shuffle(shuffled_samples)

    # 전체 데이터의 80%를 학습 데이터로 사용합니다.
    split_index = int(len(shuffled_samples) * 0.8)

    # 앞부분을 학습 데이터로 분리합니다.
    train_samples = shuffled_samples[:split_index]

    # 뒷부분을 검증 데이터로 분리합니다.
    valid_samples = shuffled_samples[split_index:]

    # 학습 데이터를 train.jsonl로 저장합니다.
    save_jsonl(
        train_samples,
        TRAIN_FILE,
    )

    # 검증 데이터를 valid.jsonl로 저장합니다.
    save_jsonl(
        valid_samples,
        VALID_FILE,
    )

    # 생성 결과를 화면에 출력합니다.
    print("=" * 70)
    print("SFT 데이터셋 생성 완료")
    print("=" * 70)
    print(f"전체 데이터 수 : {len(shuffled_samples)}")
    print(f"학습 데이터 수 : {len(train_samples)}")
    print(f"검증 데이터 수 : {len(valid_samples)}")
    print(f"학습 파일      : {TRAIN_FILE}")
    print(f"검증 파일      : {VALID_FILE}")


# 이 파일을 직접 실행한 경우에만 main 함수를 호출합니다.
if __name__ == "__main__":
    main()
