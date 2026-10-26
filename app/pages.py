"""화면별 그리기 함수. 샘플 숫자는 docs/SCREEN_REFERENCE.md 컨셉 이미지 기준. 실제 숫자는 tools/에서."""
from __future__ import annotations

import streamlit as st

# 컨셉 이미지의 샘플 숫자 (회의용). 실제 연동은 v1.5
SAMPLE = {
    "부부 전체": {"total": 12_8450, "pension": 4_2300, "cash": 8_6150, "pension_pct": 33, "cash_pct": 67, "delta": "+3.2%"},
    "나":        {"total": 6_2500,  "pension": 2_0500, "cash": 4_2000, "pension_pct": 33, "cash_pct": 67, "delta": "+2.9%"},
    "배우자":    {"total": 6_5950,  "pension": 2_1800, "cash": 4_4150, "pension_pct": 33, "cash_pct": 67, "delta": "+3.5%"},
}


def _won(man: int) -> str:
    eok, rest = divmod(man, 10_000)
    return (f"{eok}억 " if eok else "") + (f"{rest:,}만원" if rest else "원")


def home(view: str) -> None:
    d = SAMPLE[view]
    st.caption("지금의 선택이, 10년 후의 삶을 만듭니다. (샘플 숫자 — 실제 연동은 다음 단계)")
    c1, c2, c3 = st.columns(3)
    c1.metric("총 자산", _won(d["total"]), d["delta"] + " 전분기 대비")
    c2.metric("노후 주머니 (연금)", _won(d["pension"]), f"{d['pension_pct']}%")
    c3.metric("갈아타기 주머니 (현금)", _won(d["cash"]), f"{d['cash_pct']}%")

    st.subheader("이번 달 제안")
    a, b = st.columns(2)
    with a:
        st.warning("**리밸런싱이 필요해요** — 연금저축(구) 주식 비중이 목표보다 높아요. 리밸런싱 메뉴에서 주문표를 확인하세요.")
    with b:
        st.info("**IRP 세액공제 한도 300만원 남았어요** — 올해 안에 납입하면 매수만 모드로 자동 배분 제안을 받을 수 있어요.")

    st.subheader("이번 달 체크리스트")
    st.checkbox("연금 납입 확인하기", value=True)
    st.checkbox("연금저축 리밸런싱 검토", value=False)
    st.checkbox("대출 상환 계획 점검", value=False)


def pension(view: str) -> None:
    st.caption("부부 각자의 4층 석탑과 '우리 집 예상 월 수령액'. (샘플 — 계산은 3단계 Pension Payout Simulator)")
    left, right = st.columns([2, 1])
    layers = [("4층 ISA → 연금계좌", 0.3), ("3층 개인연금 (연금저축·연금보험)", 0.6), ("2층 퇴직연금 (DB·DC·IRP)", 0.8), ("1층 국민연금", 1.0)]
    with left:
        for label, width in layers:
            st.progress(width, text=label)
        st.caption("막대 길이는 샘플. 층별 월 수령액 입력 → CALCULATION_RULES §4 공식으로 계산 예정")
    with right:
        st.metric("우리 집 예상 월 수령액", "— 만원", "55세 사적연금 개시, 65세 국민연금 (기본값)")
        st.slider("수익률 가정 (%)", 0.0, 10.0, 5.0, 0.5)
        st.slider("물가 가정 (%)", 0.0, 5.0, 2.0, 0.5)
        st.slider("수령 종료 나이", 80, 100, 90)


def _default_holdings_path():
    """data/samples 아래 가장 최근 *_parsed_*.csv 또는 balance_*.csv (git 제외 폴더)."""
    from pathlib import Path
    root = Path(__file__).resolve().parents[1]
    cands = sorted(root.glob("data/samples/**/holdings_parsed_*.csv")) + sorted(root.glob("data/samples/**/balance_*.csv"))
    return cands[-1] if cands else None


