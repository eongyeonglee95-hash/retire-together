# 증권사 API 지원 범위 — 미래에셋 · 한국투자(KIS) · 키움
기준일: 2026-10-26 · 상태: 초안

## 요약 (5줄 이내)
- 한국투자증권 KIS Developers: 개인 개방 REST API. 공식 GitHub 설정 파일에 계좌상품코드 `22`(개인연금) · `29`(퇴직연금)가 선택지로 있고, 퇴직연금 전용 **조회** TR 5종이 있다. 연금 전용 **주문** TR은 없다(주문은 `주식주문(현금)`에 상품코드를 넣는 구조). 연금계좌로 주문이 수용되는지는 공식 문서·코드에 명시가 없어 **미확인**. 모의투자(vps) 분기는 `01`·`03`만 있어 연금계좌 모의투자는 공식 샘플 코드상 불가.
- 미래에셋증권: 개인용 Open API 개발자 포털·신청 페이지를 찾지 못함. 홈페이지 '매매주문 접수·처리 방법 안내'에 `FIX/API DMA(QOMS)` 경로가 있으나 "자체주문시스템 보유" 고객이 영업점 신청→본사 승인을 거치는 특화주문이다. 연금계좌 조회·주문 API 지원은 **미확인**(근거 없음).
- 키움증권: 2025-03-24 REST API 출시, 개인 대상, 운영/모의 키 분리. 공식 저장소 API 명세(337개)에 "연금·IRP·ISA" 문자열이 0건. 잔고조회(kt00018)에 계좌번호 파라미터가 없고 계좌번호조회(ka00001)가 따로 있어, 연금계좌가 앱키에 연결되는지는 **미확인**.
- 기존 조사(MASTER_CONTEXT 2026-10-26)와의 대조는 §상세 끝 "기존 조사 검증" 표.

## 비교표

| 항목 | 미래에셋증권 | 한국투자증권 KIS Developers | 키움증권 REST API |
|---|---|---|---|
| 제공 여부 | 개인용 Open API 포털 미발견. FIX/API DMA(QOMS) 특화주문만 확인 [M1] | 제공 [K1][K2] | 제공(2025-03-24 출시) [W1] |
| 플랫폼 | FIX/API(사설망, 자체주문시스템 전제) [M1] | REST + WebSocket [K1] | REST + WebSocket(OS 무관) [W1][W2]. Open API+(OCX, Windows)는 이번에 열어본 페이지 없음 → 미확인 |
| 개인 개방 | 미확인. 트레이딩 Open API 명세서 작성 아르바이트 공고(2026-07)만 간접 근거 [M2] | 개인 계좌·HTS ID 전제 [K2](README) | 개인 투자자·개발자 대상 [W1] |
| 연금계좌 조회 | 미확인 | 퇴직연금 조회 TR 5종(TTTC2208R 등), 예시 상품코드 `29`. "주식·ETF·ETN만 조회, 펀드 불가". `55`(DC가입자) 불가 [K3] | 명세에 연금 관련 문자열 0건 → 미확인 [W2][W3] |
| 연금계좌 주문 | 미확인 | 연금 전용 주문 TR 없음. `주식주문(현금)` TTTC0012U/0011U에 `ACNT_PRDT_CD`를 넣는 구조 [K4]. 연금계좌 수용 여부 공식 명시 없음 → 미확인 | 미확인 |
| 모의투자 | 미확인 | 있음(vps 도메인). 샘플 코드의 모의 분기는 `01`·`03`만 [K5] | 있음(mockapi.kiwoom.com, 키 별도). "모의투자에서 지원하지 않는 API" 오류코드 8104 존재 [W2][W3] |
| 인증 | 미확인 | 계좌별 Appkey/Appsecret → 접근토큰 [K1] | App Key/Secret → OAuth 접근토큰(au10001) [W2][W3] |
| 호출 제한 | 미확인 | 기본 20 TPS(언론 보도, 2026-08-31) [K6]. 모의는 "호출 제한이 낮음"(EGW00201) [K2] | 유량 초과 오류코드 1700·1701·1702 존재, 수치는 미확인 [W3] |
| 출처·확인일 | [M1][M2] 2026-10-26 | [K1]~[K6] 2026-10-26 | [W1]~[W3] 2026-10-26 |

