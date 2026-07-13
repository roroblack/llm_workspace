import json
from pathlib import Path

import torch


class MusicRecommender:
    """
    PyTorch Tensor 기반 음악 추천 클래스입니다.

    이 클래스는 사용자의 감정 문장과 음악 데이터의 감성 태그를
    같은 단어 사전 벡터로 변환한 뒤 Cosine Similarity로 유사도를 계산합니다.

    대규모 딥러닝 학습 모델은 아니지만,
    추천 시스템의 핵심 개념인 '사용자 입력과 콘텐츠 간 유사도 계산'을
    PyTorch로 직접 확인할 수 있도록 구성한 교육용 모델입니다.
    """

    def __init__(self, dataset_path: str | Path):
        """
        추천 모델 초기화 함수입니다.

        dataset_path:
            음악 추천 데이터가 들어 있는 JSON 파일 경로입니다.
        """

        # 문자열 경로를 Path 객체로 변환하여 파일 경로 처리를 안전하게 합니다.
        self.dataset_path = Path(dataset_path)

        # JSON 파일을 읽어 음악 데이터 리스트를 메모리에 저장합니다.
        self.songs = self._load_dataset()

        # 음악 데이터의 모든 tag 값을 모아 추천 모델에서 사용할 단어 사전을 만듭니다.
        self.vocabulary = self._build_vocabulary()

        # 각 음악 데이터를 PyTorch Tensor 벡터로 미리 변환합니다.
        self.song_vectors = self._build_song_vectors()

    def _load_dataset(self) -> list[dict]:
        """
        JSON 음악 데이터셋을 읽어 리스트로 반환합니다.
        """

        # UTF-8 인코딩으로 JSON 파일을 엽니다.
        with self.dataset_path.open("r", encoding="utf-8") as file:
            # JSON 문자열을 Python 리스트/딕셔너리 구조로 변환합니다.
            return json.load(file)

    def _build_vocabulary(self) -> list[str]:
        """
        음악 데이터의 모든 감성 태그를 중복 없이 모아 단어 사전을 만듭니다.
        """

        # 중복 제거를 위해 set 자료구조를 사용합니다.
        vocab_set: set[str] = set()

        # 모든 음악 데이터를 반복합니다.
        for song in self.songs:
            # 각 음악에 등록된 tags 리스트를 반복합니다.
            for tag in song.get("tags", []):
                # 태그 앞뒤 공백을 제거한 뒤 소문자 형태로 저장합니다.
                vocab_set.add(tag.strip().lower())

        # 결과가 항상 같은 순서가 되도록 정렬해서 리스트로 반환합니다.
        return sorted(vocab_set)

    def _text_to_vector(self, text: str, extra_tags: list[str] | None = None) -> torch.Tensor:
        """
        입력 문장을 단어 사전 크기의 PyTorch Tensor 벡터로 변환합니다.

        text:
            사용자 입력 문장 또는 음악 태그 문자열입니다.

        extra_tags:
            이미 분리된 태그 리스트가 있는 경우 추가로 반영합니다.
        """

        # 단어 사전의 크기만큼 0으로 채워진 Tensor를 생성합니다.
        vector = torch.zeros(len(self.vocabulary), dtype=torch.float32)

        # 비교를 쉽게 하기 위해 입력 문장을 소문자로 변환합니다.
        normalized_text = text.lower()

        # 단어 사전의 각 단어가 입력 문장에 들어 있는지 확인합니다.
        for index, keyword in enumerate(self.vocabulary):
            # 키워드가 문장에 포함되어 있으면 해당 위치의 값을 1로 설정합니다.
            if keyword in normalized_text:
                vector[index] = 1.0

        # extra_tags가 전달된 경우 태그 기반으로도 벡터를 보강합니다.
        if extra_tags:
            # 태그 리스트를 반복합니다.
            for tag in extra_tags:
                # 태그 문자열을 정리합니다.
                normalized_tag = tag.strip().lower()

                # 태그가 단어 사전에 있으면 해당 위치를 1로 설정합니다.
                if normalized_tag in self.vocabulary:
                    vector[self.vocabulary.index(normalized_tag)] = 1.0

        # 사용자가 직접적인 태그 단어를 쓰지 않는 경우를 보완하기 위한 간단한 동의어 규칙입니다.
        synonym_map = {
            "우울": ["슬픔", "위로"],
            "힘들": ["위로", "힐링"],
            "외로": ["그리움", "슬픔"],
            "보고": ["그리움"],
            "사랑": ["사랑", "설렘"],
            "좋아": ["행복", "기쁨"],
            "기뻐": ["행복", "기쁨"],
            "화": ["화남", "분노", "진정"],
            "공부": ["집중"],
            "운동": ["활력", "운동"],
        }

        # 동의어 규칙을 반복하면서 사용자 표현을 감성 태그로 연결합니다.
        for cue, mapped_tags in synonym_map.items():
            # cue가 입력 문장에 포함되어 있는지 확인합니다.
            if cue in normalized_text:
                # 연결된 태그들을 벡터에 반영합니다.
                for tag in mapped_tags:
                    normalized_tag = tag.lower()
                    if normalized_tag in self.vocabulary:
                        vector[self.vocabulary.index(normalized_tag)] = 1.0

        # 완성된 Tensor 벡터를 반환합니다.
        return vector

    def _build_song_vectors(self) -> torch.Tensor:
        """
        모든 음악 데이터를 Tensor 행렬로 변환합니다.

        반환 Tensor의 모양:
            [음악 개수, 단어 사전 크기]
        """

        # 음악별 벡터를 저장할 리스트입니다.
        vectors: list[torch.Tensor] = []

        # 모든 음악 데이터를 반복합니다.
        for song in self.songs:
            # title, artist, mood, tags를 하나의 텍스트로 합칩니다.
            text = " ".join([
                song.get("title", ""),
                song.get("artist", ""),
                song.get("mood", ""),
                " ".join(song.get("tags", [])),
            ])

            # 합쳐진 텍스트와 태그를 Tensor 벡터로 변환합니다.
            vectors.append(self._text_to_vector(text, song.get("tags", [])))

        # 벡터 리스트를 하나의 2차원 Tensor로 묶습니다.
        return torch.stack(vectors)

    def recommend(self, user_message: str, top_k: int = 3) -> tuple[str, list[dict]]:
        """
        사용자 입력 문장에 맞는 음악을 추천합니다.

        user_message:
            사용자의 감정 또는 상황 문장입니다.

        top_k:
            상위 몇 개의 음악을 추천할지 결정합니다.

        반환값:
            추정 감정 문자열과 추천 음악 리스트입니다.
        """

        # 사용자 입력 문장을 Tensor 벡터로 변환합니다.
        user_vector = self._text_to_vector(user_message)

        # 사용자가 감성 키워드를 전혀 입력하지 않은 경우 기본 추천을 위해 작은 값을 더합니다.
        if torch.sum(user_vector) == 0:
            # 모든 음악이 완전히 0점이 되는 것을 방지하기 위해 전체 벡터에 작은 값을 부여합니다.
            user_vector = torch.ones_like(user_vector) * 0.01

        # 사용자 벡터와 음악 벡터 사이의 Cosine Similarity를 계산합니다.
        scores = torch.nn.functional.cosine_similarity(
            user_vector.unsqueeze(0),
            self.song_vectors,
            dim=1,
        )

        # 추천 개수가 전체 음악 개수보다 커지지 않도록 보정합니다.
        safe_top_k = min(top_k, len(self.songs))

        # 유사도가 높은 순서대로 top_k개의 인덱스를 구합니다.
        top_scores, top_indices = torch.topk(scores, k=safe_top_k)

        # 추천 결과를 저장할 리스트입니다.
        recommendations: list[dict] = []

        # 상위 추천 결과를 하나씩 구성합니다.
        for score, index in zip(top_scores.tolist(), top_indices.tolist()):
            # 원본 음악 데이터를 복사합니다.
            song = dict(self.songs[index])

            # API 응답용 유사도 점수를 추가합니다.
            song["score"] = round(float(score), 4)

            # 추천 리스트에 추가합니다.
            recommendations.append(song)

        # 가장 높은 점수를 받은 음악의 mood를 대표 감정으로 사용합니다.
        detected_mood = recommendations[0]["mood"] if recommendations else "일반"

        # 대표 감정과 추천 리스트를 반환합니다.
        return detected_mood, recommendations
