"""
Slack Web API 또는 데모 모드를 제공하는 어댑터입니다.
"""

# HTTP 요청을 보내기 위해 httpx를 가져옵니다.
import httpx


# Slack 어댑터를 정의합니다.
class SlackAdapter:
    """Slack 채널 메시지 전송 기능을 제공합니다."""

    # Slack 설정을 전달받습니다.
    def __init__(self, live_mode: bool, token: str, default_channel: str) -> None:
        # 실제 API 호출 여부를 저장합니다.
        self.live_mode = live_mode

        # Slack Bot Token을 저장합니다.
        self.token = token

        # 기본 채널 ID를 저장합니다.
        self.default_channel = default_channel

    # Slack 메시지를 전송합니다.
    def post_message(self, text: str, channel: str = "") -> dict:
        """지정한 Slack 채널에 메시지를 전송합니다."""

        # 입력 채널이 없으면 기본 채널을 사용합니다.
        target_channel = channel or self.default_channel

        # 데모 모드이면 외부로 전송하지 않고 결과만 반환합니다.
        if not self.live_mode:
            return {
                "mode": "demo",
                "ok": True,
                "channel": target_channel or "DEMO_CHANNEL",
                "text": text,
            }

        # 실제 호출에 필요한 토큰과 채널을 검사합니다.
        if not self.token or not target_channel:
            raise RuntimeError("Slack live 모드 설정이 부족합니다.")

        # Slack chat.postMessage API를 호출합니다.
        response = httpx.post(
            "https://slack.com/api/chat.postMessage",
            headers={"Authorization": f"Bearer {self.token}"},
            json={"channel": target_channel, "text": text},
            timeout=15.0,
        )

        # HTTP 자체 오류를 검사합니다.
        response.raise_for_status()

        # Slack 응답 JSON을 가져옵니다.
        result = response.json()

        # Slack API의 ok 값이 false이면 오류 메시지를 발생시킵니다.
        if not result.get("ok"):
            raise RuntimeError(f"Slack API 오류: {result.get('error', 'unknown_error')}")

        # 메시지 전송 결과를 반환합니다.
        return result
