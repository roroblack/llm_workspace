"""
PyCharm에서 실행하는 GAN 학습 및 이미지 생성 콘솔 프로그램입니다.
"""

# 파일 경로를 안전하게 처리하기 위해 pathlib의 Path 클래스를 가져옵니다.
from pathlib import Path

# PyTorch 버전과 GPU 정보를 확인하기 위해 torch를 가져옵니다.
import torch

# 프로젝트 공통 설정 클래스를 가져옵니다.
from config import GANConfig

# MNIST DataLoader 생성 함수를 가져옵니다.
from src.data import create_mnist_dataloader

# GAN 학습 관리 클래스를 가져옵니다.
from src.trainer import GANTrainer

# 난수 시드를 고정하는 유틸리티 함수를 가져옵니다.
from src.utils import set_random_seed


# 숫자 입력을 안전하게 처리하는 함수를 정의합니다.
def read_positive_integer(prompt: str, default: int) -> int:
    """사용자로부터 양의 정수를 입력받고 빈 입력이면 기본값을 반환합니다."""

    # 입력 오류가 발생하면 다시 입력받기 위해 무한 반복문을 시작합니다.
    while True:
        # 안내 문구를 출력하고 양쪽 공백을 제거한 문자열을 받습니다.
        raw_value = input(prompt).strip()

        # 사용자가 아무 값도 입력하지 않았는지 확인합니다.
        if raw_value == "":
            # 빈 입력이면 전달받은 기본값을 반환합니다.
            return default

        # 문자열을 정수로 변환할 때 발생할 수 있는 오류를 처리합니다.
        try:
            # 입력 문자열을 정수형으로 변환합니다.
            value = int(raw_value)

            # 입력값이 1 이상인지 확인합니다.
            if value >= 1:
                # 올바른 양의 정수이면 값을 반환합니다.
                return value

            # 1 미만의 값이면 올바른 범위를 안내합니다.
            print("1 이상의 정수를 입력해야 합니다.")

        # 정수로 변환할 수 없는 문자열이 입력된 경우를 처리합니다.
        except ValueError:
            # 숫자 형식의 값을 다시 입력하도록 안내합니다.
            print("정수 형식으로 입력해야 합니다.")


# GAN 핵심 개념을 콘솔에 출력하는 함수를 정의합니다.
def print_gan_concept() -> None:
    """생성자와 판별자의 역할 및 적대적 학습 흐름을 설명합니다."""

    # 여러 줄 문자열을 사용하여 GAN 개념을 구조적으로 출력합니다.
    print(
        """
============================================================
GAN(Generative Adversarial Network) 핵심 개념
============================================================

1. 생성자(Generator)
   - 무작위 잠재 벡터 z를 입력받습니다.
   - 실제 데이터와 비슷한 가짜 이미지를 생성합니다.
   - 목표: 판별자가 가짜 이미지를 실제라고 판단하도록 만듭니다.

2. 판별자(Discriminator)
   - 실제 이미지 또는 생성자가 만든 가짜 이미지를 입력받습니다.
   - 입력 이미지가 실제인지 가짜인지 구분합니다.
   - 목표: 실제는 1, 가짜는 0으로 정확히 판별합니다.

3. 적대적 학습
   - 판별자는 실제와 가짜를 더 잘 구분하도록 학습합니다.
   - 생성자는 판별자를 더 잘 속이도록 학습합니다.
   - 두 모델이 경쟁하면서 생성 이미지의 품질이 점차 향상됩니다.

4. 이 프로젝트의 처리 흐름
   잠재 벡터 z
        ↓
   생성자 G(z)
        ↓
   가짜 MNIST 이미지
        ↓
   판별자 D(x)
        ↓
   실제/가짜 로짓값
        ↓
   두 모델의 손실 계산 및 파라미터 갱신

5. 저장 결과
   - outputs/generated: 에포크별 생성 이미지
   - outputs/checkpoints: 학습 모델 및 체크포인트
   - outputs/plots: 생성자/판별자 손실 그래프
============================================================
"""
    )


# 현재 실행 환경 정보를 출력하는 함수를 정의합니다.
def print_environment(config: GANConfig) -> None:
    """Python에서 확인 가능한 PyTorch 및 하드웨어 정보를 출력합니다."""

    # 구분선을 출력합니다.
    print("\n========== 실행 환경 ==========")

    # 현재 설치된 PyTorch 버전을 출력합니다.
    print(f"PyTorch 버전: {torch.__version__}")

    # CUDA GPU 사용 가능 여부를 출력합니다.
    print(f"CUDA 사용 가능: {torch.cuda.is_available()}")

    # 실제 선택된 실행 장치를 출력합니다.
    print(f"선택된 실행 장치: {config.device}")

    # CUDA를 사용할 수 있는 경우인지 확인합니다.
    if torch.cuda.is_available():
        # 첫 번째 CUDA GPU의 제품명을 출력합니다.
        print(f"GPU 이름: {torch.cuda.get_device_name(0)}")

    # 이미지가 저장되는 디렉터리를 출력합니다.
    print(f"출력 디렉터리: {config.output_dir}")

    # 마지막 구분선을 출력합니다.
    print("===============================\n")


