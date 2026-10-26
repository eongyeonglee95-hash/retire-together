# RetireTogether (둘이서은퇴)

부부 연금·현금 주머니를 규칙대로 굴리는 은퇴 가계 노트. 첫 목표는 Pension Rebalancing Agent PoC.

## 시작할 때 반드시 읽을 것
1. `docs/MASTER_CONTEXT.md` — 단일 출발점. 제품 철학과 책임 분리 원칙
2. `docs/AGENT_DESIGN.md` — 첫 Agent 정의와 PoC 범위(§2). 범위 밖 기능은 만들지 않는다
3. 작업 영역에 따라 `docs/REBALANCING_RULES.md`, `docs/CALCULATION_RULES.md`, `docs/TAX_RULES.md`

## 지켜야 할 원칙
- 숫자 → 코드/DB. LLM은 계산하지 않는다. 모든 공식은 `CALCULATION_RULES.md`를 순수 함수로 구현하고 pytest 단위 테스트를 둔다
- 규칙 → `docs/*_RULES.md` (wiki). 코드에 규칙을 하드코딩하지 말고 문서/YAML에서 읽는다
- 판단 조건(임계치·한도·제도 제약) → deterministic logic
- 설명/대화/기억 → Agent. 예측·추천 표현 금지("오를 것", "이 ETF가 좋다")
- 전략과 종목은 사용자가 정한다. Agent는 전략을 바꾸거나 추천하지 않는다
- 사용자 결정(수락/거절/사유, 가정값 변경)은 `docs/DECISIONS.md`에 기록
- 문서를 고치면 `docs/CHANGELOG.md`에 한 줄 남긴다
- Agent 허용 도구는 `tools/`의 커스텀 도구만. Bash·파일 편집 등 SDK 기본 도구는 비활성
- 전략 비율·종목 매핑 숫자는 `rules/*.yaml`이 원천. 문서에 숫자를 복사하지 않는다

## 저장소 구조 (목표)
- `docs/` 기획·규칙 문서. `docs/wiki/` 리서치 위키 — 쓰고 갱신하는 절차는 `/wiki-research` 스킬
- `app/` Streamlit 화면 (홈·리밸런싱)
- `agent/` 메인 Agent와 프롬프트
- `tools/` parse_balance / tag_assets / load_strategy / compute_rebalance / explain_inputs / build_order_sheet / record_decision
- `rules/` 전략 YAML, 자산군↔종목 매핑 YAML, 계좌 목록 YAML(소유자·증권사·계좌종류)
- `data/` 샘플 CSV·캡처, 결정 기록
- `tests/` 계산 함수 단위 테스트

## 기술
Python 3.12 + uv, Claude Agent SDK, pandas, PyYAML, pytest, Streamlit.
실행: `uv run pytest` / 등록 `uv run python -m tools.register --account <id> --images <png...> --out <csv>` / 드라이런 `uv run python -m tools.cli --holdings <csv> --pool me_pension [--new-cash 3000000 --new-cash-account <id>] [--live]` / 화면 `uv run streamlit run app/main.py`(2주차).
tools/: strategy(load_strategy) · assets(tag_assets, 제약 검증, 계좌·풀) · market(종목코드·현재가) · rebalance(compute_rebalance 순수 함수) · explain(왜 지금 템플릿) · order_sheet · decisions · parse_balance(CSV·캡처) · cli. 자동주문(KIS API)은 PoC 2단계 — 지금은 드라이런만. 일정과 현재 범위는 `docs/AGENT_DESIGN.md` §2.
