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


def rebalancing(view: str) -> None:
    st.caption("2주차에 엔진을 연결합니다. 지금은 터미널에서: `uv run python -m tools.cli --holdings <csv> --pool me_pension_old`")
    st.info("준비 중 — 풀 선택 → 목표 vs 현재 → 주문표 → 왜 지금")


def coming_soon(name: str) -> None:
    st.info(f"**{name}** 화면은 준비 중이에요. 기획은 docs/SCREEN_REFERENCE.md를 보세요.")