## 상세 (소스별 단락)

### 미래에셋증권
- 공식 홈페이지 '매매주문 접수·처리 방법 안내' 표에 주문 채널로 영업점·ARS·MTS·HTS/홈페이지·시스템트레이딩·특화주문(`FIX/API DMA(QOMS)`, `FEP DMA`)이 있다. 특화주문의 이용조건은 "자체주문시스템보유"(파생은 "자체주문시스템 보유 & 사후증거금 계좌")이고, "전용 프로세스 신청 절차"는 "고객이 영업점에 신청 → 영업점은 본사 담당부서에 승인요청 → 담당부서는 적격여부 판단 → 결재권자의 승인". 주1)에 "특화주문서비스는 이용조건을 충족하는 고객(고빈도주문 고객)에게 맞춤 주문서비스를 제공"이라고 적혀 있다 [M1]. 이 페이지는 연금계좌를 언급하지 않는다.
- 서울대 컴퓨터공학부 게시판의 "[미래에셋증권] 트레이딩 Open API 개발 지원 아르바이트 채용 안내"(게시 2026-07-09)에 "Open API 명세서(정의서) 작성 및 최신화 보조", "API 기능 및 연동 테스트 수행"이 업무로 적혀 있다. 대상 고객(개인/기관)은 공고에 없다 [M2].
- `securities.miraeasset.com` 도메인 한정 검색에서 Open API 안내 페이지는 나오지 않았다. `developers.digitalx.miraeasset.com`(디지털엑스 개발자센터)은 열어봤으나 본문이 비어 있어 내용 미확인 — 검색 요약은 가상자산 거래소 API라고 했으나 그 설명은 열어본 페이지에서 확인하지 못함.
- 2026-08~10월 언론의 개인용 Open API 기사(KB증권 2026-07-20 오픈베타 [O1], 메리츠증권 2026-10-12 시범 [O2])에 미래에셋증권은 언급되지 않는다.

