"""
임의 코드 실행 대신 산술 표현식만 허용하는 안전한 Python Tool입니다.
"""

# Python 표현식을 구문 트리로 분석하기 위해 ast를 가져옵니다.
import ast

# 허용할 연산 함수를 사용하기 위해 operator를 가져옵니다.
import operator


# 안전한 Python 계산 어댑터를 정의합니다.
class PythonSandboxAdapter:
    """파일·네트워크·import 없이 숫자 계산만 수행합니다."""

    # 허용할 이항 연산 노드와 실제 함수를 연결합니다.
    BINARY_OPERATORS = {
        ast.Add: operator.add,
        ast.Sub: operator.sub,
        ast.Mult: operator.mul,
        ast.Div: operator.truediv,
        ast.FloorDiv: operator.floordiv,
        ast.Mod: operator.mod,
        ast.Pow: operator.pow,
    }

    # 허용할 단항 연산 노드와 실제 함수를 연결합니다.
    UNARY_OPERATORS = {
        ast.UAdd: operator.pos,
        ast.USub: operator.neg,
    }

    # 산술 표현식을 계산합니다.
    def evaluate(self, expression: str) -> dict:
        """허용된 숫자 연산만 계산하여 반환합니다."""

        # 지나치게 긴 입력을 차단합니다.
        if len(expression) > 200:
            raise ValueError("표현식은 200자 이하만 허용합니다.")

        # eval 모드로 표현식을 AST로 변환합니다.
        tree = ast.parse(expression, mode="eval")

        # AST를 재귀적으로 안전하게 계산합니다.
        result = self._evaluate_node(tree.body)

        # 입력과 계산 결과를 반환합니다.
        return {"expression": expression, "result": result}

    # AST 노드를 재귀적으로 평가합니다.
    def _evaluate_node(self, node):
        """허용된 AST 노드만 처리합니다."""

        # 정수 또는 실수 상수를 허용합니다.
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
            return node.value

        # 허용된 이항 연산을 처리합니다.
        if isinstance(node, ast.BinOp) and type(node.op) in self.BINARY_OPERATORS:
            # 왼쪽 값을 계산합니다.
            left = self._evaluate_node(node.left)

            # 오른쪽 값을 계산합니다.
            right = self._evaluate_node(node.right)

            # 지수 연산의 비정상적인 크기를 제한합니다.
            if isinstance(node.op, ast.Pow) and abs(right) > 10:
                raise ValueError("지수의 절댓값은 10 이하만 허용합니다.")

            # 연결된 연산 함수를 호출합니다.
            return self.BINARY_OPERATORS[type(node.op)](left, right)

        # 허용된 단항 연산을 처리합니다.
        if isinstance(node, ast.UnaryOp) and type(node.op) in self.UNARY_OPERATORS:
            # 피연산자를 계산한 뒤 단항 연산을 적용합니다.
            return self.UNARY_OPERATORS[type(node.op)](self._evaluate_node(node.operand))

        # 그 밖의 노드는 모두 차단합니다.
        raise ValueError("숫자와 +, -, *, /, //, %, **, 괄호만 사용할 수 있습니다.")
