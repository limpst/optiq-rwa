"""Project settings from .env (gitignored) / environment. No third-party deps.

Never print DERIBIT_CLIENT_SECRET. The paper engine never needs the key:
all market data comes from public endpoints.
"""
from __future__ import annotations

import os
import pathlib
from dataclasses import dataclass

ROOT = pathlib.Path(__file__).resolve().parents[2]


def load_dotenv(path: pathlib.Path | None = None) -> None:
    p = path or ROOT / ".env"
    if not p.exists():
        return
    for line in p.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


load_dotenv()


@dataclass(frozen=True)
class Settings:
    db_path: pathlib.Path = ROOT / os.environ.get("OPTIQ_DB", "data/optiq.db")
    parquet_dir: pathlib.Path = ROOT / os.environ.get("OPTIQ_PARQUET_DIR", "data/parquet")
    min_daily_volume_krw: float = float(os.environ.get("OPTIQ_MIN_DAILY_VOLUME_KRW", 1e9))
    usdkrw: float = float(os.environ.get("OPTIQ_USDKRW", 1400))
    # bases always snapshotted at order-book depth even if below the volume filter
    focus_bases: tuple = tuple(os.environ.get("OPTIQ_FOCUS_BASES", "SOL_USDC").split(","))
    rwa_rate: float = float(os.environ.get("OPTIQ_RWA_RATE", 0.045))
    deribit_client_id: str = os.environ.get("DERIBIT_CLIENT_ID", "")

    @property
    def min_daily_volume_usd(self) -> float:
        return self.min_daily_volume_krw / self.usdkrw


SETTINGS = Settings()
