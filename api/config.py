from dataclasses import dataclass
from typing import Dict
from pathlib import Path
import yaml

@dataclass(frozen=True)
class ExperimentCfg:
    key: str
    name: str
    enabled: bool
    allocation: Dict[str, int]
    targeting: Dict[str, object]

@dataclass(frozen=True)
class AppConfig:
    experiments: Dict[str, ExperimentCfg]

def load_config(path: str | None = None) -> AppConfig:
    cfg_path = Path(path or Path(__file__).parent / "experiments.yaml")
    with open(cfg_path, "r") as f:
        raw = yaml.safe_load(f)
    exps: Dict[str, ExperimentCfg] = {}
    for e in raw.get("experiments", []):
        exps[e["key"]] = ExperimentCfg(
            key=e["key"],
            name=e.get("name", e["key"]),
            enabled=bool(e.get("enabled", True)),
            allocation=e.get("allocation", {"A": 50, "B": 50}),
            targeting=e.get("targeting", {}),
        )
    return AppConfig(experiments=exps)

def pick_variant_by_bucket(buckets: Dict[str, int], bucket_value: int) -> str:
    cumulative = 0
    for variant, pct in buckets.items():
        if pct < 0:
            raise ValueError("Allocation percent must be >= 0")
        cumulative += pct
        if bucket_value < cumulative:
            return variant
    return list(buckets.keys())[-1]
