from dataclasses import dataclass


@dataclass
class WatermarkConfig:
    alpha: float = 0.05
    delta: float = 36.0
    level: int = 2
    sync_seed: int = 42
    bch_enabled: bool = True
    sync_enabled: bool = True
    block_size: int = 8
    memory_pool_size: int = 4
    psnr_min: float = 40.0
    ssim_min: float = 0.98
