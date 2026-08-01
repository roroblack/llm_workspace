"""조건부 GAN을 학습하고 에포크별 이미지를 저장합니다."""

# 실행 재현성을 위한 Python 난수 모듈을 가져옵니다.
import random
# NumPy 난수 시드를 고정하기 위해 numpy를 가져옵니다.
import numpy as np
# 텐서 연산과 GPU 사용을 위해 torch를 가져옵니다.
import torch
# 손실 함수를 위해 torch.nn을 nn으로 가져옵니다.
from torch import nn
# 데이터 배치와 부분 데이터셋을 위해 DataLoader, Subset을 가져옵니다.
from torch.utils.data import DataLoader, Subset
# MNIST 데이터와 전처리를 위해 torchvision 기능을 가져옵니다.
from torchvision import datasets, transforms
# 이미지 격자 저장을 위해 save_image를 가져옵니다.
from torchvision.utils import save_image
# 프로젝트 설정 객체를 가져옵니다.
from app.core.config import settings
# 조건부 GAN 모델과 초기화 함수를 가져옵니다.
from app.models.conditional_gan import ConditionalGenerator, ConditionalDiscriminator, initialize_weights
# 작업 상태 관리자 객체를 가져옵니다.
from app.services.job_manager import job_manager


def set_seed(seed: int) -> None:
    """Python, NumPy, PyTorch의 난수 시드를 고정합니다."""
    # Python 난수 시드를 설정합니다.
    random.seed(seed)
    # NumPy 난수 시드를 설정합니다.
    np.random.seed(seed)
    # CPU PyTorch 난수 시드를 설정합니다.
    torch.manual_seed(seed)
    # 모든 CUDA 장치 난수 시드를 설정합니다.
    torch.cuda.manual_seed_all(seed)


def create_dataloader(device: torch.device) -> DataLoader:
    """MNIST 일부를 -1~1 범위로 정규화한 DataLoader를 반환합니다."""
    # 이미지 전처리 파이프라인을 정의합니다.
    transform = transforms.Compose([
        # PIL 이미지를 0~1 텐서로 변환합니다.
        transforms.ToTensor(),
        # Tanh 출력에 맞춰 -1~1 범위로 정규화합니다.
        transforms.Normalize((0.5,), (0.5,)),
    ])
    # MNIST 학습 데이터셋을 생성하고 없으면 내려받습니다.
    dataset = datasets.MNIST(
        root=str(settings.data_dir),
        train=True,
        download=True,
        transform=transform,
    )
    # 전체 데이터와 설정 최대값 중 작은 크기를 선택합니다.
    subset_size = min(len(dataset), settings.max_training_samples)
    # 빠른 실습용 부분 데이터셋을 생성합니다.
    subset = Subset(dataset, range(subset_size))
    # 미니배치 공급 객체를 생성하여 반환합니다.
    return DataLoader(
        subset,
        batch_size=settings.batch_size,
        shuffle=True,
        num_workers=settings.num_workers,
        pin_memory=device.type == "cuda",
        drop_last=False,
    )


def save_epoch_sample(generator, fixed_noise, target_digit, output_path, device) -> None:
    """현재 생성자로 대상 숫자 64장을 생성하여 PNG로 저장합니다."""
    # 원래 학습 모드 상태를 저장합니다.
    was_training = generator.training
    # BatchNorm이 평가 방식으로 동작하도록 전환합니다.
    generator.eval()
    # 모든 샘플에 동일한 목표 숫자 레이블을 생성합니다.
    labels = torch.full(
        (fixed_noise.size(0),),
        target_digit,
        dtype=torch.long,
        device=device,
    )
    # 이미지 저장 과정에서 기울기 계산을 비활성화합니다.
    with torch.no_grad():
        # 고정 노이즈와 숫자 조건으로 이미지를 생성합니다.
        generated = generator(fixed_noise, labels)
        # 784차원 벡터를 1×28×28 이미지로 복원합니다.
        generated = generated.view(-1, 1, 28, 28)
        # -1~1 범위를 0~1 범위로 변환합니다.
        generated = (generated + 1.0) / 2.0
        # 출력 폴더가 없으면 생성합니다.
        output_path.parent.mkdir(parents=True, exist_ok=True)
        # 64장을 8×8 격자 이미지로 저장합니다.
        save_image(generated.cpu(), str(output_path), nrow=8)
    # 원래 학습 모드였다면 복원합니다.
    if was_training:
        # 생성자를 다시 학습 모드로 전환합니다.
        generator.train()


