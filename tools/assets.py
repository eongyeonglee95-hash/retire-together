"""tag_assets — 종목 → 자산군 태그. rules/asset_map.yaml이 원천.

미등록 종목은 여기서 분류하지 않는다 (LLM 제안 → 사용자 확인 → YAML 저장은 Agent 단계).
제도 제약 검증(연금저축: 레버리지·인버스 불가)도 여기서 한다 — deterministic.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

import pandas as pd
import yaml

ROOT = Path(__file__).resolve().parents[1]
ASSET_MAP_PATH = ROOT / "rules" / "asset_map.yaml"
ACCOUNTS_PATH = ROOT / "rules" / "accounts.yaml"

# 연금저축·IRP에서 담을 수 없는 상품의 이름 패턴 (KRX 상장 ETF 명명 규칙 기준)
LEVERAGE_INVERSE_PATTERN = re.compile(r"레버리지|인버스|2X|3X|곱버스|-1X|-2X", re.IGNORECASE)


@dataclass(frozen=True)
class ConstraintResult:
    name: str
    passed: bool
    detail: str


def load_asset_map(path: Path = ASSET_MAP_PATH) -> dict[str, dict]:
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return data.get("assets") or {}


def load_accounts(path: Path = ACCOUNTS_PATH) -> dict[str, dict]:
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return {a["id"]: a for a in data.get("accounts", [])}


def load_pools(path: Path = ACCOUNTS_PATH) -> dict[str, dict]:
    """pool id → {label, strategy, accounts: [account ids]}. 풀 = 리밸런싱 단위."""
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    pools = {k: dict(v, accounts=[]) for k, v in (data.get("pools") or {}).items()}
    for a in data.get("accounts", []):
        pid = a.get("pool")
        if pid:
            pools.setdefault(pid, {"label": pid, "strategy": None, "accounts": []})["accounts"].append(a["id"])
    return pools


def tag_holdings(holdings: pd.DataFrame, asset_map: dict[str, dict] | None = None) -> tuple[pd.DataFrame, list[str]]:
    """holdings에 asset_class 열을 붙인다. 매핑에 없는 종목명 목록을 함께 돌려준다.

    매핑 키는 종목명(캡처에 보이는 이름). 티커로도 찾는다.
    """
    amap = load_asset_map() if asset_map is None else asset_map
    by_ticker = {v.get("ticker"): v for v in amap.values() if v.get("ticker")}
    out = holdings.copy()
    classes, unmapped = [], []
    for _, row in out.iterrows():
        entry = amap.get(row["ticker_name"]) or by_ticker.get(str(row.get("ticker", "")))
        if entry is None:
            classes.append(None)
            unmapped.append(row["ticker_name"])
        else:
            classes.append(entry["asset_class"])
    out["asset_class"] = classes
    return out, sorted(set(unmapped))


def check_constraints(holdings: pd.DataFrame, accounts: dict[str, dict] | None = None) -> list[ConstraintResult]:
    """계좌 종류별 제도 제약. 하나라도 실패하면 주문표를 만들지 않는다."""
    accts = load_accounts() if accounts is None else accounts
    results: list[ConstraintResult] = []

    bad = holdings[holdings["ticker_name"].str.contains(LEVERAGE_INVERSE_PATTERN)]
    pension_bad = bad[bad["account_id"].map(lambda a: accts.get(a, {}).get("account_type") in ("pension_savings", "irp"))]
    if len(pension_bad):
        names = ", ".join(pension_bad["ticker_name"].unique())
        results.append(ConstraintResult("연금계좌 레버리지·인버스 없음", False, f"연금저축/IRP 불가 종목: {names}"))
    else:
        results.append(ConstraintResult("연금계좌 레버리지·인버스 없음", True, "통과"))

    untagged = holdings[holdings["asset_class"].isna()] if "asset_class" in holdings else holdings
    if len(untagged):
        results.append(ConstraintResult("모든 종목 자산군 태깅", False, "미분류: " + ", ".join(untagged["ticker_name"].unique())))
    else:
        results.append(ConstraintResult("모든 종목 자산군 태깅", True, "통과"))

    # IRP 위험자산 70% 한도 — IRP 계좌가 활성화되면 검증 (회의 후). 지금은 항목만 둔다
    return results