def rebalancing(view: str) -> None:
    import pandas as pd
    from tools import explain, order_sheet
    from tools.assets import defaults_with_prices, load_accounts, load_pools, tag_holdings
    from tools.decisions import read_decisions, record_decision
    from tools.parse_balance import load_holdings_csv
    from tools.rebalance import NewCash, compute_rebalance
    from tools.strategy import list_strategies, load_strategy

    accounts = load_accounts()
    pools = load_pools()
    labels = {k: v.get("label", k) for k, v in accounts.items()}

    # ---- 머리글: 풀 · 전략 · 납입 · 데이터 ----
    top = st.columns([2, 2, 2, 2])
    pool_id = top[0].selectbox("풀 (합산 단위)", list(pools), format_func=lambda k: pools[k].get("label", k))
    pool = pools[pool_id]
    strategies = list_strategies()
    strat_ids = [k for k, _ in strategies]
    default_idx = strat_ids.index(pool.get("strategy")) if pool.get("strategy") in strat_ids else 0
    strategy_id = top[1].selectbox("전략", strat_ids, index=default_idx, format_func=lambda k: dict(strategies)[k])
    mode = top[2].radio("모드", ["rebalance", "buy_only"], index=0 if pool.get("mode", "rebalance") == "rebalance" else 1,
                        format_func=lambda m: "리밸런싱 (매도·매수)" if m == "rebalance" else "매수만 (납입금으로)", horizontal=True)
    new_cash_amt = top[3].number_input("신규 납입 (원)", min_value=0, step=100_000, value=0)

    uploaded = st.file_uploader("보유 내역 CSV (비우면 data/samples의 최근 파일)", type=["csv"])
    path = uploaded if uploaded is not None else _default_holdings_path()
    if path is None:
        st.warning("보유 내역이 없어요. 입력 메뉴에서 캡처를 등록하거나 CSV를 올려 주세요.")
        return
    holdings = load_holdings_csv(path)
    holdings = holdings[holdings["account_id"].isin(pool["accounts"])].reset_index(drop=True)
    if holdings.empty:
        st.warning("이 풀의 계좌에 해당하는 보유 내역이 없어요.")
        return
    if st.toggle("현재가를 공개 시세로 갱신", value=False):
        from tools.market import fetch_prices
        try:
            prices = fetch_prices(list(holdings["ticker"].dropna().unique()))
            holdings["price"] = holdings["ticker"].map(prices).fillna(holdings["price"]).astype(int)
            st.caption("현재가: 네이버 금융 기준 방금 갱신")
        except Exception as e:  # 네트워크 없으면 스냅샷 가격
            st.caption(f"현재가 조회 실패({e}) → 파일의 스냅샷 가격")
    holdings, unmapped = tag_holdings(holdings)
    if unmapped:
        st.error("자산군 미분류 종목: " + ", ".join(unmapped) + " → rules/asset_map.yaml에 추가 필요")

    try:
        strategy = load_strategy(strategy_id)
    except ValueError as e:
        st.error(str(e))
        return
    new_cash = NewCash(int(new_cash_amt), pool["accounts"][0]) if new_cash_amt else None
    defaults = defaults_with_prices(holdings, live=True)
    r = compute_rebalance(holdings, strategy, new_cash=new_cash, accounts=accounts, mode=mode, defaults=defaults)
    last = read_decisions()

    # ---- 경고 배너 + 왜 지금 + 총 평가액 ----
    b1, b2 = st.columns([4, 1])
    with b1:
        if r.blocked_reason:
            st.error("**" + explain.headline(r) + "**")
        elif r.triggered:
            st.warning("**" + explain.headline(r) + "**\n\n" + explain.why_now(r, last[-2:]))
        else:
            st.success("**" + explain.headline(r) + "**\n\n" + explain.why_now(r, last[-2:]))
    with b2:
        st.metric("총 평가액", f"{r.total_value/10_000:,.0f}만원", f"납입 {r.new_cash:,}원 포함" if r.new_cash else None)

    # ---- 목표 vs 현재 ----
    st.subheader("목표 vs 현재")
    chart = pd.DataFrame({"자산군": [c["label"] for c in r.classes],
                          "목표": [round(c["target"] * 100, 1) for c in r.classes],
                          "현재": [round(c["current"] * 100, 1) for c in r.classes]}).set_index("자산군")
    st.bar_chart(chart, stack=False, height=220)
    st.dataframe(order_sheet.classes_table(r), hide_index=True, use_container_width=True)
    st.caption(f"발동 기준 ±{r.threshold*100:.0f}%p · 임계치를 넘은 자산군만 거래 · 제도 검증: " +
               " / ".join(f"{c.name} {'✓' if c.passed else '✗'}" for c in r.constraints))

    # ---- 주문표 ----
    st.subheader("주문표")
    st.caption("매도 먼저, 그다음 매수 · 납입금은 매수에 먼저 사용 · 종목이 비어 있으면 그 자산군 종목은 아직 안 정한 것")
    if r.orders:
        st.dataframe(order_sheet.orders_table(r, labels), hide_index=True, use_container_width=True)
    else:
        st.info("이번엔 주문 없음")
    for n in r.notes:
        st.caption("· " + n)

    # ---- 지난 결정 + 버튼 ----
    if last:
        d = last[-1]
        st.caption(f"지난 결정: {d['date']} \"{d['decision']}\" — {d['reason']}")
    c1, c2, c3 = st.columns(3)
    reason = st.text_input("사유 (넘기기·보류할 때)", placeholder="예: 금리 인하 기다림")
    if c1.button("이번엔 넘기기"):
        record_decision(f"{pools[pool_id].get('label', pool_id)} 리밸런싱 보류", reason or "(사유 없음)")
        st.toast("DECISIONS.md에 기록했어요")
    if c2.button("직접 주문할게요"):
        record_decision(f"{pools[pool_id].get('label', pool_id)} 주문표 수락 (직접 주문)", reason or "")
        st.toast("DECISIONS.md에 기록했어요. 증권사 앱에서 주문표대로 주문하세요")
    c3.button("승인하고 자동주문", disabled=True, help="한국투자증권 계좌가 생기면(2027) 활성화 — 2단계")


def coming_soon(name: str) -> None:
    st.info(f"**{name}** 화면은 준비 중이에요. 기획은 docs/SCREEN_REFERENCE.md를 보세요.")
