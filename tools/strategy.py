"""load_strategy — rules/strategies.yaml에서 전략(목표 비율·임계치·최소 거래)과 가정 하락장을 읽는다.

비율 숫자의 단일 원천은 YAML이다 (docs/REBALANCING_RULES.md §1).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
STRATEGIES_PATH = ROOT / "rules" / "strategies.yaml"

ASSET_CLASSES = ("stock", "long_bond", "mid_bond", "gold", "commodity", "cash")
CLASS_LABELS = {
    "stock": "주식", "long_bond": "장기채", "mid_bond": "중기채",
    "gold": "금", "commodity": "원자재", "cash": "현금",
}


@dataclass(frozen=True)
class Strategy:
    id: str
    name: str
    targets: dict[str, float]          # 자산군 → 목표 비중 (0~1, 합 1)
    threshold: float                   # 발동 임계치 (절대, 0.05 = ±5%p)
    min_trade_krw: int
    shock: dict[str, float] = field(default_factory=dict)  # 가정 하락장 수익률


def load_strategy(strategy_id: str, path: Path = STRATEGIES_PATH) -> Strategy:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    raw = data["strategies"].get(strategy_id)
    if raw is None:
        raise KeyError(f"전략 '{strategy_id}' 이(가) {path.name}에 없음")
    targets_pct = raw.get("targets") or {}
    if not targets_pct:
        raise ValueError(f"전략 '{strategy_id}'의 targets가 비어 있음 (직접 설정은 비율을 먼저 채워야 함)")
    total = sum(targets_pct.values())
    if abs(total - 100) > 1e-6:
        raise ValueError(f"전략 '{strategy_id}' 비율 합계가 100이 아님: {total}")
    unknown = set(targets_pct) - set(ASSET_CLASSES)
    if unknown:
        raise ValueError(f"알 수 없는 자산군: {sorted(unknown)}")
    return Strategy(
        id=strategy_id,
        name=raw.get("name", strategy_id),
        targets={k: v / 100.0 for k, v in targets_pct.items()},
        threshold=float(raw.get("threshold_pp", 5)) / 100.0,
        min_trade_krw=int(raw.get("min_trade_krw", 100_000)),
        shock={k: float(v) for k, v in (data.get("shock") or {}).items()},
    )


def list_strategies(path: Path = STRATEGIES_PATH) -> list[tuple[str, str]]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    return [(k, v.get("name", k)) for k, v in data["strategies"].items()]