# 처음부터 GAN을 학습하는 함수를 정의합니다.
def train_new_model(config: GANConfig) -> None:
    """MNIST 데이터셋으로 새로운 GAN 모델을 처음부터 학습합니다."""

    # 사용자가 학습 에포크 수를 직접 입력하거나 기본값을 사용할 수 있도록 합니다.
    epochs = read_positive_integer(
        prompt=f"학습 에포크 수를 입력하세요. [기본값: {config.epochs}]: ",
        default=config.epochs,
    )

    # MNIST 학습 데이터를 배치 단위로 읽는 DataLoader를 생성합니다.
    dataloader = create_mnist_dataloader(config)

    # 생성자, 판별자, 손실 함수, 옵티마이저를 포함하는 학습 객체를 생성합니다.
    trainer = GANTrainer(config)

    # 선택한 에포크 수만큼 GAN 학습을 시작합니다.
    trainer.train(dataloader=dataloader, epochs=epochs)


# 저장된 체크포인트에서 이어서 학습하는 함수를 정의합니다.
def resume_training(config: GANConfig) -> None:
    """gan_latest.pt 체크포인트를 불러와 추가 학습을 수행합니다."""

    # 기본 체크포인트 파일 경로를 지정합니다.
    checkpoint_path = config.checkpoint_dir / "gan_latest.pt"

    # 체크포인트 파일이 존재하는지 확인합니다.
    if not checkpoint_path.exists():
        # 파일이 없으면 먼저 새 학습을 수행하도록 안내합니다.
        print(f"\n체크포인트가 없습니다: {checkpoint_path}")
        print("먼저 메뉴 2번으로 모델을 학습하세요.\n")

        # 현재 함수를 종료하고 메뉴로 돌아갑니다.
        return

    # 추가로 학습할 에포크 수를 입력받습니다.
    additional_epochs = read_positive_integer(
        prompt="추가 학습 에포크 수를 입력하세요. [기본값: 5]: ",
        default=5,
    )

    # MNIST DataLoader를 생성합니다.
    dataloader = create_mnist_dataloader(config)

    # 새 GANTrainer 객체를 생성합니다.
    trainer = GANTrainer(config)

    # 체크포인트 상태를 복원한 후 지정한 에포크만큼 추가 학습합니다.
    trainer.train(
        dataloader=dataloader,
        epochs=additional_epochs,
        resume_checkpoint=checkpoint_path,
    )


# 학습된 생성자 모델을 이용하여 새로운 이미지를 만드는 함수를 정의합니다.
def generate_images(config: GANConfig) -> None:
    """generator_final.pt를 불러와 새로운 가짜 숫자 이미지를 생성합니다."""

    # 최종 생성자 가중치 파일의 기본 경로를 지정합니다.
    generator_path = config.checkpoint_dir / "generator_final.pt"

    # 최종 가중치가 없으면 최신 체크포인트를 대신 사용할 수 있는지 확인합니다.
    if not generator_path.exists():
        # 최신 GAN 체크포인트 경로를 지정합니다.
        checkpoint_path = config.checkpoint_dir / "gan_latest.pt"

        # 최신 체크포인트도 존재하지 않는지 확인합니다.
        if not checkpoint_path.exists():
            # 학습된 모델 파일이 없음을 안내합니다.
            print("\n학습된 모델이 없습니다. 먼저 메뉴 2번으로 학습하세요.\n")

            # 현재 함수를 종료하고 메뉴로 돌아갑니다.
            return

        # 체크포인트만 존재할 경우 GANTrainer 객체를 생성합니다.
        trainer = GANTrainer(config)

        # 체크포인트에서 생성자와 판별자 상태를 함께 복원합니다.
        from src.utils import load_checkpoint

        # 모델 상태만 필요하므로 옵티마이저에는 None을 전달합니다.
        load_checkpoint(
            checkpoint_path=checkpoint_path,
            generator=trainer.generator,
            discriminator=trainer.discriminator,
            generator_optimizer=None,
            discriminator_optimizer=None,
            device=config.device,
        )

    # 생성자 전용 최종 가중치 파일이 존재하는 경우입니다.
    else:
        # GANTrainer 객체를 생성합니다.
        trainer = GANTrainer(config)

        # 생성자 전용 가중치 파일을 불러옵니다.
        trainer.load_generator_weights(generator_path)

    # 생성할 이미지 개수를 입력받습니다.
    sample_count = read_positive_integer(
        prompt="생성할 이미지 수를 입력하세요. [기본값: 64]: ",
        default=64,
    )

    # 새 이미지 파일의 저장 경로를 지정합니다.
    output_path = config.generated_dir / "manual_generated.png"

    # 입력한 개수만큼 새로운 잠재 벡터를 사용하여 이미지를 생성합니다.
    trainer.generate_samples(
        output_path=output_path,
        sample_count=sample_count,
    )

    # 생성 완료 및 저장 경로를 출력합니다.
    print(f"\n이미지를 생성했습니다: {output_path}\n")