### 한국투자증권 KIS Developers
- 공식 포털(apiportal.koreainvestment.com)의 API 문서·FAQ·이용안내 페이지는 JS 렌더링이라 본문을 읽지 못했다(FAQ "총 0건", 문서 표의 TR ID 칸 비어 있음). 아래는 **공식 GitHub 저장소** `koreainvestment/open-trading-api`(마지막 push 2026-10-23, Issues 비활성) 기준.
- 인증: 소개 페이지 원문 "계좌의 Appkey, App secret으로 토큰을 발급받고, 이것을 이용하여 REST API를 호출합니다." [K1]
- 계좌상품코드(`kis_devlp.yaml`): `01` 종합계좌 / `03` 국내선물옵션 / `08` 해외선물옵션 / `22` 개인연금 / `29` 퇴직연금. 계좌번호 앞 8자리(`my_acct_stock`)는 연금도 증권계좌와 같은 값을 쓴다(`kis_auth.py` 156~165행: prod+`22`, prod+`29` → `my_acct_stock`) [K5].
- 모의투자: `kis_auth.py`의 `changeTREnv`에서 `vps`(모의) 분기는 `01`과 `03`뿐이다(166~169행). 즉 공식 샘플 코드상 연금계좌(22·29)의 모의투자 조합은 없다 [K5]. README: "모의투자 계좌는 REST API 호출 제한이 낮습니다." [K2]
- 퇴직연금 조회 TR 5종(`examples_llm/domestic_stock/pension_*`): 잔고조회 TTTC2208R(v1_국내주식-036), 체결기준잔고(-032), 미체결내역(-033), 매수가능조회(-034), 예수금조회(-035). 예시 상품코드는 모두 `29`. 잔고조회 docstring 원문: "주식, ETF, ETN만 조회 가능하며 펀드는 조회 불가합니다." 5종 모두 "55번 계좌(DC가입자계좌)의 경우 해당 API 이용이 불가합니다. KIS Developers API의 경우 HTS ID에 반드시 연결되어있어야만 API 신청 및 앱정보 발급이 가능한 서비스로 개발되어서 실물계좌가 아닌 55번 계좌는 API 이용이 불가능" [K3]. `22`(개인연금)에 대한 전용 조회 TR·주석은 없다.
- 주문: `order_cash.py` — `주식주문(현금)` 실전 TTTC0012U(매수)/TTTC0011U(매도), 모의 VTTC0012U/VTTC0011U. 파라미터 `ACNT_PRDT_CD`는 "계좌상품코드(상품유형코드)"로만 설명되고 허용값 목록·연금 관련 주석은 없다 [K4]. 연금계좌에 대한 서버 수용 여부를 적은 공식 문구는 저장소에서 찾지 못했다.
- 호출 제한: 아시아경제 2026-08-31 "한투증권, '오픈API 활성화 캠페인'" — 기본 20 TPS, 조건 충족 시 최대 100 TPS(12-31까지) [K6]. 토큰 유효기간·모의투자 초당 건수는 열어본 공식 페이지에 없음 → 미확인(블로그는 24시간·모의 초당 2건이라 하나 미검증).
- 2차 출처(단서): AlgoLab 블로그 2026-09-26 — 위 상품코드·TR 5종·vps 분기와 같은 내용을 적고, "연금계좌 주문은 일반 주문 TR에 상품코드만 바꾸는 구조이나 서버 수용 여부는 확인 대상"이라고 한다 [B1]. 실제 연금계좌 주문 성공/실패 사례는 검색에서 찾지 못했다.

### 키움증권
- 출시: 2025-03-24 "키움 REST API" 출시. 별도 프로그램 설치 없이 Windows·Mac·Linux, Python·Java. 대상은 개인 투자자·개발자 [W1]. 2025-08-18 기준 누적 호출 5억건·접속자 1만명 [W4].
- 공식 저장소 `Kiwoom-Securities/Kiwoom-REST-API`(마지막 push 2026-09-15): 전체 337 API 명세, 운영 도메인 `https://api.kiwoom.com`, 모의 `https://mockapi.kiwoom.com`. README: "운영(real)과 모의투자(demo)는 키가 서로 다릅니다." [W2]
- 명세 JSON(`kiwoom/_data/kiwoom_api_spec.json`)에서 "연금"·"IRP"·"ISA" 문자열 0건. 계좌평가잔고내역요청 kt00018의 요청 body는 `qry_tp`(1 합산/2 개별)·`dmst_stex_tp`(KRX/NXT) 둘뿐이고 계좌번호 항목이 없다. 계좌번호조회 ka00001은 응답 `acctNo`만 돌려준다 [W3]. 어느 계좌가 조회되는지(앱키 단위인지, 연금계좌도 포함되는지)는 명세로는 알 수 없다 → 미확인.
- 오류코드: 1700 "허용된 API 요청 개수를 초과", 1701 "허용된 전체 요청 개수를 초과", 1702 "허용된 그룹 요청 개수를 초과", 8104 "모의투자에서 지원하지 않는 API", 8200 "법인 고객은 해당 API를 지원하지 않습니다" [W3]. 초당 수치는 명세에 없다.
- Open API+(OCX): 이번에 열어본 공식 페이지 없음. 포털 공지·FAQ 게시판(`openapi.kiwoom.com/board/Board010xView`)은 JS 로딩이라 글 목록을 읽지 못했다.
- 사례(커뮤니티): "키움 연금저축 보유 종목을 API로 반영하려면"이라는 질문 글이 검색에 걸렸으나 결과가 적혀 있지 않아 근거로 쓰지 않음. 블로그 [B1]은 키움 저장소에서 "연금/IRP" 검색 0건을 "근거 없음"으로 한정해 적었다(이번 확인과 일치).

