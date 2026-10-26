"""compute_rebalance — 순수 함수. docs/CALCULATION_RULES.md §1~3, REBALANCING_RULES.md §1-1·§2.

입력: 태깅된 보유 내역(account_id, ticker_name, ticker, qty, price, asset_class), 계좌별 예수금,
      신규 납입(금액·계좌), 전략.
출력: docs/AGENT_DESIGN.md "compute_rebalance 출력" 데이터 계약 (dict).

원칙
- 비중·편차·발동은 같은 풀의 계좌를 **합산**해서 본다. 주문은 **계좌별**로 낸다 (계좌 간 자금 이동 불가).
- 임계치를 넘은 자산군만 거래한다. 신규 납입은 매도 없이 부족한 자산군 매수에 먼저 쓴다.
- 매도 → 매수 순서. 계좌 예수금이 부족하면 매수 수량을 줄이고 표시한다.
- LLM은 이 함수를 실행하지 않는다. 같은 입력이면 같은 출력.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field

import pandas as pd

from tools.assets import ConstraintResult, check_constraints
from tools.strategy import CLASS_LABELS, Strategy


@dataclass
class NewCash:
    amount: int
    account_id: str


@dataclass
class Order:
    side: str            # "매도" | "매수" | "생략"
    asset_class: str
    account_id: str
    ticker_name: str | None
    ticker: str | None
    qty: int | None
    amount: int          # 양수. 매도는 유입, 매수는 유출
    note: str


@dataclass
class RebalanceResult:
    mode: str
    strategy_id: str
    strategy_name: str
    threshold: float
    min_trade_krw: int
    total_value: int                 # 보유 + 예수금
    new_cash: int
    total_after_cash: int            # total_value + new_cash  (T')
    classes: list[dict]              # 자산군별 target/current/deviation_pp/value/over_threshold
    triggered: bool
    constraints: list[ConstraintResult]
    orders: list[Order]
    explain_inputs: dict
    blocked_reason: str | None = None
    notes: list[str] = field(default_factory=list)

    def orders_df(self) -> pd.DataFrame:
        return pd.DataFrame([o.__dict__ for o in self.orders])


def _class_values(holdings: pd.DataFrame) -> dict[str, int]:
    v = holdings.assign(value=holdings["qty"] * holdings["price"]).groupby("asset_class")["value"].sum()
    return {k: int(x) for k, x in v.items()}


def compute_rebalance(
    holdings: pd.DataFrame,
    strategy: Strategy,
    cash_by_account: dict[str, int] | None = None,
    new_cash: NewCash | None = None,
    accounts: dict[str, dict] | None = None,
    mode: str = "rebalance",
) -> RebalanceResult:
    """mode: "rebalance" = 매도·매수 / "buy_only" = 매도 없이 납입금·예수금으로 부족한 자산군만 매수."""
    if mode not in ("rebalance", "buy_only"):
        raise ValueError(f"알 수 없는 mode: {mode}")
    cash_by_account = dict(cash_by_account or {})
    h = holdings.copy()
    h["value"] = (h["qty"] * h["price"]).astype(int)

    # ---- 제약 검증 (실패 시 주문표 없음) ----
    constraints = check_constraints(h, accounts)
    blocked = [c for c in constraints if not c.passed]

    # ---- 합산 비중·편차 ----
    class_vals = _class_values(h) if not blocked else {}
    cash_total = sum(cash_by_account.values())
    T = sum(class_vals.values()) + cash_total
    C = new_cash.amount if new_cash else 0
    T2 = T + C
    classes = []
    for cls, t in strategy.targets.items():
        a = class_vals.get(cls, 0) + (cash_total if cls == "cash" else 0)
        w = a / T if T else 0.0
        d = w - t
        classes.append({
            "asset_class": cls, "label": CLASS_LABELS.get(cls, cls),
            "target": t, "current": w, "deviation_pp": round(d * 100, 2),
            "value": a, "over_threshold": abs(d) > strategy.threshold + 1e-12,
        })
    # 전략에 없는 자산군을 들고 있으면 (예: 전략이 금을 안 쓰는데 금 보유) 편차 = 전부 초과
    for cls, a in class_vals.items():
        if cls not in strategy.targets and cls != "cash":
            w = a / T if T else 0.0
            classes.append({"asset_class": cls, "label": CLASS_LABELS.get(cls, cls), "target": 0.0,
                            "current": w, "deviation_pp": round(w * 100, 2), "value": a,
                            "over_threshold": w > strategy.threshold})
    triggered = any(c["over_threshold"] for c in classes)

    # ---- 설명용 수치 (§3) ----
    shock = strategy.shock
    L_now = sum(c["current"] * shock.get(c["asset_class"], 0.0) for c in classes) * T
    L_target = sum(c["target"] * shock.get(c["asset_class"], 0.0) for c in classes) * T
    worst = max(classes, key=lambda c: abs(c["deviation_pp"])) if classes else None
    explain_inputs = {
        "loss_now": int(round(-L_now)), "loss_target": int(round(-L_target)),
        "loss_diff": int(round(-L_now + L_target)),
        "worst_class": worst["label"] if worst else None,
        "worst_deviation_pp": worst["deviation_pp"] if worst else None,
        "tax_deferred": True,
    }

    result = RebalanceResult(
        mode=mode,
        strategy_id=strategy.id, strategy_name=strategy.name, threshold=strategy.threshold,
        min_trade_krw=strategy.min_trade_krw, total_value=int(T), new_cash=C, total_after_cash=int(T2),
        classes=classes, triggered=triggered, constraints=constraints, orders=[],
        explain_inputs=explain_inputs,
    )
    if blocked:
        result.blocked_reason = " / ".join(f"{c.name}: {c.detail}" for c in blocked)
        return result
    if not triggered and C == 0 and cash_total == 0:
        result.notes.append("모든 자산군이 임계치 안. 이번엔 거래 없음")
        return result
    if mode == "buy_only" and C == 0 and cash_total == 0:
        result.notes.append("매수만 모드: 납입금·예수금이 없어 이번엔 거래 없음" + (" (편차는 임계치 초과)" if triggered else ""))
        return result

    # ---- 주문 (계좌별) ----
    orders: list[Order] = []
    acct_cash = {a: int(v) for a, v in cash_by_account.items()}
    if new_cash:
        acct_cash[new_cash.account_id] = acct_cash.get(new_cash.account_id, 0) + C

    targets = {c["asset_class"]: c["target"] for c in classes if c["asset_class"] != "cash"}
    goal = {cls: t * T2 for cls, t in targets.items()}              # G_i
    have = {cls: class_vals.get(cls, 0) for cls in targets}
    over = {c["asset_class"] for c in classes if c["over_threshold"] and c["asset_class"] != "cash"}

    # 1) 매도: 임계치를 넘은 초과 자산군만, 보유 계좌별로 비례 매도 (buy_only 모드는 매도 없음)
    for cls in (sorted(over) if mode == "rebalance" else []):
        excess = have[cls] - goal[cls]
        if excess <= 0:
            continue
        rows = h[h["asset_class"] == cls].sort_values("value", ascending=False)
        cls_total = int(rows["value"].sum())
        for _, r in rows.iterrows():
            amt = excess * r["value"] / cls_total
            qty = int(math.floor(amt / r["price"]))
            amt_i = qty * int(r["price"])
            if amt_i < strategy.min_trade_krw or qty <= 0:
                orders.append(Order("생략", cls, r["account_id"], r["ticker_name"], r.get("ticker"), None, int(amt),
                                    "최소 거래 금액 미만"))
                continue
            orders.append(Order("매도", cls, r["account_id"], r["ticker_name"], r.get("ticker"), qty, amt_i,
                                f"편차 {[c for c in classes if c['asset_class']==cls][0]['deviation_pp']:+.1f}%p"))
            acct_cash[r["account_id"]] = acct_cash.get(r["account_id"], 0) + amt_i
            have[cls] -= amt_i

    # 2) 매수: 부족한 자산군에, 계좌별 가용 현금 안에서 부족분 비례 배분
    short = {cls: goal[cls] - have[cls] for cls in targets if goal[cls] - have[cls] > 0}
    for acct, cash in sorted(acct_cash.items()):
        if cash <= 0 or not short:
            continue
        total_short = sum(short.values())
        spend = min(cash, total_short)
        for cls in sorted(short, key=lambda k: -short[k]):
            if short[cls] <= 0:
                continue
            amt = spend * short[cls] / total_short
            rows = h[(h["asset_class"] == cls) & (h["account_id"] == acct)].sort_values("value", ascending=False)
            if len(rows) == 0:
                # 이 계좌에 해당 자산군 종목이 없음 → 종목은 사용자가 정한다
                orders.append(Order("매수", cls, acct, None, None, None, int(amt),
                                    "이 계좌에 해당 자산군 종목 없음 — 종목 지정 필요 (asset_map.yaml)"))
                short[cls] -= amt
                acct_cash[acct] -= amt
                continue
            r = rows.iloc[0]
            qty = int(math.floor(amt / r["price"]))
            amt_i = qty * int(r["price"])
            if amt_i < strategy.min_trade_krw or qty <= 0:
                orders.append(Order("생략", cls, acct, r["ticker_name"], r.get("ticker"), None, int(amt),
                                    "최소 거래 금액 미만"))
                continue
            note = f"편차 {[c for c in classes if c['asset_class']==cls][0]['deviation_pp']:+.1f}%p"
            if new_cash and acct == new_cash.account_id:
                note += f" · 납입금 {C:,}원 포함"
            orders.append(Order("매수", cls, acct, r["ticker_name"], r.get("ticker"), qty, amt_i, note))
            short[cls] -= amt_i
            acct_cash[acct] -= amt_i
            have[cls] += amt_i

    # 3) 임계치 안이라 건드리지 않은 자산군은 "생략" 한 줄로
    untouched = [c for c in classes if not c["over_threshold"] and c["asset_class"] != "cash"
                 and not any(o.asset_class == c["asset_class"] and o.side != "생략" for o in orders)]
    if untouched:
        orders.append(Order("생략", ",".join(c["asset_class"] for c in untouched), "", None, None, None, 0,
                            "임계치 미만 · " + " · ".join(c["label"] for c in untouched)))

    leftover = {a: int(v) for a, v in acct_cash.items() if v >= strategy.min_trade_krw}
    if leftover:
        result.notes.append("매수 후 남는 예수금: " + ", ".join(f"{a} {v:,}원" for a, v in leftover.items()))
    remaining_short = {cls: int(v) for cls, v in short.items() if v >= strategy.min_trade_krw}
    if remaining_short:
        result.notes.append("현금 부족으로 목표에 못 미친 자산군: " +
                            ", ".join(f"{CLASS_LABELS.get(k,k)} {v:,}원" for k, v in remaining_short.items()))
    # 매도 먼저, 그다음 매수, 생략은 끝에
    order_rank = {"매도": 0, "매수": 1, "생략": 2}
    result.orders = sorted(orders, key=lambda o: (order_rank[o.side], o.account_id, -o.amount))
    return result
