# FastAPI 웹 서버를 만들기 위해 FastAPI 클래스를 불러옵니다.
from fastapi import FastAPI, Request
# 정적 파일 경로를 연결하기 위해 StaticFiles를 불러옵니다.
from fastapi.staticfiles import StaticFiles
# HTML 템플릿을 렌더링하기 위해 Jinja2Templates를 불러옵니다.
from fastapi.templating import Jinja2Templates
# JSON 응답을 명확하게 반환하기 위해 JSONResponse를 불러옵니다.
from fastapi.responses import JSONResponse
# 경로 처리를 위해 Path를 불러옵니다.
from pathlib import Path

# 요청 데이터 구조를 불러옵니다.
from app.schemas import ChatRequest, CartAddRequest
# 메뉴 데이터와 주문 처리 함수를 불러옵니다.
from app.menu_data import COFFEE_MENU, TASTE_KEYWORDS
from app.order_service import CART, add_to_cart, cart_total, clear_cart, extract_quantity, extract_temperature, find_menus
# PyTorch 의도 분류 함수를 불러옵니다.
from app.torch_model import predict_intent
# OpenAI 응답 생성 함수를 불러옵니다.
from app.openai_service import generate_chat_answer, is_openai_ready

# DB 테이블 자동 생성을 위해 Base와 엔진, 세션 팩토리를 불러옵니다.
from app.database import Base, engine, SessionLocal
# 테이블 자동 생성 전에 모든 ORM 모델을 Base에 등록하기 위해 임포트합니다.
import app.models  # noqa: F401
# 회원가입/로그인, 메뉴, 주문, 결제 라우터를 불러옵니다.
from app.routers import auth, menus, orders, payments
# 최초 실행 시 기본 메뉴를 DB에 채워 넣기 위해 메뉴 서비스를 불러옵니다.
from app.services import menu_service

# 현재 파일 기준으로 app 디렉터리 경로를 계산합니다.
BASE_DIR = Path(__file__).resolve().parent

# 개발/실습 편의를 위해 앱 시작 시 ORM 모델 기준으로 테이블을 자동 생성합니다.
# 운영 환경에서는 Alembic 같은 마이그레이션 도구 사용을 권장합니다.
Base.metadata.create_all(bind=engine)  # users, menus, orders, order_items, payments 테이블을 자동 생성합니다.

# 메뉴 테이블이 비어 있으면 챗봇용 기본 커피 메뉴(COFFEE_MENU)를 DB에 등록합니다.
with SessionLocal() as _seed_db:  # 시딩 전용 임시 DB 세션을 엽니다.
    menu_service.seed_menus(_seed_db, COFFEE_MENU)  # 최초 1회 기본 메뉴를 채워 넣습니다.

# FastAPI 애플리케이션 객체를 생성합니다.
app = FastAPI(title="Coffee Order AI Chatbot", description="FastAPI + OpenAI + PyTorch 커피 주문 챗봇", version="2.0.0")

# 회원 인증/메뉴/주문/결제 API 라우터를 앱에 등록합니다. (DB 저장 기능)
app.include_router(auth.router)  # /auth 경로의 회원가입·로그인 API입니다.
app.include_router(menus.router)  # /menus 경로의 메뉴 CRUD API입니다.
app.include_router(orders.router)  # /orders 경로의 주문 API입니다.
app.include_router(payments.router)  # /payments 경로의 결제 API입니다.

# CSS, JS 같은 정적 파일 경로를 /static URL에 연결합니다.
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")

# HTML 템플릿 폴더를 설정합니다.
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))


# 루트 페이지를 렌더링하는 엔드포인트입니다.
@app.get("/")
def home(request: Request):
    # index.html 템플릿에 요청 객체와 제목을 전달하여 화면을 반환합니다.
    return templates.TemplateResponse("index.html", {"request": request, "app_title": "Coffee Order AI"})


