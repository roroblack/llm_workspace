"""
SMTP 이메일 또는 데모 모드를 제공하는 어댑터입니다.
"""

# SMTP 서버와 통신하기 위해 smtplib를 가져옵니다.
import smtplib

# 표준 이메일 메시지를 만들기 위해 EmailMessage를 가져옵니다.
from email.message import EmailMessage


# 이메일 어댑터를 정의합니다.
class EmailAdapter:
    """SMTP 설정이 있으면 실제 전송하고 아니면 데모 결과를 반환합니다."""

    # SMTP 설정을 전달받습니다.
    def __init__(
        self,
        live_mode: bool,
        host: str,
        port: int,
        user: str,
        password: str,
        email_from: str,
    ) -> None:
        # 실제 전송 여부를 저장합니다.
        self.live_mode = live_mode

        # SMTP 호스트를 저장합니다.
        self.host = host

        # SMTP 포트를 저장합니다.
        self.port = port

        # SMTP 사용자를 저장합니다.
        self.user = user

        # SMTP 비밀번호를 저장합니다.
        self.password = password

        # 발신 주소를 저장합니다.
        self.email_from = email_from

    # 이메일을 전송합니다.
    def send(self, to: str, subject: str, body: str) -> dict:
        """지정한 수신자에게 일반 텍스트 이메일을 전송합니다."""

        # 데모 모드이면 실제 전송 없이 내용을 반환합니다.
        if not self.live_mode:
            return {
                "mode": "demo",
                "sent": True,
                "to": to,
                "subject": subject,
                "body": body,
            }

        # 실제 전송에 필요한 설정을 검사합니다.
        if not all([self.host, self.user, self.password, self.email_from]):
            raise RuntimeError("Email live 모드 설정이 부족합니다.")

        # 표준 이메일 메시지 객체를 생성합니다.
        message = EmailMessage()

        # 발신 주소를 설정합니다.
        message["From"] = self.email_from

        # 수신 주소를 설정합니다.
        message["To"] = to

        # 제목을 설정합니다.
        message["Subject"] = subject

        # 본문을 UTF-8 일반 텍스트로 설정합니다.
        message.set_content(body)

        # SMTP 서버에 연결합니다.
        with smtplib.SMTP(self.host, self.port, timeout=20) as server:
            # STARTTLS로 전송 구간을 암호화합니다.
            server.starttls()

            # SMTP 계정으로 로그인합니다.
            server.login(self.user, self.password)

            # 이메일을 전송합니다.
            server.send_message(message)

        # 전송 성공 결과를 반환합니다.
        return {"mode": "live", "sent": True, "to": to, "subject": subject}