### 기존 조사 검증 (docs/MASTER_CONTEXT.md 41·80·81행, 2026-10-26)

| 기존 조사 | 이번 확인 | 출처 |
|---|---|---|
| KIS: 연금저축(22)·IRP(29)는 일반 주문 TR에 코드만 바꾸는 구조 | 확인됨(구조). `kis_devlp.yaml`에 22·29 선택지, 연금 전용 주문 TR 없음, `order_cash`가 `ACNT_PRDT_CD`를 받음. 단 "서버가 수용한다"는 공식 문구는 없음 | [K4][K5] |
| KIS: 조회 API는 문서화됨 | 확인됨 — 단 **퇴직연금(29)** 조회 TR 5종. 개인연금(22) 전용 조회 TR은 없음 | [K3] |
| KIS: 주문 수용 여부는 실계좌 소액 테스트 필요(모의투자 불가) | 확인됨. vps 분기 `01`·`03`뿐 | [K5] |
| KIS: 퇴직연금 잔고조회는 펀드 미포함 | 확인됨(docstring 원문) | [K3] |
| KIS: DC(55) 불가 | 확인됨 | [K3] |
| KIS: ISA 미확인 | 그대로 미확인. 저장소에 ISA 상품코드 없음 | [K5] |
| 미래에셋: 트레이딩 Open API 자체는 존재 | **부분 반박/보강**: 개인용 Open API 포털은 미발견. 확인된 것은 FIX/API DMA(QOMS) 특화주문(자체주문시스템·영업점 승인)과 2026-07 Open API 개발 지원 아르바이트 공고뿐 | [M1][M2] |
| 미래에셋: 연금저축 잔고 조회 지원 여부 확인 못 함 | 그대로 미확인 | — |
| 타 증권사 연금 API 근거 없음 | 키움 공식 명세 0건으로 확인. KB·메리츠는 이번 범위 밖 | [W3] |

## 우리 적용 — accounts.yaml `api:` 값·2단계 자동주문 설계에 주는 사실 (사용자 확인 전)
- `me_mirae_pension_new/old`, `me_irp`(미래에셋 추정): 개인용 API 근거 없음 → `api: false` 유지가 현재 사실과 맞다.
- `me_kis_pension`(2027 개설 예정, `api: true`): 조회는 `29`용 TR만 문서화. 연금저축은 `22`이므로 잔고조회는 일반 `주식잔고조회`(inquire_balance)에 `22`를 넣는 방식인지, 퇴직연금 TR에 `22`가 통하는지 둘 다 미확인. 주문 수용 여부는 실계좌 소액 주문으로만 확인 가능(모의 불가).
- `me_kiwoom_general`(현금 주머니, 일반계좌): 키움 REST API로 잔고 조회 가능 범위에 들어가지만 PoC 범위 밖. 연금계좌가 아니므로 "연금 미지원" 쟁점과 무관.
- KIS 호출 제한(기본 20 TPS)은 하루 한 번 리밸런싱 용도에는 제약이 되지 않는다는 사실만 기록.

## 미확인 · 열린 질문
- KIS `주식주문(현금)`이 `ACNT_PRDT_CD=22`(연금저축)로 주문을 수용하는지 — 공식 문서·GitHub에 명시 없음. Issues가 비활성이라 이슈 검색 불가.
- KIS 개인연금(22) 잔고조회에 어떤 TR을 쓰는지(일반 잔고조회 vs 퇴직연금 TR).
- KIS ISA 계좌의 상품코드·API 허용 여부.
- KIS 토큰 유효기간, 모의투자 초당 건수(공식 페이지 미열람).
- 미래에셋 개인용 Open API 존재 여부 — 홈페이지 고객서비스 메뉴·고객센터(1588-6800)로 확인 필요. `FIX/API DMA`가 연금계좌에 적용되는지.
- 키움 REST API 앱키에 연금저축·IRP 계좌가 연결되는지, ka00001이 돌려주는 계좌 목록에 포함되는지. Open API+(OCX)의 연금계좌 지원 여부.
- 키움 호출 제한 수치(1700~1702의 기준값).

