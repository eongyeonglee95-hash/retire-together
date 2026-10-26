# CHANGELOG

## 2026-10-26
- docs/ 구조로 재편: MASTER_CONTEXT, SCREEN_REFERENCE, MASTER_PRD, AGENT_DESIGN, REBALANCING_RULES, TAX_RULES, CALCULATION_RULES, DECISIONS, CHANGELOG 생성
- TAX_RULES: 퇴직금 연금수령 과세 비율을 2단계(30/40% 감면)에서 3단계(실제수령연차 10년 이하 70% / 20년 이하 60% / 20년 초과 50% 과세)로 수정. "55세 즉시 개시" 하드코딩 금지 → 시나리오 비교. 1,500만원은 절벽이 아닌 기준선으로 표현 수정
- AGENT_DESIGN: Pension Rebalancing Agent 정의 고정, 내부 역할 표, 첫 PoC 1페이지(범위·제외·완료 기준·기술·일정)
- 자동매매(KIS API 연금계좌 조사 결과), 레거시 처리, 현금 주머니 구조 반영
- (Claude Code 세션) 확정 대기 기본값 확정, 수령 기간을 층별 종료 나이로 변경, 계좌 현황(미래에셋·키움·한투) 추가, 아이디에이션 회의(1~2주 뒤) 기준으로 PoC 일정을 "계산 함수 → Streamlit 홈 → 리밸런싱 화면 → Agent"로 조정, 전략 비율 원천을 rules/strategies.yaml로 통일, Agent 도구·컨텍스트 제한 명시, 워크플로우 0단계 계좌 선택(rules/accounts.yaml) 추가, 리밸런싱 HTML 목업(docs/assets/mockup-rebalancing.html) 반영 및 compute_rebalance 출력 데이터 계약 추가, 미래에셋 연금저축 (구)+(신) 합산 규칙과 캡처 입력 경로 반영, data/ 전체 git 제외, 입력 구조를 "보유 내역 1회 등록 + 현재가 공개 시세 조회"로 확정(fetch_prices tool 추가)
- (코드) 1주차 전반 완료: tools/ 9개 모듈, 테스트 15개 통과, 실제 잔고로 드라이런 주문표 생성. 리밸런싱 풀(pool)과 모드(리밸런싱/매수만)를 accounts.yaml에 추가, 첫 로그인 때 합산/따로를 고르는 "계좌 묶기" 화면을 SCREEN_REFERENCE에 추가
- (코드) 종목 역할 core/satellite(위성 먼저 매도, 핵심만 매수)와 완전 리밸런싱 옵션. 자산 시트(출처·음영·매입단가·필터)
- (코드) 설정(계좌 묶기)·입력(캡처 등록) 화면 완성. 화면 스모크 테스트 추가
- (코드) 2주차 리밸런싱 화면 완성(풀·전략·모드·납입·차트·주문표·결정 버튼). 종목 선택 규칙 §1-2와 class_defaults 추가, 엔진이 기본 종목으로 수량 계산
- docs/wiki/ 리서치 위키 폴더와 `/wiki-research` 프로젝트 스킬(새 주제·주기 갱신 절차) 추가
- (코드) Streamlit 메인 화면(홈·연금 샘플·메뉴) 1주차 후반 완료. 체크리스트에 '데이터 리서치 / llm-wiki' 트랙 분리
- (코드) 캡처 파싱(Claude 비전, Agent SDK) 실행: 캡처 6장 → 두 계좌 모두 화면 합계와 오차 0. 완료 기준 2 통과
