"""store — 보유 내역 저장소 (파일). 계좌마다 따로 저장하고, 읽을 때는 계좌별 최신 파일을 합친다.

data/snapshots/<account_id>/<YYYY-MM-DD>.csv  ← 입력 화면·register가 쓴다
스냅샷이 없는 계좌는 data/samples/**/holdings_parsed_*.csv, balance_*.csv에서 찾는다 (초기 자료).
PoC는 파일만, SQLite는 v1.5 (docs/DECISIONS.md).
"""
from __future__ import annotations

import datetime as dt
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SNAPSHOTS = ROOT / "data" / "snapshots"
SAMPLES = ROOT / "data" / "samples"


def _read(path: Path) -> pd.DataFrame:
    return pd.read_csv(path, encoding="utf-8-sig", dtype={"ticker": str})


def save_holdings(account_id: str, df: pd.DataFrame, on: dt.date | None = None) -> Path:
    on = on or dt.date.today()
    out = SNAPSHOTS / account_id / f"{on.isoformat()}.csv"
    out.parent.mkdir(parents=True, exist_ok=True)
    df = df[df["account_id"] == account_id] if "account_id" in df else df.assign(account_id=account_id)
    df.to_csv(out, index=False, encoding="utf-8-sig")
    return out


def latest_snapshot(account_id: str) -> Path | None:
    d = SNAPSHOTS / account_id
    files = sorted(d.glob("*.csv")) if d.exists() else []
    return files[-1] if files else None


def _sample_rows(account_id: str) -> pd.DataFrame | None:
    cands = sorted(SAMPLES.glob("**/holdings_parsed_*.csv")) + sorted(SAMPLES.glob("**/balance_*.csv"))
    for p in sorted(cands, key=lambda c: c.stat().st_mtime, reverse=True):
        df = _read(p)
        rows = df[df["account_id"] == account_id]
        if len(rows):
            return rows
    return None


def load_holdings(account_ids: list[str]) -> tuple[pd.DataFrame, dict[str, str]]:
    """계좌별 최신 보유 내역을 합쳐 돌려준다. 두 번째 값은 계좌 → 출처(파일 경로 또는 '없음')."""
    frames, sources = [], {}
    for acct in account_ids:
        p = latest_snapshot(acct)
        if p is not None:
            frames.append(_read(p)); sources[acct] = str(p.relative_to(ROOT))
            continue
        rows = _sample_rows(acct)
        if rows is not None:
            frames.append(rows); sources[acct] = "data/samples (초기 자료)"
        else:
            sources[acct] = "없음"
    df = pd.concat(frames, ignore_index=True) if frames else pd.DataFrame(columns=["account_id", "ticker_name", "ticker", "qty", "price"])
    if len(df):
        df["qty"] = df["qty"].astype(int); df["price"] = df["price"].astype(int)
    return df, sources
