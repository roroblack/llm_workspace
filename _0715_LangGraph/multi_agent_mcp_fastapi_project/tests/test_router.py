from app.services.router_service import route_rule

def test_policy_route():
    assert route_rule("환불은 며칠 안에 가능한가요?") == "policy"

def test_sales_route():
    assert route_rule("전자기기 추천해 주세요") == "sales"