# 프로젝트에서 생성된 결과 파일의 위치를 출력하는 함수를 정의합니다.
def print_output_paths(config: GANConfig) -> None:
    """학습 결과 파일을 확인할 수 있는 경로를 출력합니다."""

    # 생성 이미지 디렉터리를 출력합니다.
    print(f"\n생성 이미지 폴더: {config.generated_dir}")

    # 체크포인트 디렉터리를 출력합니다.
    print(f"모델 파일 폴더: {config.checkpoint_dir}")

    # 손실 그래프 디렉터리를 출력합니다.
    print(f"손실 그래프 폴더: {config.plot_dir}\n")


# 콘솔 프로그램의 전체 메뉴 반복을 담당하는 main 함수를 정의합니다.
def main() -> None:
    """GAN 콘솔 메뉴를 출력하고 사용자의 선택에 따라 기능을 실행합니다."""

    # 설정 객체를 생성합니다.
    config = GANConfig()

    # 데이터 및 출력 폴더를 생성합니다.
    config.create_directories()

    # 재현 가능한 결과를 위해 난수 시드를 고정합니다.
    set_random_seed(config.random_seed)

    # 현재 실행 환경 정보를 먼저 출력합니다.
    print_environment(config)

    # 사용자가 종료 메뉴를 선택할 때까지 반복합니다.
    while True:
        # 콘솔 메뉴를 출력합니다.
        print(
            """
================ GAN MNIST 콘솔 프로젝트 ================
1. GAN 핵심 개념 확인
2. 새로운 GAN 모델 학습
3. 체크포인트에서 이어서 학습
4. 학습된 생성자로 이미지 생성
5. 결과 파일 저장 경로 확인
0. 프로그램 종료
=========================================================
"""
        )

        # 사용자의 메뉴 선택값을 문자열로 입력받습니다.
        choice = input("메뉴 번호를 입력하세요: ").strip()

        # 사용자가 1번을 선택했는지 확인합니다.
        if choice == "1":
            # GAN의 핵심 개념을 화면에 출력합니다.
            print_gan_concept()

        # 사용자가 2번을 선택했는지 확인합니다.
        elif choice == "2":
            # 예외가 발생해도 프로그램 전체가 종료되지 않도록 처리합니다.
            try:
                # 새로운 모델 학습 기능을 실행합니다.
                train_new_model(config)

            # 사용자가 Ctrl+C를 눌러 학습을 중단한 경우를 처리합니다.
            except KeyboardInterrupt:
                # 중단 사실을 안내하고 메뉴로 돌아갑니다.
                print("\n사용자가 학습을 중단했습니다.\n")

            # 그 밖의 실행 오류를 처리합니다.
            except Exception as error:
                # 오류 타입과 메시지를 출력하여 원인 파악을 돕습니다.
                print(f"\n[학습 오류] {type(error).__name__}: {error}\n")

        # 사용자가 3번을 선택했는지 확인합니다.
        elif choice == "3":
            # 이어서 학습 중 발생할 수 있는 예외를 처리합니다.
            try:
                # 체크포인트 이어서 학습 기능을 실행합니다.
                resume_training(config)

            # 사용자가 Ctrl+C로 중단한 경우를 처리합니다.
            except KeyboardInterrupt:
                # 중단 사실을 출력하고 메뉴로 돌아갑니다.
                print("\n사용자가 학습을 중단했습니다.\n")

            # 그 밖의 오류를 처리합니다.
            except Exception as error:
                # 오류 타입과 상세 메시지를 출력합니다.
                print(f"\n[이어 학습 오류] {type(error).__name__}: {error}\n")

        # 사용자가 4번을 선택했는지 확인합니다.
        elif choice == "4":
            # 이미지 생성 중 발생할 수 있는 예외를 처리합니다.
            try:
                # 학습된 생성자로 새로운 이미지를 만듭니다.
                generate_images(config)

            # 이미지 생성 과정의 일반 오류를 처리합니다.
            except Exception as error:
                # 오류 타입과 메시지를 화면에 출력합니다.
                print(f"\n[이미지 생성 오류] {type(error).__name__}: {error}\n")

        # 사용자가 5번을 선택했는지 확인합니다.
        elif choice == "5":
            # 결과 파일이 저장되는 폴더 위치를 출력합니다.
            print_output_paths(config)

        # 사용자가 0번을 선택했는지 확인합니다.
        elif choice == "0":
            # 종료 메시지를 출력합니다.
            print("GAN 콘솔 프로그램을 종료합니다.")

            # while 반복문을 종료합니다.
            break

        # 정의되지 않은 메뉴 번호가 입력된 경우입니다.
        else:
            # 올바른 메뉴 번호를 다시 입력하도록 안내합니다.
            print("0~5 사이의 메뉴 번호를 입력하세요.\n")


# 현재 파일을 직접 실행한 경우인지 확인합니다.
if __name__ == "__main__":
    # 직접 실행된 경우 main 함수를 호출하여 콘솔 프로그램을 시작합니다.
    main()
