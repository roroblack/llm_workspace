"""
GAN의 학습, 모델 저장, 생성 이미지 출력 기능을 담당하는 모듈입니다.
"""

# 경로 처리를 위해 pathlib의 Path 클래스를 가져옵니다.
from pathlib import Path

# GAN 모델과 손실 함수를 실행하기 위해 torch를 가져옵니다.
import torch

# 신경망 손실 함수를 사용하기 위해 torch.nn을 가져옵니다.
from torch import nn

# Adam 옵티마이저를 사용하기 위해 torch.optim을 가져옵니다.
from torch import optim

# DataLoader 타입을 명시하기 위해 가져옵니다.
from torch.utils.data import DataLoader

# 프로젝트 설정 클래스를 가져옵니다.
from config import GANConfig

# 생성자, 판별자, 가중치 초기화 함수를 가져옵니다.
from src.models import Discriminator, Generator, initialize_weights

# 이미지, 그래프, 체크포인트 처리 함수를 가져옵니다.
from src.utils import (
    load_checkpoint,
    save_checkpoint,
    save_generated_images,
    save_loss_plot,
)


# GAN 학습 과정을 하나의 객체로 관리하기 위한 클래스를 정의합니다.
class GANTrainer:
    """생성자와 판별자를 교대로 학습하고 결과를 저장합니다."""

    # GANTrainer 객체를 초기화하는 메서드를 정의합니다.
    def __init__(self, config: GANConfig) -> None:
        # 전달받은 프로젝트 설정 객체를 멤버 변수에 저장합니다.
        self.config = config

        # 계산에 사용할 CPU 또는 GPU 장치를 저장합니다.
        self.device = config.device

        # 설정에 맞는 생성자 모델을 생성하고 실행 장치로 이동합니다.
        self.generator = Generator(
            latent_dim=config.latent_dim,
            image_size=config.flattened_image_size,
        ).to(self.device)

        # 설정에 맞는 판별자 모델을 생성하고 실행 장치로 이동합니다.
        self.discriminator = Discriminator(
            image_size=config.flattened_image_size
        ).to(self.device)

        # 생성자 내부의 Linear 계층에 초기화 함수를 적용합니다.
        self.generator.apply(initialize_weights)

        # 판별자 내부의 Linear 계층에 초기화 함수를 적용합니다.
        self.discriminator.apply(initialize_weights)

        # 로짓을 직접 입력받는 이진 교차 엔트로피 손실 함수를 생성합니다.
        self.criterion = nn.BCEWithLogitsLoss()

        # 생성자 파라미터를 갱신할 Adam 옵티마이저를 생성합니다.
        self.generator_optimizer = optim.Adam(
            # 생성자가 학습해야 할 전체 파라미터를 전달합니다.
            self.generator.parameters(),

            # 설정 파일의 학습률을 적용합니다.
            lr=config.learning_rate,

            # GAN에서 자주 사용하는 Adam 모멘텀 계수를 적용합니다.
            betas=(config.beta1, config.beta2),
        )

        # 판별자 파라미터를 갱신할 Adam 옵티마이저를 생성합니다.
        self.discriminator_optimizer = optim.Adam(
            # 판별자가 학습해야 할 전체 파라미터를 전달합니다.
            self.discriminator.parameters(),

            # 생성자와 같은 학습률을 적용합니다.
            lr=config.learning_rate,

            # 생성자와 같은 Adam 모멘텀 계수를 적용합니다.
            betas=(config.beta1, config.beta2),
        )

        # 에포크별 생성자 평균 손실을 저장할 빈 목록을 생성합니다.
        self.generator_losses: list[float] = []

        # 에포크별 판별자 평균 손실을 저장할 빈 목록을 생성합니다.
        self.discriminator_losses: list[float] = []

        # 학습 중 같은 잠재 벡터의 변화 결과를 비교할 고정 노이즈를 생성합니다.
        self.fixed_noise = torch.randn(
            config.sample_count,
            config.latent_dim,
            device=self.device,
        )

    # 판별자를 한 단계 학습하는 내부 메서드를 정의합니다.
    def _train_discriminator(self, real_images: torch.Tensor) -> float:
        # 현재 배치에 포함된 실제 이미지 개수를 계산합니다.
        batch_size = real_images.size(0)

        # 판별자 파라미터에 남아 있는 이전 기울기값을 0으로 초기화합니다.
        self.discriminator_optimizer.zero_grad(set_to_none=True)

        # 실제 이미지에 대한 정답 레이블 1을 생성합니다.
        real_labels = torch.ones(batch_size, 1, device=self.device)

        # 실제 이미지를 판별자에 입력하여 실제 여부 로짓을 계산합니다.
        real_logits = self.discriminator(real_images)

        # 실제 이미지를 실제로 판별하도록 손실을 계산합니다.
        real_loss = self.criterion(real_logits, real_labels)

        # 가짜 이미지를 만들 잠재 벡터를 표준정규분포에서 생성합니다.
        noise = torch.randn(
            batch_size,
            self.config.latent_dim,
            device=self.device,
        )

        # 생성자를 통해 가짜 이미지 배치를 생성합니다.
        fake_images = self.generator(noise)

        # 가짜 이미지에 대한 정답 레이블 0을 생성합니다.
        fake_labels = torch.zeros(batch_size, 1, device=self.device)

        # 생성자 쪽으로 기울기가 전달되지 않도록 가짜 이미지를 계산 그래프에서 분리합니다.
        fake_logits = self.discriminator(fake_images.detach())

        # 가짜 이미지를 가짜로 판별하도록 손실을 계산합니다.
        fake_loss = self.criterion(fake_logits, fake_labels)

        # 실제 이미지 손실과 가짜 이미지 손실을 합산합니다.
        discriminator_loss = real_loss + fake_loss

        # 판별자 손실을 기준으로 역전파하여 기울기를 계산합니다.
        discriminator_loss.backward()

        # 계산된 기울기를 사용하여 판별자 파라미터를 갱신합니다.
        self.discriminator_optimizer.step()

        # 출력용으로 손실 텐서를 Python 실수값으로 변환하여 반환합니다.
        return discriminator_loss.item()

    # 생성자를 한 단계 학습하는 내부 메서드를 정의합니다.
    def _train_generator(self, batch_size: int) -> float:
        # 생성자 파라미터에 남아 있는 이전 기울기값을 0으로 초기화합니다.
        self.generator_optimizer.zero_grad(set_to_none=True)

        # 생성자의 입력으로 사용할 새로운 잠재 벡터를 생성합니다.
        noise = torch.randn(
            batch_size,
            self.config.latent_dim,
            device=self.device,
        )

        # 잠재 벡터를 생성자에 입력하여 가짜 이미지를 생성합니다.
        fake_images = self.generator(noise)

        # 생성된 가짜 이미지를 판별자에 전달합니다.
        fake_logits = self.discriminator(fake_images)

        # 생성자는 가짜 이미지를 판별자가 실제라고 판단하도록 학습해야 하므로 레이블 1을 사용합니다.
        target_labels = torch.ones(batch_size, 1, device=self.device)

        # 판별자가 가짜 이미지를 실제로 판단하도록 만드는 생성자 손실을 계산합니다.
        generator_loss = self.criterion(fake_logits, target_labels)

        # 생성자 손실을 기준으로 역전파하여 생성자 파라미터의 기울기를 계산합니다.
        generator_loss.backward()

        # 계산된 기울기를 사용하여 생성자 파라미터를 갱신합니다.
        self.generator_optimizer.step()

        # 출력용으로 손실 텐서를 Python 실수값으로 변환하여 반환합니다.
        return generator_loss.item()

    # 전체 GAN 학습을 수행하는 공개 메서드를 정의합니다.
    def train(
        self,
        dataloader: DataLoader,
        epochs: int | None = None,
        resume_checkpoint: Path | None = None,
    ) -> None:
        """설정된 에포크만큼 GAN을 학습하고 결과 파일을 저장합니다."""

        # 사용자가 별도 에포크를 전달하지 않으면 설정값을 사용합니다.
        total_epochs = epochs if epochs is not None else self.config.epochs

        # 처음 학습을 시작할 기본 에포크 번호를 1로 지정합니다.
        start_epoch = 1

        # 이어서 학습할 체크포인트 경로가 전달되었는지 확인합니다.
        if resume_checkpoint is not None:
            # 체크포인트 파일이 실제로 존재하는지 확인합니다.
            if not resume_checkpoint.exists():
                # 파일이 없으면 사용자가 원인을 바로 알 수 있도록 예외를 발생시킵니다.
                raise FileNotFoundError(
                    f"체크포인트 파일을 찾을 수 없습니다: {resume_checkpoint}"
                )

            # 체크포인트에서 모델, 옵티마이저, 손실 기록을 복원합니다.
            start_epoch, self.generator_losses, self.discriminator_losses = (
                load_checkpoint(
                    checkpoint_path=resume_checkpoint,
                    generator=self.generator,
                    discriminator=self.discriminator,
                    generator_optimizer=self.generator_optimizer,
                    discriminator_optimizer=self.discriminator_optimizer,
                    device=self.device,
                )
            )

            # 복원된 시작 에포크 번호를 사용자에게 출력합니다.
            print(f"\n[체크포인트 복원] {start_epoch} 에포크부터 이어서 학습합니다.")

        # 생성자를 학습 모드로 전환하여 BatchNorm이 학습 방식으로 동작하게 합니다.
        self.generator.train()

        # 판별자를 학습 모드로 전환합니다.
        self.discriminator.train()

        # 시작 에포크부터 사용자가 지정한 추가 에포크 수만큼 반복합니다.
        for epoch in range(start_epoch, start_epoch + total_epochs):
            # 현재 에포크의 생성자 손실을 누적할 변수를 초기화합니다.
            epoch_generator_loss = 0.0

            # 현재 에포크의 판별자 손실을 누적할 변수를 초기화합니다.
            epoch_discriminator_loss = 0.0

            # 전체 배치 개수를 미리 계산하여 진행률 출력에 사용합니다.
            total_batches = len(dataloader)

            # DataLoader에서 실제 이미지와 정답 숫자 레이블을 배치 단위로 가져옵니다.
            for batch_index, (real_images, _) in enumerate(dataloader, start=1):
                # 실제 이미지 텐서를 현재 실행 장치로 이동합니다.
                real_images = real_images.to(self.device, non_blocking=True)

                # 4차원 이미지를 판별자가 받을 수 있는 2차원 벡터 형태로 펼칩니다.
                real_images = real_images.view(
                    real_images.size(0),
                    self.config.flattened_image_size,
                )

                # 실제 이미지와 생성 이미지를 사용하여 판별자를 한 단계 학습합니다.
                discriminator_loss = self._train_discriminator(real_images)

                # 같은 배치 크기로 생성자를 한 단계 학습합니다.
                generator_loss = self._train_generator(real_images.size(0))

                # 현재 배치의 생성자 손실을 에포크 누적값에 더합니다.
                epoch_generator_loss += generator_loss

                # 현재 배치의 판별자 손실을 에포크 누적값에 더합니다.
                epoch_discriminator_loss += discriminator_loss

                # 첫 배치이거나 지정한 출력 간격에 해당하는지 확인합니다.
                if (
                    batch_index == 1
                    or batch_index % self.config.log_interval == 0
                    or batch_index == total_batches
                ):
                    # 현재 학습 진행 상황과 두 손실값을 화면에 출력합니다.
                    print(
                        f"[Epoch {epoch:03d}] "
                        f"[Batch {batch_index:04d}/{total_batches:04d}] "
                        f"D Loss: {discriminator_loss:.4f} | "
                        f"G Loss: {generator_loss:.4f}"
                    )

            # 에포크 내 전체 배치에 대한 생성자 평균 손실을 계산합니다.
            average_generator_loss = epoch_generator_loss / total_batches

            # 에포크 내 전체 배치에 대한 판별자 평균 손실을 계산합니다.
            average_discriminator_loss = epoch_discriminator_loss / total_batches

            # 계산한 생성자 평균 손실을 기록 목록에 추가합니다.
            self.generator_losses.append(average_generator_loss)

            # 계산한 판별자 평균 손실을 기록 목록에 추가합니다.
            self.discriminator_losses.append(average_discriminator_loss)

            # 현재 에포크의 고정 노이즈 생성 결과를 저장합니다.
            self.generate_samples(
                output_path=(
                    self.config.generated_dir
                    / f"epoch_{epoch:03d}.png"
                ),
                noise=self.fixed_noise,
            )

            # 현재까지의 모델과 옵티마이저 상태를 체크포인트로 저장합니다.
            save_checkpoint(
                output_path=self.config.checkpoint_dir / "gan_latest.pt",
                epoch=epoch,
                generator=self.generator,
                discriminator=self.discriminator,
                generator_optimizer=self.generator_optimizer,
                discriminator_optimizer=self.discriminator_optimizer,
                generator_losses=self.generator_losses,
                discriminator_losses=self.discriminator_losses,
            )

            # 현재까지의 에포크 평균 손실을 그래프 파일로 저장합니다.
            save_loss_plot(
                generator_losses=self.generator_losses,
                discriminator_losses=self.discriminator_losses,
                output_path=self.config.plot_dir / "training_loss.png",
            )

            # 한 에포크가 완료되었음을 평균 손실과 함께 출력합니다.
            print(
                f"[에포크 완료] Epoch {epoch:03d} | "
                f"평균 D Loss: {average_discriminator_loss:.4f} | "
                f"평균 G Loss: {average_generator_loss:.4f}\n"
            )

        # 전체 학습 완료 후 생성자 가중치만 별도 파일로 저장합니다.
        torch.save(
            self.generator.state_dict(),
            self.config.checkpoint_dir / "generator_final.pt",
        )

        # 전체 학습 완료 후 판별자 가중치만 별도 파일로 저장합니다.
        torch.save(
            self.discriminator.state_dict(),
            self.config.checkpoint_dir / "discriminator_final.pt",
        )

        # 최종 모델 및 결과 파일의 저장 위치를 사용자에게 안내합니다.
        print("[학습 완료] 모델과 생성 이미지 및 손실 그래프를 저장했습니다.")
        print(f"- 생성 이미지: {self.config.generated_dir}")
        print(f"- 체크포인트: {self.config.checkpoint_dir}")
        print(f"- 손실 그래프: {self.config.plot_dir}")

    # 생성자 모델로 샘플 이미지를 만드는 메서드를 정의합니다.
    def generate_samples(
        self,
        output_path: Path,
        noise: torch.Tensor | None = None,
        sample_count: int | None = None,
    ) -> None:
        """학습된 생성자로 가짜 이미지를 만들고 PNG 파일로 저장합니다."""

        # 생성 전 현재 생성자의 학습 모드 상태를 저장합니다.
        was_training = self.generator.training

        # BatchNorm이 저장된 통계값을 사용하도록 생성자를 평가 모드로 전환합니다.
        self.generator.eval()

        # 이미지 생성 과정에서는 역전파가 필요 없으므로 기울기 계산을 비활성화합니다.
        with torch.no_grad():
            # 외부에서 잠재 벡터를 전달하지 않은 경우인지 확인합니다.
            if noise is None:
                # 생성할 이미지 수를 인수 또는 설정값에서 결정합니다.
                count = (
                    sample_count
                    if sample_count is not None
                    else self.config.sample_count
                )

                # 결정된 개수만큼 새로운 잠재 벡터를 생성합니다.
                noise = torch.randn(
                    count,
                    self.config.latent_dim,
                    device=self.device,
                )

            # 잠재 벡터를 현재 실행 장치로 이동합니다.
            noise = noise.to(self.device)

            # 생성자에 잠재 벡터를 입력하여 가짜 이미지를 생성합니다.
            generated_images = self.generator(noise)

            # 생성 이미지를 격자 형태의 PNG 파일로 저장합니다.
            save_generated_images(
                generated_images=generated_images,
                output_path=output_path,
                image_channels=self.config.image_channels,
                image_height=self.config.image_height,
                image_width=self.config.image_width,
            )

        # 생성 전 모델이 학습 모드였다면 다시 학습 모드로 복원합니다.
        if was_training:
            # 생성자를 다시 학습 모드로 전환합니다.
            self.generator.train()

    # 생성자 가중치 파일을 불러오는 메서드를 정의합니다.
    def load_generator_weights(self, weight_path: Path) -> None:
        """생성자 전용 가중치 파일을 현재 생성자 모델에 적용합니다."""

        # 지정한 생성자 가중치 파일이 존재하는지 확인합니다.
        if not weight_path.exists():
            # 파일이 없으면 명확한 오류 메시지와 함께 예외를 발생시킵니다.
            raise FileNotFoundError(
                f"생성자 가중치 파일을 찾을 수 없습니다: {weight_path}"
            )

        # 현재 CPU 또는 GPU 장치에 맞게 가중치 파일을 불러옵니다.
        state_dict = torch.load(weight_path, map_location=self.device)

        # 불러온 파라미터를 생성자 모델에 적용합니다.
        self.generator.load_state_dict(state_dict)
