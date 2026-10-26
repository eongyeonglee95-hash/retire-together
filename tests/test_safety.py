"""SAFE-01 — 저장 경로·계좌·수량·가격·합계 재검증 (docs/AGENT_DESIGN.md §0, ARCHITECTURE_REVIEW §4 P0).
각 테스트는 보고서의 합성 입력을 그대로 재현한다. 고치기 전에는 실패해야 한다."""
import datetime as dt
from pathlib import Path

import pandas as pd
import pytest

from tools import store
from tools.assets import tag_holdings
from tools.parse_balance import load_holdings_csv, reconcile, validate_holdings
from tools.rebalance import compute_rebalance
from tools.strategy import Strategy

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "data" / "fixtures" / "holdings_fixture.csv"
STRAT = Strategy(id="t", name="t", targets={"stock": 0.3, "long_bond": 0.4, "mid_bond": 0.15, "gold": 0.075, "commodity": 0.075},
                 threshold=0.05, min_trade_krw=100_000)


def _csv(tmp_path: Path, text: str) -> Path:
    p = tmp_path / "h.csv"
    p.write_text(text, encoding="utf-8-sig")
    return p


# ---- 수량·가격: 음수·소수·0·빈 종목명·이상한 계좌 ID는 행별 오류로 거부 ----
def test_csv_rejects_negative_fraction_zero_and_bad_ids(tmp_path):
    p = _csv(tmp_path, "account_id,ticker_name,ticker,qty,price\n"
                       "acct_a,X,1,-2,100\n"       # 음수 수량
                       "acct_a,Y,2,1.9,100\n"      # 소수 수량 (예전엔 1로 잘림)
                       "acct_a,Z,3,1,0\n"          # 가격 0
                       "acct_a,,4,1,100\n"         # 종목명 없음
                       "../outside,W,5,1,100\n")   # 경로 문자가 든 계좌 ID
    with pytest.raises(ValueError) as e:
        load_holdings_csv(p)
    msg = str(e.value)
    assert "2행" in msg and "qty" in msg          # 음수
    assert "3행" in msg                            # 소수
    assert "4행" in msg and "price" in msg        # 0
    assert "5행" in msg and "ticker_name" in msg  # 빈 종목명
    assert "6행" in msg and "account_id" in msg   # 계좌 ID 형식


def test_csv_rejects_duplicate_rows_and_accepts_clean(tmp_path):
    dup = _csv(tmp_path, "account_id,ticker_name,ticker,qty,price\nacct_a,X,1,1,100\nacct_a,X,1,2,100\n")
    with pytest.raises(ValueError, match="중복"):
        load_holdings_csv(dup)
    df = load_holdings_csv(FIXTURE)
    assert df["qty"].dtype.kind == "i" and (df["qty"] > 0).all() and (df["price"] > 0).all()
    assert validate_holdings(df) == []


# ---- 합계 대조: 수량×가격으로 계산하고, 전사한 value가 그것과 다르면 '일치'라고 하지 않는다 ----
def test_reconcile_uses_qty_times_price_not_transcribed_value():
    rows = pd.DataFrame({"account_id": ["a"], "ticker_name": ["X"], "ticker": ["1"], "qty": [1], "price": [100], "value": [10_000]})
    r = reconcile(rows, 10_000)
    assert r.verified and not r.ok           # 예전엔 (True, 0)으로 통과했던 입력
    assert r.computed == 100 and r.diff == 100 - 10_000 and r.value_diff == 10_000 - 100
    good = rows.assign(value=[100])
    assert reconcile(good, 100).ok
    # 화면 합계가 없으면 '검증 불가'이지 '일치'가 아니다
    r2 = reconcile(good, 0)
    assert not r2.verified and not r2.ok


# ---- 저장: 계좌 ID는 등록·활성 계좌만, 경로 문자 금지, 빈 표 거부, 스냅샷 폴더 밖 쓰기 금지 ----
def test_save_holdings_rejects_traversal_unregistered_inactive_and_empty(tmp_path, monkeypatch):
    monkeypatch.setattr(store, "SNAPSHOTS", tmp_path / "snap")
    accounts = {"a": {"active": True}, "off": {"active": False}}
    df = pd.DataFrame({"account_id": ["a"], "ticker_name": ["X"], "ticker": ["1"], "qty": [1], "price": [100]})
    with pytest.raises(ValueError, match="계좌 ID"):
        store.save_holdings("../outside", df, accounts=accounts)
    assert not (tmp_path / "outside").exists() and not list(tmp_path.glob("*.csv"))
    with pytest.raises(ValueError, match="등록"):
        store.save_holdings("ghost", df, accounts=accounts)
    with pytest.raises(ValueError, match="사용 안 함"):
        store.save_holdings("off", df.assign(account_id="off"), accounts=accounts)
    # A 계좌 표를 B로 저장 → 필터 후 0행 → 거부 (예전엔 0행 CSV가 생김)
    with pytest.raises(ValueError, match="행이 없"):
        store.save_holdings("a", df.assign(account_id="b"), accounts={"a": {}, "b": {}})
    with pytest.raises(ValueError, match="qty"):
        store.save_holdings("a", df.assign(qty=[-1]), accounts=accounts)
    out = store.save_holdings("a", df, on=dt.date(2026, 1, 1), accounts=accounts)
    assert out == tmp_path / "snap" / "a" / "2026-01-01.csv" and out.exists()


# ---- 계산: 계좌 목록에 없거나 사용 안 함인 계좌의 보유분은 주문표를 만들지 않는다 ----
def test_unknown_or_inactive_account_blocks_orders():
    h, _ = tag_holdings(load_holdings_csv(FIXTURE))
    only_a = {"acct_a": {"account_type": "pension_savings"}}          # acct_b 미등록
    r = compute_rebalance(h, STRAT, accounts=only_a)
    assert r.blocked_reason and "acct_b" in r.blocked_reason and r.orders == []
    inactive = {"acct_a": {"account_type": "pension_savings"}, "acct_b": {"account_type": "pension_savings", "active": False}}
    r2 = compute_rebalance(h, STRAT, accounts=inactive)
    assert r2.blocked_reason and "acct_b" in r2.blocked_reason
    ok = {"acct_a": {"account_type": "pension_savings"}, "acct_b": {"account_type": "pension_savings", "active": True}}
    assert compute_rebalance(h, STRAT, accounts=ok).blocked_reason is None
