"""Small, strict TOML configuration with no optional framework dependency."""

import math
import tomllib
from dataclasses import asdict, dataclass, fields
from pathlib import Path


@dataclass(frozen=True)
class ExperimentConfig:
    dataset: str = "data/processed/dev_set.json"
    limit: int = 3
    k: int = 5
    short_pool_policy: str = "use_all"
    alpha: float = 1.0
    beta: float = 0.2
    seed: int = 42
    device: str = "cpu"
    threads: int = 4
    local_files_only: bool = True
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    embedding_revision: str = "1110a243fdf4706b3f48f1d95db1a4f5529b4d41"
    generator_model: str = "Qwen/Qwen2.5-1.5B-Instruct"
    generator_revision: str = "989aa7980e4cf806f80c7fef2b1adb7bc71aa306"
    embedding_truncation: str = "error"
    max_input_tokens: int = 4096
    max_new_tokens: int = 32
    solver_time_limit: float = 10.0
    generator_dtype: str = "float32"

    def __post_init__(self) -> None:
        for name in ("limit", "k", "threads", "max_input_tokens", "max_new_tokens"):
            if type(getattr(self, name)) is not int or getattr(self, name) <= 0:
                raise ValueError(f"{name} must be a positive integer")
        if type(self.seed) is not int or not 0 <= self.seed < 2**32:
            raise ValueError("seed must be an integer in [0, 2**32)")
        if type(self.local_files_only) is not bool:
            raise ValueError("local_files_only must be boolean")
        for name in ("alpha", "beta", "solver_time_limit"):
            value = getattr(self, name)
            if type(value) not in (int, float) or not math.isfinite(value) or value < 0:
                raise ValueError(f"{name} must be finite and nonnegative")
        if self.solver_time_limit == 0:
            raise ValueError("solver_time_limit must be positive")
        if self.device not in {"cpu", "cuda", "auto"}:
            raise ValueError("device must be cpu, cuda or auto")
        if self.generator_dtype not in {"float32", "float16", "bfloat16"}:
            raise ValueError("generator_dtype must be float32, float16 or bfloat16")
        if self.short_pool_policy not in {"error", "use_all"}:
            raise ValueError("short_pool_policy must be error or use_all")
        if self.embedding_truncation not in {"error", "report"}:
            raise ValueError("embedding_truncation must be error or report")
        for name in ("dataset", "embedding_model", "generator_model"):
            if (
                not isinstance(getattr(self, name), str)
                or not getattr(self, name).strip()
            ):
                raise ValueError(f"{name} must be a nonempty string")
        for name in ("embedding_revision", "generator_revision"):
            value = getattr(self, name)
            if (
                not isinstance(value, str)
                or len(value) != 40
                or any(ch not in "0123456789abcdef" for ch in value)
            ):
                raise ValueError(f"{name} must be an immutable 40-character commit")

    def as_dict(self) -> dict:
        return asdict(self)


def load_config(path: Path) -> ExperimentConfig:
    raw = tomllib.loads(path.read_text(encoding="utf-8"))
    unknown = set(raw) - {field.name for field in fields(ExperimentConfig)}
    if unknown:
        raise ValueError(f"Unknown configuration keys: {sorted(unknown)}")
    return ExperimentConfig(**raw)
