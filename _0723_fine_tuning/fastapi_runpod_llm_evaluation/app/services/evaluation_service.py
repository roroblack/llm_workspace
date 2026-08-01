"""
모델 예측 생성과 자동 평가 지표 계산을 담당합니다.
"""

# JSON 및 JSONL 파일을 처리하기 위해 json을 가져옵니다.
import json

# 응답 시간의 평균과 중앙값을 계산하기 위해 통계 함수를 가져옵니다.
from statistics import mean, median

# 파일 경로를 처리하기 위해 Path를 가져옵니다.
from pathlib import Path

# 여러 형태의 딕셔너리 값을 표현하기 위해 Any를 가져옵니다.
from typing import Any

# ROUGE 점수를 계산하기 위한 클래스를 가져옵니다.
from rouge_score import rouge_scorer

# 애플리케이션 설정을 가져옵니다.
from app.core.config import Settings, get_settings

# 추론 요청 스키마와 모델 구분 자료형을 가져옵니다.
from app.models.schemas import GenerationRequest, ModelKind

# 실제 답변 생성 서비스를 가져옵니다.
from app.services.inference_service import InferenceService, inference_service


class EvaluationService:
    """
    평가 데이터 로드, 예측 생성, 지표 계산과 저장을 수행합니다.
    """

    def __init__(
        self,
        settings: Settings | None = None,
        inference: InferenceService | None = None,
    ) -> None:
        """
        설정과 추론 서비스 의존성을 초기화합니다.
        """

        # 전달된 설정이 없으면 전역 설정 객체를 사용합니다.
        self.settings = settings or get_settings()

        # 전달된 추론 서비스가 없으면 애플리케이션 공용 객체를 사용합니다.
        self.inference = inference or inference_service

    @staticmethod
    def _normalize_text(text: str) -> str:
        """
        Exact Match 계산을 위해 공백과 대소문자를 정규화합니다.
        """

        # 줄바꿈과 연속 공백을 하나의 공백으로 합치고 소문자로 변환합니다.
        return " ".join(text.strip().lower().split())

    @staticmethod
    def _is_valid_json(text: str) -> bool:
        """
        문자열이 올바른 JSON이면 True를 반환합니다.
        """

        try:
            # 모델 답변 문자열을 JSON으로 파싱합니다.
            json.loads(text)

            # 오류가 없으면 올바른 JSON 형식입니다.
            return True
        except json.JSONDecodeError:
            # JSON 문법 오류가 발생하면 False를 반환합니다.
            return False

    def load_evaluation_rows(
        self,
        file_path: Path | None = None,
        limit: int | None = None,
    ) -> list[dict[str, Any]]:
        """
        평가 JSONL 파일을 읽고 필요한 개수만 반환합니다.
        """

        # 별도 파일이 없으면 설정의 기본 평가 파일을 사용합니다.
        source_path = file_path or self.settings.evaluation_path

        # 파일이 존재하지 않으면 명확한 오류를 발생시킵니다.
        if not source_path.exists():
            raise FileNotFoundError(f"평가 파일이 없습니다: {source_path}")

        # 읽은 평가 데이터를 저장할 리스트입니다.
        rows: list[dict[str, Any]] = []

        # UTF-8 인코딩으로 JSONL 파일을 엽니다.
        with source_path.open("r", encoding="utf-8") as file:
            # 줄 번호와 함께 한 줄씩 읽습니다.
            for line_number, line in enumerate(file, start=1):
                # 빈 줄은 건너뜁니다.
                if not line.strip():
                    continue

                try:
                    # JSON 문자열을 파이썬 딕셔너리로 변환합니다.
                    row = json.loads(line)
                except json.JSONDecodeError as error:
                    # 오류가 발생한 줄 번호를 포함해 예외를 발생시킵니다.
                    raise ValueError(
                        f"{source_path}의 {line_number}번째 줄 JSON이 잘못되었습니다."
                    ) from error

                # 평가에 필수인 prompt와 reference가 있는지 검사합니다.
                if "prompt" not in row or "reference" not in row:
                    raise ValueError(
                        f"{line_number}번째 데이터에 prompt 또는 reference가 없습니다."
                    )

                # 정상 데이터를 결과 목록에 추가합니다.
                rows.append(row)

                # limit에 도달하면 더 이상 파일을 읽지 않습니다.
                if limit is not None and len(rows) >= limit:
                    break

        # 평가 데이터가 하나도 없으면 오류를 발생시킵니다.
        if not rows:
            raise ValueError("평가 데이터가 비어 있습니다.")

        # 검증된 평가 데이터 목록을 반환합니다.
        return rows

    def generate_predictions(
        self,
        model_kind: ModelKind,
        rows: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """
        평가 질문 각각에 대해 모델 답변과 성능 정보를 생성합니다.
        """

        # 전체 예측 결과를 저장할 리스트입니다.
        predictions: list[dict[str, Any]] = []

        # 평가 질문을 하나씩 반복합니다.
        for index, row in enumerate(rows, start=1):
            # 단일 질문 추론 요청 객체를 생성합니다.
            generation_request = GenerationRequest(
                model_kind=model_kind,
                prompt=str(row["prompt"]),
                max_new_tokens=self.settings.max_new_tokens,
                do_sample=False,
            )

            # 실제 또는 mock 추론을 실행합니다.
            response = self.inference.generate(generation_request)

            # 평가 데이터와 생성 결과를 하나의 레코드로 결합합니다.
            predictions.append(
                {
                    "id": str(row.get("id", f"eval-{index:04d}")),
                    "category": str(row.get("category", "unknown")),
                    "model_kind": model_kind,
                    "prompt": str(row["prompt"]),
                    "reference": str(row["reference"]),
                    "prediction": response.answer,
                    "latency_seconds": response.latency_seconds,
                    "input_tokens": response.input_tokens,
                    "output_tokens": response.output_tokens,
                    "tokens_per_second": response.tokens_per_second,
                }
            )

        # 전체 예측 결과를 반환합니다.
        return predictions

    def calculate_metrics(
        self,
        predictions: list[dict[str, Any]],
        use_bertscore: bool = False,
    ) -> dict[str, Any]:
        """
        Exact Match, ROUGE, JSON 준수율, 성능 지표를 계산합니다.
        """

        # 예측 데이터가 없으면 평균 계산을 할 수 없으므로 오류를 발생시킵니다.
        if not predictions:
            raise ValueError("평가할 예측 결과가 없습니다.")

        # ROUGE-1, ROUGE-2, ROUGE-L 계산기를 생성합니다.
        scorer = rouge_scorer.RougeScorer(
            ["rouge1", "rouge2", "rougeL"],
            use_stemmer=False,
        )

        # 각 데이터의 상세 결과를 저장할 리스트입니다.
        details: list[dict[str, Any]] = []

        # JSON 형식 평가 대상 데이터 수를 초기화합니다.
        json_target_count = 0

        # 유효한 JSON 답변 수를 초기화합니다.
        json_valid_count = 0

        # 개별 예측 결과를 반복합니다.
        for prediction in predictions:
            # 기준 답변을 문자열로 읽습니다.
            reference = str(prediction["reference"])

            # 모델 답변을 문자열로 읽습니다.
            answer = str(prediction["prediction"])

            # 기준 답변과 모델 답변 사이의 ROUGE 점수를 계산합니다.
            rouge_scores = scorer.score(reference, answer)

            # 정규화 후 완전히 일치하면 1, 아니면 0으로 기록합니다.
            exact_match = int(
                self._normalize_text(reference) == self._normalize_text(answer)
            )

            # category가 format이거나 기준 답변이 JSON이면 JSON 평가 대상으로 간주합니다.
            is_json_target = (
                prediction.get("category") == "format"
                or self._is_valid_json(reference)
            )

            # JSON 평가 대상이면 전체 수를 증가시킵니다.
            if is_json_target:
                json_target_count += 1

                # 모델 답변도 올바른 JSON이면 성공 수를 증가시킵니다.
                if self._is_valid_json(answer):
                    json_valid_count += 1

            # 현재 데이터의 평가 결과를 저장합니다.
            details.append(
                {
                    "id": prediction["id"],
                    "category": prediction["category"],
                    "exact_match": exact_match,
                    "rouge1_f1": rouge_scores["rouge1"].fmeasure,
                    "rouge2_f1": rouge_scores["rouge2"].fmeasure,
                    "rougeL_f1": rouge_scores["rougeL"].fmeasure,
                    "latency_seconds": float(prediction["latency_seconds"]),
                    "tokens_per_second": float(prediction["tokens_per_second"]),
                }
            )

        # 선택적으로 BERTScore를 계산합니다.
        if use_bertscore:
            try:
                # BERTScore 패키지의 계산 함수를 가져옵니다.
                from bert_score import score as bert_score

                # GPU 사용 가능 여부 확인을 위해 torch를 가져옵니다.
                import torch
            except ImportError as error:
                # 선택 기능에 필요한 패키지가 없음을 설명합니다.
                raise RuntimeError(
                    "BERTScore를 사용하려면 requirements-runpod.txt를 설치하세요."
                ) from error

            # 모든 모델 답변 문자열을 목록으로 만듭니다.
            candidate_texts = [
                str(item["prediction"])
                for item in predictions
            ]

            # 모든 기준 답변 문자열을 목록으로 만듭니다.
            reference_texts = [
                str(item["reference"])
                for item in predictions
            ]

            # 다국어 BERT 모델을 이용해 의미 유사도를 계산합니다.
            _, _, bert_f1 = bert_score(
                cands=candidate_texts,
                refs=reference_texts,
                model_type="bert-base-multilingual-cased",
                device="cuda" if torch.cuda.is_available() else "cpu",
                verbose=False,
            )

            # 각 상세 결과에 BERTScore F1 값을 추가합니다.
            for index, result in enumerate(details):
                result["bertscore_f1"] = float(bert_f1[index])

        # 모든 응답 시간을 목록으로 추출합니다.
        latency_values = [
            float(item["latency_seconds"])
            for item in predictions
        ]

        # 모든 초당 생성 토큰 값을 목록으로 추출합니다.
        throughput_values = [
            float(item["tokens_per_second"])
            for item in predictions
        ]

        # 전체 평균 평가 지표를 구성합니다.
        summary: dict[str, Any] = {
            "model_kind": predictions[0]["model_kind"],
            "sample_count": len(predictions),
            "exact_match": mean(item["exact_match"] for item in details),
            "rouge1_f1": mean(item["rouge1_f1"] for item in details),
            "rouge2_f1": mean(item["rouge2_f1"] for item in details),
            "rougeL_f1": mean(item["rougeL_f1"] for item in details),
            "json_target_count": json_target_count,
            "json_compliance_rate": (
                json_valid_count / json_target_count
                if json_target_count > 0
                else None
            ),
            "average_latency_seconds": mean(latency_values),
            "median_latency_seconds": median(latency_values),
            "average_tokens_per_second": mean(throughput_values),
        }

        # BERTScore를 계산한 경우 전체 평균도 추가합니다.
        if use_bertscore:
            summary["bertscore_f1"] = mean(
                item["bertscore_f1"]
                for item in details
            )

        # 카테고리 이름을 중복 없이 정렬합니다.
        categories = sorted(
            {str(item["category"]) for item in details}
        )

        # 카테고리별 평균 결과를 저장할 딕셔너리입니다.
        category_summary: dict[str, Any] = {}

        # 각 카테고리의 평균을 계산합니다.
        for category in categories:
            # 현재 카테고리에 해당하는 상세 결과만 선택합니다.
            category_rows = [
                item for item in details
                if item["category"] == category
            ]

            # 핵심 품질 지표를 카테고리별로 저장합니다.
            category_summary[category] = {
                "sample_count": len(category_rows),
                "exact_match": mean(
                    item["exact_match"] for item in category_rows
                ),
                "rougeL_f1": mean(
                    item["rougeL_f1"] for item in category_rows
                ),
            }

            # BERTScore가 있으면 카테고리별 평균도 추가합니다.
            if use_bertscore:
                category_summary[category]["bertscore_f1"] = mean(
                    item["bertscore_f1"] for item in category_rows
                )

        # 전체 결과를 반환합니다.
        return {
            "summary": summary,
            "category_summary": category_summary,
            "details": details,
        }

    def save_jsonl(
        self,
        rows: list[dict[str, Any]],
        file_path: Path,
    ) -> None:
        """
        딕셔너리 목록을 UTF-8 JSONL 파일로 저장합니다.
        """

        # 저장 대상 디렉터리가 없으면 생성합니다.
        file_path.parent.mkdir(parents=True, exist_ok=True)

        # UTF-8 쓰기 모드로 파일을 엽니다.
        with file_path.open("w", encoding="utf-8") as file:
            # 데이터를 한 건씩 반복합니다.
            for row in rows:
                # 한글을 유지한 JSON 문자열을 한 줄씩 기록합니다.
                file.write(json.dumps(row, ensure_ascii=False) + "\n")

    def save_json(
        self,
        data: dict[str, Any],
        file_path: Path,
    ) -> None:
        """
        딕셔너리를 보기 좋은 JSON 파일로 저장합니다.
        """

        # 상위 디렉터리를 생성합니다.
        file_path.parent.mkdir(parents=True, exist_ok=True)

        # UTF-8 쓰기 모드로 파일을 엽니다.
        with file_path.open("w", encoding="utf-8") as file:
            # 들여쓰기와 한글 유지를 적용하여 저장합니다.
            json.dump(data, file, ensure_ascii=False, indent=2)

    def run(
        self,
        model_kind: ModelKind,
        use_bertscore: bool = False,
        limit: int | None = None,
    ) -> dict[str, Any]:
        """
        평가 데이터 로드부터 예측, 지표 계산, 파일 저장까지 실행합니다.
        """

        # 평가 데이터를 읽습니다.
        rows = self.load_evaluation_rows(limit=limit)

        # 선택한 모델의 예측을 생성합니다.
        predictions = self.generate_predictions(model_kind, rows)

        # 예측 결과에 대한 자동 평가 지표를 계산합니다.
        metrics = self.calculate_metrics(
            predictions,
            use_bertscore=use_bertscore,
        )

        # 결과 디렉터리를 생성합니다.
        self.settings.output_path.mkdir(parents=True, exist_ok=True)

        # 모델별 예측 결과 파일 경로를 구성합니다.
        prediction_path = (
            self.settings.output_path
            / f"{model_kind}_predictions.jsonl"
        )

        # 모델별 지표 결과 파일 경로를 구성합니다.
        metrics_path = (
            self.settings.output_path
            / f"{model_kind}_metrics.json"
        )

        # 예측 결과를 저장합니다.
        self.save_jsonl(predictions, prediction_path)

        # 평가 지표를 저장합니다.
        self.save_json(metrics, metrics_path)

        # API 응답에 저장 경로를 추가합니다.
        return {
            **metrics,
            "prediction_file": str(prediction_path),
            "metrics_file": str(metrics_path),
        }

    def compare(
        self,
        use_bertscore: bool = False,
        limit: int | None = None,
    ) -> dict[str, Any]:
        """
        동일한 데이터로 Base와 Fine-tuned 모델을 순서대로 평가합니다.
        """

        # Base 모델 평가를 실행합니다.
        base_result = self.run(
            "base",
            use_bertscore=use_bertscore,
            limit=limit,
        )

        # Fine-tuned 모델 평가를 실행합니다.
        fine_tuned_result = self.run(
            "fine_tuned",
            use_bertscore=use_bertscore,
            limit=limit,
        )

        # 두 모델에서 공통으로 비교할 핵심 지표를 정의합니다.
        metric_names = [
            "exact_match",
            "rouge1_f1",
            "rouge2_f1",
            "rougeL_f1",
            "json_compliance_rate",
            "average_latency_seconds",
            "average_tokens_per_second",
        ]

        # BERTScore를 사용했다면 비교 지표에 추가합니다.
        if use_bertscore:
            metric_names.append("bertscore_f1")

        # 각 지표의 Base, Fine-tuned, 변화량을 저장합니다.
        comparison: dict[str, Any] = {}

        # 지표 이름을 하나씩 반복합니다.
        for metric_name in metric_names:
            # Base 모델 값을 가져옵니다.
            base_value = base_result["summary"].get(metric_name)

            # Fine-tuned 모델 값을 가져옵니다.
            fine_value = fine_tuned_result["summary"].get(metric_name)

            # 둘 중 하나가 None이면 변화량 계산을 생략합니다.
            if base_value is None or fine_value is None:
                delta = None
            else:
                # 품질과 처리량 지표는 양수 변화가 개선입니다.
                if metric_name != "average_latency_seconds":
                    delta = float(fine_value) - float(base_value)
                else:
                    # 지연 시간은 감소가 개선이므로 Base에서 Fine-tuned를 뺍니다.
                    delta = float(base_value) - float(fine_value)

            # 현재 지표의 비교 결과를 저장합니다.
            comparison[metric_name] = {
                "base": base_value,
                "fine_tuned": fine_value,
                "improvement_delta": delta,
            }

        # 최종 비교 결과를 구성합니다.
        result = {
            "base": base_result["summary"],
            "fine_tuned": fine_tuned_result["summary"],
            "comparison": comparison,
        }

        # 비교 결과를 JSON 파일로 저장합니다.
        comparison_path = self.settings.output_path / "comparison.json"
        self.save_json(result, comparison_path)

        # 저장 경로를 포함한 최종 결과를 반환합니다.
        return {
            **result,
            "comparison_file": str(comparison_path),
        }


# 애플리케이션에서 공용으로 사용할 평가 서비스 객체를 생성합니다.
evaluation_service = EvaluationService()
