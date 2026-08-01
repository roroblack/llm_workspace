[멀티 에이전트 실습문제와 해답]

문제 1 — 경쟁사 분석가 에이전트 추가 (3-way 라우팅)
code/agent.py를 복사해 code/ex_three.py를 만드세요. 
@tool search_competitor()로 data/competitor_data.csv를 조회하는 competitor_agent를 추가하고, 
route_rule/route_llm이 "sales"/"policy"/"competitor" 3개를 반환하도록 확장하세요. 
supervisor()도 3개 에이전트 중 알맞은 것에 위임하게 고치세요.

기대 결과: "경쟁사랑 비교하면 어때?" 입력 시 [Supervisor] ... 
→ competitor 로그가 찍히고 경쟁사 데이터 기반 답이 나온다.

[해답 보기] ===============================================
# -*- coding: utf-8 -*-
# 실행: python code/ch25_ex_three.py
import sys, pathlib
sys.path.append(str(pathlib.Path(__file__).resolve().parent))
from common import get_chat, DATA
import pandas as pd
from langchain_core.tools import tool
from langchain.agents import create_agent
from ch25_multi_agent import search_products, search_faq, POLICY_WORDS   # 기존 재사용

competitor = pd.read_csv(DATA / "competitor_data.csv")   # company,main_category,rating,strength,weakness
COMPETITOR_WORDS = ["경쟁사", "경쟁", "비교", "타사", "다른 쇼핑몰", "라이벌"]

@tool
def search_competitor(keyword: str) -> str:
    """키워드로 경쟁사 데이터(강점·약점·평점)를 조회한다."""
    hit = competitor[competitor.apply(
        lambda r: keyword in str(r["company"]) or keyword in str(r["main_category"]), axis=1)]
    if hit.empty:
        hit = competitor   # 못 찾으면 전체 요약
    return "\n".join(
        f"- {r.company}({r.main_category}, 평점 {r.rating}): 강점 {r.strength} / 약점 {r.weakness}"
        for r in hit.head(3).itertuples())

def build_three_agents():
    llm = get_chat(temperature=0)
    sales = create_agent(llm, tools=[search_products],
        system_prompt="너는 '상품 추천' 전문 상담원이다.")
    policy = create_agent(llm, tools=[search_faq],
        system_prompt="너는 '정책/FAQ 안내' 전문 상담원이다. FAQ 근거로만 답하라.")
    comp = create_agent(llm, tools=[search_competitor],
        system_prompt="너는 '경쟁사 분석' 전문가다. 경쟁사 데이터 근거로 비교 분석하라.")
    return llm, sales, policy, comp

def route_rule3(question: str) -> str:
    """3-way 규칙 라우터: competitor → policy → sales(기본) 순 우선순위."""
    if any(w in question for w in COMPETITOR_WORDS):
        return "competitor"
    if any(w in question for w in POLICY_WORDS):
        return "policy"
    return "sales"

def route_llm3(llm, question: str) -> str:
    msg = ("다음 질문을 한 단어로 분류: 경쟁사 비교면 'competitor', "
           "환불/배송 등 정책이면 'policy', 상품 추천이면 'sales'.\n"
           f"질문: {question}\n분류:")
    ans = llm.invoke(msg).content.strip().lower()
    for t in ("competitor", "policy", "sales"):
        if t in ans:
            return t
    return "sales"

def supervisor3(llm, agents, question, use_llm=False):
    target = route_llm3(llm, question) if use_llm else route_rule3(question)
    print(f"  [Supervisor] '{question}' → {target} 에이전트로 라우팅")
    agent = agents[target]
    return agent.invoke({"messages": [{"role": "user", "content": question}]})["messages"][-1].content

if __name__ == "__main__":
    llm, sales, policy, comp = build_three_agents()
    agents = {"sales": sales, "policy": policy, "competitor": comp}
    for q in ["전자기기 추천해줘", "환불 며칠 이내?", "경쟁사랑 비교하면 어때?"]:
        print("=" * 60)
        print("고객:", q)
        print("답변:", supervisor3(llm, agents, q)[:150])