# 서버 상태와 OpenAI 키 설정 상태를 확인하는 엔드포인트입니다.
@app.get("/api/health")
def health():
    # 서버 상태와 OpenAI 준비 여부를 JSON으로 반환합니다.
    return {"status": "ok", "openai_ready": is_openai_ready()}


# 전체 메뉴 목록을 반환하는 엔드포인트입니다.
@app.get("/api/menu")
def menu():
    # 커피 메뉴와 맛 키워드를 함께 반환합니다.
    return {"menus": COFFEE_MENU, "taste_keywords": TASTE_KEYWORDS}


# 챗봇 대화 처리 엔드포인트입니다.
@app.post("/api/chat")
def chat(request_data: ChatRequest):
    # 사용자 메시지를 변수에 저장합니다.
    message = request_data.message
    # PyTorch 모델로 사용자 의도를 예측합니다.
    intent, confidence = predict_intent(message)
    # 사용자 메시지에 맞는 메뉴를 검색합니다.
    recommendations = find_menus(message, top_k=request_data.top_k)
    # 사용자의 메시지에서 온도 옵션을 추출합니다.
    temperature = extract_temperature(message)
    # 사용자의 메시지에서 수량을 추출합니다.
    quantity = extract_quantity(message)
    # OpenAI에 전달할 시스템 분석 내용을 만듭니다.
    system_context = (
        f"예측 의도: {intent}\n"
        f"신뢰도: {confidence:.2f}\n"
        f"추천 메뉴: {', '.join(menu['name'] for menu in recommendations)}\n"
        f"온도 옵션: {temperature}\n"
        f"수량: {quantity}\n"
        f"장바구니 합계: {cart_total()}원"
    )
    # OpenAI 또는 로컬 fallback으로 자연어 답변을 생성합니다.
    ai_message = generate_chat_answer(message, system_context)
    # 주문 의도이고 추천 메뉴가 있으면 첫 번째 메뉴를 장바구니에 담을 수 있도록 안내합니다.
    if intent == "order" and recommendations:
        ai_message += f"\n\n'{recommendations[0]['name']}' 메뉴를 장바구니에 담으려면 추천 카드의 담기 버튼을 눌러주세요."
    # 프론트엔드에서 사용할 JSON 응답을 반환합니다.
    return {
        "message": ai_message,
        "intent": intent,
        "confidence": round(confidence, 3),
        "recommendations": recommendations,
        "temperature": temperature,
        "quantity": quantity,
        "cart": CART,
        "total": cart_total(),
    }


# 추천 카드에서 장바구니에 메뉴를 담는 엔드포인트입니다.
@app.post("/api/cart/add")
def cart_add(request_data: CartAddRequest):
    # 전달받은 메뉴 정보를 장바구니에 추가합니다.
    result = add_to_cart(request_data.menu_id, request_data.temperature, request_data.quantity, request_data.option_note)
    # 처리 결과를 JSON으로 반환합니다.
    return JSONResponse(result)


# 현재 장바구니를 조회하는 엔드포인트입니다.
@app.get("/api/cart")
def cart_get():
    # 장바구니 목록과 총액을 반환합니다.
    return {"cart": CART, "total": cart_total()}


# 장바구니를 초기화하는 엔드포인트입니다.
@app.post("/api/cart/clear")
def cart_clear():
    # 장바구니 항목을 모두 삭제합니다.
    clear_cart()
    # 초기화 완료 메시지를 반환합니다.
    return {"ok": True, "cart": CART, "total": cart_total()}


# 데모 결제 페이지 이동 전 주문 요약을 반환하는 엔드포인트입니다.
@app.post("/api/checkout")
def checkout():
    # 장바구니가 비어 있으면 결제할 수 없다는 메시지를 반환합니다.
    if not CART:
        return {"ok": False, "message": "장바구니가 비어 있습니다."}
    # 실제 결제가 아닌 데모 결제 안내를 반환합니다.
    return {"ok": True, "message": "데모 결제 페이지로 이동할 수 있습니다.", "cart": CART, "total": cart_total()}