## 출처 (열어본 페이지만, 날짜)
- [M1] 미래에셋증권 매매주문 접수·처리 방법 안내 — https://securities.miraeasset.com/imf/100/imf203.do (2026-10-26, EUC-KR 디코딩해 읽음)
- [M2] 서울대 컴퓨터공학부 공지 "[미래에셋증권] 트레이딩 Open API 개발 지원 아르바이트 채용 안내" — https://cse.snu.ac.kr/en/community/notice/25298 (2026-10-26)
- [K1] KIS Developers 소개 — https://apiportal.koreainvestment.com/intro (2026-10-26)
- [K2] koreainvestment/open-trading-api README — https://github.com/koreainvestment/open-trading-api (2026-10-26)
- [K3] 같은 저장소 `examples_llm/domestic_stock/pension_inquire_balance/pension_inquire_balance.py` 및 `pension_inquire_present_balance`·`pension_inquire_daily_ccld`·`pension_inquire_psbl_order`·`pension_inquire_deposit` — https://github.com/koreainvestment/open-trading-api/tree/main/examples_llm/domestic_stock (2026-10-26)
- [K4] 같은 저장소 `examples_llm/domestic_stock/order_cash/order_cash.py` (2026-10-26)
- [K5] 같은 저장소 `kis_devlp.yaml`, `examples_llm/kis_auth.py` (2026-10-26)
- [K6] 아시아경제 "한투증권, '오픈API 활성화 캠페인'…API 호출 한도 최대 5배 확대" 2026-08-31 — https://core.asiae.co.kr/article/2026083110264822190 (2026-10-26); 같은 내용 매일신문 — https://www.imaeil.com/page/view/2026083114305386174 (2026-10-26)
- [W1] 스마트투데이 "키움증권, 트레이딩 로직 만들어 투자하는 서비스 제공" 2025-03-24 — https://www.smarttoday.co.kr/ko-kr/articles/75984 (2026-10-26)
- [W2] Kiwoom-Securities/Kiwoom-REST-API README·LICENSE — https://github.com/Kiwoom-Securities/Kiwoom-REST-API (2026-10-26)
- [W3] 같은 저장소 `kiwoom/_data/kiwoom_api_spec.json`, `kiwoom/core/errors.py`, `examples/국내주식/계좌/get_domestic_account_evaluation_balance.py`, `list_domestic_accounts.py` (2026-10-26)
- [W4] 아시아경제 "키움증권, REST API 거래 이벤트 시즌2" 2025-08-25 — https://core.asiae.co.kr/article/2025082509405960531 (2026-10-26)
- [O1] 머니투데이 "KB증권, 개인 고객 대상 오픈API 서비스 실시" 2026-08-04 — https://www.mt.co.kr/stock/2026/08/04/2026080414364184356 (2026-10-26)
- [O2] SBS Biz "AI가 주식 사고파는 시대…메리츠도 '오픈 API' 참전" 2026-10-13 — https://biz.sbs.co.kr/amp/article/20000339624 (2026-10-26)
- [B1] (2차·단서) AlgoLab 블로그 "연금·IRP 알고트레이딩 KIS API" 2026-09-26 — https://algolab.co.kr/blog/pension-irp-algotrading-kis-api-2026 (2026-10-26)
- 열어봤으나 본문을 못 읽은 페이지: KIS 포털 FAQ(/faq)·이용안내(/about-howto)·API 문서(/apiservice-apiservice), 키움 포털 홈(openapi.kiwoom.com/main/home)·공지(/board/Board0101View), 미래에셋 다이렉트 계좌개설(nki3002/n02.do), 디지털엑스 개발자센터 — 모두 2026-10-26

## 변경 이력
- 2026-10-26: 초기 작성