# ==========================================================        
**예상 출력**
============================================================
고객: 경쟁사랑 비교하면 어때?
  [Supervisor] '경쟁사랑 비교하면 어때?' → competitor 에이전트로 라우팅
답변: 경쟁사 비교 분석입니다.
- A몰(전자기기, 평점 4.5): 강점 빠른배송 / 약점 높은가격 ...

**해설**: 핵심은 **라우팅을 3-way로 확장**할 때 **우선순위**입니다.
`route_rule3`에서 competitor → policy → sales 순으로 확인하죠. 
"경쟁사 환불 비교"처럼 두 키워드가 겹칠 때, 먼저 확인하는 쪽이 이깁니다. 
`agents` dict로 라우팅 결과를 바로 매핑하면(`agents[target]`) if-elif 없이 깔끔하죠. 
에이전트를 추가해도 dict에 한 줄만 넣으면 됩니다 — 확장에 유리한 구조입니다.



문제 2 — 라우팅 정확도 테스트 작성
code/ch25_ex_test.py를 만들어, 위 3-way route_rule에 (질문, 기대route) 쌍 6개(각 에이전트당 2개)를 넣고
실제 결과와 비교해 정확도를 출력하는 평가 스크립트를 작성하세요.

검증: 실행 시 "정확도: N/6"이 출력되고, 오분류된 질문이 있으면 함께 표시.

[해답 보기] ===================================================
# -*- coding: utf-8 -*-
# 실행: python code/ch25_ex_test.py
import sys, pathlib
sys.path.append(str(pathlib.Path(__file__).resolve().parent))
from ch25_ex_three import route_rule3      # 문제 1의 3-way 규칙 라우터 재사용

# (질문, 기대 route) — 각 에이전트당 2개씩 6개
TESTSET = [
    ("전자기기 추천해줘", "sales"),
    ("선물용 좋은 거 골라줘", "sales"),
    ("환불 며칠 이내에 해야 해?", "policy"),
    ("무료배송 기준이 뭐야?", "policy"),
    ("경쟁사랑 비교해줘", "competitor"),
    ("타사 대비 우리 강점이 뭐야?", "competitor"),
]

def evaluate():
    correct = 0
    wrong = []
    for q, gold in TESTSET:
        pred = route_rule3(q)
        if pred == gold:
            correct += 1
        else:
            wrong.append((q, gold, pred))
    n = len(TESTSET)
    print(f"정확도: {correct}/{n} ({correct/n*100:.0f}%)")
    if wrong:
        print("\n[오분류]")
        for q, gold, pred in wrong:
            print(f"  '{q}' → 기대 {gold}, 실제 {pred}")
    else:
        print("모두 정확히 분류됨 ✅")

if __name__ == "__main__":
    evaluate()
# =============================================================    
**예상 출력**
정확도: 6/6 (100%)
모두 정확히 분류됨 ✅
또는 오분류가 있다면:
정확도: 5/6 (83%)

[오분류]
  '타사 대비 우리 강점이 뭐야?' → 기대 competitor, 실제 sales

**해설**: 핵심은 **테스트셋을 균형 있게**(각 에이전트당 2개) 구성하는 것입니다. 
한 카테고리만 많으면 정확도가 왜곡되죠. 
오분류를 `wrong` 리스트에 모아 **무엇을 왜 틀렸는지** 보여 주면, 
키워드 목록을 어떻게 개선할지 알 수 있습니다(예: '타사'가 `COMPETITOR_WORDS`에 없으면 추가).
06번에서 본 "정답 라벨 + 정확도 측정"을 직접 구현한 거죠 
— 이런 테스트가 있으면 라우터를 고칠 때마다 회귀(regression)를 잡을 수 있습니다.



 