def run_generation_job(job_id: str, prompt: str, normalized_prompt: str, target_digit: int, epochs: int) -> None:
    """GAN을 학습하고 작업별 에포크 이미지 및 모델을 저장합니다."""
    # 모든 작업 오류를 상태 정보에 기록하기 위해 예외 처리합니다.
    try:
        # 대상 숫자와 에포크에 따라 재현 가능한 시드를 계산합니다.
        set_seed(2026 + target_digit * 100 + epochs)
        # CUDA 사용 가능 여부에 따라 실행 장치를 선택합니다.
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        # 작업 상태를 실행 중으로 변경합니다.
        job_manager.update(
            job_id,
            status="running",
            message="MNIST 데이터와 GAN 모델을 준비하고 있습니다.",
            device=str(device),
            progress=1,
        )
        # MNIST DataLoader를 생성합니다.
        dataloader = create_dataloader(device)
        # 조건부 생성자를 생성하고 장치로 이동합니다.
        generator = ConditionalGenerator(settings.latent_dim).to(device)
        # 조건부 판별자를 생성하고 장치로 이동합니다.
        discriminator = ConditionalDiscriminator().to(device)
        # 생성자 가중치를 초기화합니다.
        generator.apply(initialize_weights)
        # 판별자 가중치를 초기화합니다.
        discriminator.apply(initialize_weights)
        # 로짓 기반 이진 교차 엔트로피 손실을 생성합니다.
        criterion = nn.BCEWithLogitsLoss()
        # 생성자 Adam 옵티마이저를 생성합니다.
        generator_optimizer = torch.optim.Adam(
            generator.parameters(),
            lr=settings.learning_rate,
            betas=(settings.beta1, settings.beta2),
        )
        # 판별자 Adam 옵티마이저를 생성합니다.
        discriminator_optimizer = torch.optim.Adam(
            discriminator.parameters(),
            lr=settings.learning_rate,
            betas=(settings.beta1, settings.beta2),
        )
        # 에포크별 변화를 비교할 고정 잠재 벡터를 생성합니다.
        fixed_noise = torch.randn(64, settings.latent_dim, device=device)
        # 작업별 결과 디렉터리를 생성합니다.
        job_directory = settings.generation_dir / job_id
        # 결과 디렉터리가 없으면 생성합니다.
        job_directory.mkdir(parents=True, exist_ok=True)
        # 원본 프롬프트와 실행 설정을 텍스트 파일로 저장합니다.
        (job_directory / "prompt.txt").write_text(
            f"original_prompt={prompt}\n"
            f"normalized_prompt={normalized_prompt}\n"
            f"target_digit={target_digit}\n"
            f"epochs={epochs}\n"
            f"device={device}\n",
            encoding="utf-8",
        )
        # 프론트에 전달할 에포크 이미지 URL 목록을 생성합니다.
        epoch_image_urls: list[str] = []
        # 생성자를 학습 모드로 전환합니다.
        generator.train()
        # 판별자를 학습 모드로 전환합니다.
        discriminator.train()
        # 지정한 에포크 수만큼 반복합니다.
        for epoch in range(1, epochs + 1):
            # 생성자 손실 누적값을 초기화합니다.
            generator_loss_sum = 0.0
            # 판별자 손실 누적값을 초기화합니다.
            discriminator_loss_sum = 0.0
            # 처리한 배치 수를 초기화합니다.
            processed_batches = 0
            # 실제 이미지와 숫자 레이블을 배치 단위로 가져옵니다.
            for real_images, real_labels in dataloader:
                # 현재 배치 크기를 계산합니다.
                batch_size = real_images.size(0)
                # 실제 이미지를 장치로 이동하고 평탄화합니다.
                real_images = real_images.to(device, non_blocking=True).view(batch_size, -1)
                # 실제 숫자 레이블을 장치로 이동합니다.
                real_labels = real_labels.to(device, non_blocking=True)
                # 실제 목표 레이블 1을 생성합니다.
                valid_targets = torch.ones(batch_size, 1, device=device)
                # 가짜 목표 레이블 0을 생성합니다.
                fake_targets = torch.zeros(batch_size, 1, device=device)
                # 판별자 기울기를 초기화합니다.
                discriminator_optimizer.zero_grad(set_to_none=True)
                # 실제 이미지 판별 결과를 계산합니다.
                real_logits = discriminator(real_images, real_labels)
                # 실제 이미지 판별 손실을 계산합니다.
                real_loss = criterion(real_logits, valid_targets)
                # 가짜 이미지용 잠재 벡터를 생성합니다.
                noise = torch.randn(batch_size, settings.latent_dim, device=device)
                # 현재 레이블 조건으로 가짜 이미지를 생성합니다.
                fake_images = generator(noise, real_labels)
                # 생성자 기울기를 차단하고 가짜 이미지 판별 결과를 계산합니다.
                fake_logits = discriminator(fake_images.detach(), real_labels)
                # 가짜 이미지 판별 손실을 계산합니다.
                fake_loss = criterion(fake_logits, fake_targets)
                # 판별자 전체 손실을 계산합니다.
                discriminator_loss = real_loss + fake_loss
                # 판별자 손실을 역전파합니다.
                discriminator_loss.backward()
                # 판별자 파라미터를 갱신합니다.
                discriminator_optimizer.step()
                # 생성자 기울기를 초기화합니다.
                generator_optimizer.zero_grad(set_to_none=True)
                # 생성자 학습용 잠재 벡터를 생성합니다.
                generator_noise = torch.randn(batch_size, settings.latent_dim, device=device)
                # 새 가짜 이미지를 생성합니다.
                generated_images = generator(generator_noise, real_labels)
                # 생성 이미지를 판별자에 전달합니다.
                generator_logits = discriminator(generated_images, real_labels)
                # 판별자를 속이기 위한 목표값 1로 생성자 손실을 계산합니다.
                generator_loss = criterion(generator_logits, valid_targets)
                # 생성자 손실을 역전파합니다.
                generator_loss.backward()
                # 생성자 파라미터를 갱신합니다.
                generator_optimizer.step()
                # 생성자 손실을 누적합니다.
                generator_loss_sum += generator_loss.item()
                # 판별자 손실을 누적합니다.
                discriminator_loss_sum += discriminator_loss.item()
                # 처리 배치 수를 증가시킵니다.
                processed_batches += 1
            # 현재 에포크 이미지 파일명을 생성합니다.
            epoch_filename = f"epoch_{epoch:03d}.png"
            # 이미지 저장 전체 경로를 생성합니다.
            epoch_path = job_directory / epoch_filename
            # 현재 생성자의 대상 숫자 이미지를 저장합니다.
            save_epoch_sample(generator, fixed_noise, target_digit, epoch_path, device)
            # 브라우저 접근용 이미지 URL을 생성합니다.
            epoch_url = f"{settings.storage_url_prefix}/generations/{job_id}/{epoch_filename}"
            # 이미지 URL을 결과 목록에 추가합니다.
            epoch_image_urls.append(epoch_url)
            # 평균 생성자 손실을 계산합니다.
            average_generator_loss = generator_loss_sum / processed_batches
            # 평균 판별자 손실을 계산합니다.
            average_discriminator_loss = discriminator_loss_sum / processed_batches
            # 현재 진행률을 정수 백분율로 계산합니다.
            progress = int(epoch / epochs * 100)
            # 프론트에서 조회할 작업 상태를 갱신합니다.
            job_manager.update(
                job_id,
                status="running",
                message=f"{epoch}/{epochs} 에포크 학습 및 이미지 저장 완료",
                current_epoch=epoch,
                progress=progress,
                epoch_images=list(epoch_image_urls),
                generator_loss=average_generator_loss,
                discriminator_loss=average_discriminator_loss,
            )
        # 최종 생성자 모델 경로를 생성합니다.
        generator_model_path = settings.model_dir / f"{job_id}_generator.pt"
        # 최종 판별자 모델 경로를 생성합니다.
        discriminator_model_path = settings.model_dir / f"{job_id}_discriminator.pt"
        # 생성자 가중치를 저장합니다.
        torch.save(generator.state_dict(), generator_model_path)
        # 판별자 가중치를 저장합니다.
        torch.save(discriminator.state_dict(), discriminator_model_path)
        # 작업 완료 상태와 최종 이미지 정보를 저장합니다.
        job_manager.update(
            job_id,
            status="completed",
            message="모든 에포크 학습과 이미지 생성을 완료했습니다.",
            progress=100,
            current_epoch=epochs,
            final_image_url=epoch_image_urls[-1],
            epoch_images=list(epoch_image_urls),
            generator_model=generator_model_path.name,
            discriminator_model=discriminator_model_path.name,
        )
    # 학습 또는 저장 중 발생한 모든 오류를 처리합니다.
    except Exception as error:
        # 프론트에서 오류를 확인할 수 있도록 실패 상태를 기록합니다.
        job_manager.update(
            job_id,
            status="failed",
            message=f"{type(error).__name__}: {error}",
            error=str(error),
        )
