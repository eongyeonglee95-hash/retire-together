# 공개 시세 소스 안정성 — 네이버 금융 · KRX · 공공데이터포털 · 라이브러리
기준일: 2026-10-26 · 상태: 초안

## 요약 (5줄 이내)
- `tools/market.py`는 네이버의 비공개(undocumented) JSON 두 개를 쓴다: 종목 검색 `ac.stock.naver.com/ac`, 현재가 `polling.finance.naver.com/api/realtime/domestic/stock/{code}`. 2026-10-26 둘 다 키 없이 200 응답. 네이버 이용약관(시행 2026-10-01)은 "사전 허락 없이 자동화된 수단(…스크래퍼 등)"으로 "이용자(사람)의 실제 이용을 전제로 하는" 취지에 맞지 않게 쓰는 것을 금지하고, `finance.naver.com/robots.txt`는 `Disallow: /`다.
- 공식 대안: 공공데이터포털 "금융위원회_증권상품시세정보"(ETF 시세: 종가·NAV·기초지수명·기초지수종가·순자산총액) — 무료, 서비스키, 일 1회 갱신(다음 영업일 13시 이후), 공공누리 4유형(상업적 이용 금지).
- KRX 정보데이터시스템(data.krx.co.kr)은 자동화 대량 조회를 감지해 IP를 차단하고 "KRX Open API(openapi.krx.co.kr) 등 공식 경로"를 안내한다(이번 접속에서 실제로 차단 안내 페이지를 받음). KRX Open API 포털은 JS 렌더링이라 조건 미확인.
- pykrx(마지막 커밋 2026-09-30)는 KRX·네이버 스크래핑, FinanceDataReader(2026-05-13)는 기본 네이버. 둘 다 MIT, 유지보수는 개인.
- 종목명→코드는 네이버 자동완성 외에 공공데이터 ETF API(종목명 필드)와 FDR `StockListing('ETF/KR')`이 같은 일을 한다.

## 비교표

| 소스 | 공식 여부 | 제공 항목 | 지연 | 인증 | 변경 위험 | 라이선스 | 출처·확인일 |
|---|---|---|---|---|---|---|---|
| 네이버 `polling.finance.naver.com/api/realtime/...` (현재 사용) | 비공식(문서 없음) | 현재가(`closePrice`), 등락, 거래상태; 응답에 `pollingInterval: 70000` | 응답 `delayTime: 0` 표기 | 없음 | 약관상 자동화 금지 조항·robots `Disallow: /`. 차단·변경 공지 채널 없음 | 네이버 약관 | [N1][N2][N3] 2026-10-26 |
| 네이버 `ac.stock.naver.com/ac` (종목명→코드, 현재 사용) | 비공식 | 코드·종목명·시장·국가 | — | 없음 | 위와 같음. `/robots.txt` 요청은 "접근 오류" HTML | 네이버 약관 | [N1][N3] 2026-10-26 |
| 공공데이터포털 금융위원회_증권상품시세정보 (ETF/ETN/ELW) | 공식(원천 KRX) | 종가·시가·고가·저가·거래량·NAV·기초지수명·기초지수종가·순자산총액; 종목명·코드 | 일 1회, 기준일 다음 영업일 13시 이후 | 서비스키(자동승인), 개발계정 일 10,000건 | 낮음(2021-11-16 등록, 2026-09-07 수정) | 공공누리 4유형: 출처표시·상업적 이용 금지·변경 금지, 재배포 금지 | [D1] 2026-10-26 |
| 공공데이터포털 금융위원회_주식시세정보 | 공식(원천 KRX) | 주식·수익증권 등 시가·종가·고가·저가·거래량 | 일 1회(상동) | 서비스키, 일 10,000건 | 낮음 | 공공누리 4유형 | [D2] 2026-10-26 |
| 공공데이터포털 금융위원회_지수시세정보 | 공식 | 주가지수·채권지수·파생지수 시가·종가 등 (2020-01-01 이후) | 일 1회(상동) | 서비스키 | 2024-12-06 지수명 변경 이력 있음 | 공공누리 4유형 | [D3] 2026-10-26 |
| KRX 정보데이터시스템 data.krx.co.kr (화면) | 공식 | (화면 미열람) | — | 일부 메뉴 KRX 회원 로그인(pykrx README) | 자동화 대량 조회 시 IP 차단 안내 | KRX | [X1][L1] 2026-10-26 |
| KRX Open API openapi.krx.co.kr | 공식 | 미확인(JS 렌더링) | 미확인 | 미확인 | 미확인 | 미확인 | [X2] 2026-10-26 |
| 금융투자협회 ETF 공시(dis.kofia.or.kr) | 공식 | 미확인(JS, 본문 못 읽음) | — | 미확인 | — | — | 2026-10-26 (열었으나 본문 없음) |
| 운용사 상품 페이지(삼성자산운용 KODEX 200) | 공식 | 미확인(JS, 본문 못 읽음) | — | — | — | — | 2026-10-26 (열었으나 본문 없음) |
| pykrx | 비공식 라이브러리 | ETF 목록·OHLCV·NAV·괴리율·추적오차 | KRX 화면과 동일 | 일부 KRX 로그인(`KRX_ID`/`KRX_PW`) | KRX 차단 가능성 README 명시 | MIT | [L1] 2026-10-26 |
| FinanceDataReader | 비공식 라이브러리 | 가격(기본 NAVER, `KRX:` 접두어), `StockListing('ETF/KR')` | — | 없음 | 네이버·KRX 변경에 종속 | MIT | [L2] 2026-10-26 |

## 상세 (소스별 단락)

### 네이버 금융 (현재 `tools/market.py`)
- 코드가 쓰는 URL: `https://ac.stock.naver.com/ac?q={q}&target=stock`(종목 검색, `nationCode == "KOR"` 필터), `https://polling.finance.naver.com/api/realtime/domestic/stock/{code}`(현재가, `datas[0].closePrice`). User-Agent `Mozilla/5.0 (retire-together PoC)`, 종목 간 0.2초 대기 [N1].
- 2026-10-26 직접 호출 결과: polling 엔드포인트 200 `application/json`, 본문에 `"pollingInterval":70000`, `stockExchangeType.delayTime: 0`, `closePriceSendTime: "1630"`, `closePrice "85,995"`(KODEX 200). 자동완성 엔드포인트도 200 JSON. 두 호스트 모두 공식 문서·개발자 안내 페이지가 없다(네이버 개발자센터 API 아님) [N3].
- robots: `finance.naver.com/robots.txt` = `User-agent: * / Disallow: /`; `m.stock.naver.com/robots.txt` = `Disallow: /`(Yeti만 일부 Allow); `polling.finance.naver.com/robots.txt`는 404 JSON; `ac.stock.naver.com/robots.txt`는 "[접근 오류] 서비스에 접속할 수 없습니다" HTML [N3].
- 이용약관(네이버 서비스 이용약관, 시행일자 2026-10-01) 원문: "네이버의 사전 허락 없이 자동화된 수단(예: 매크로 프로그램, 로봇(봇), 스파이더, 스크래퍼 등)을 이용하여 … 이용자(사람)의 실제 이용을 전제로 하는 네이버 서비스의 제공 취지에 부합하지 않는 방식으로 네이버 서비스를 이용하거나 … 네이버의 기술적 조치를 무력화하려는 일체의 행위 … 를 시도해서는 안 됩니다." 조항 번호는 HTML에서 추출하지 못함 [N2].
- 호출 빈도 제한: 공식 수치 없음. 응답의 `pollingInterval 70000`(70초)이 네이버 화면이 쓰는 갱신 주기라는 것만 확인. 변경 이력: 공식 변경 공지 채널이 없어 이력을 확인할 수 없음. 제3자 스킬 문서들은 "undocumented", "URL scheme이 바뀔 수 있다"고만 적음 (열어보지 않아 출처에서 제외).
- 보도: 네이버가 2025년 6~7월 AI 크롤러 차단 코드를 전 서비스로 확대했다는 기사가 검색에 걸렸으나 열어보지 않아 미확인.

### 공공데이터포털(data.go.kr) 금융위원회 API
- 금융위원회_증권상품시세정보(ID 15094806): 오퍼레이션 3개(ETF 시세·ETN 시세·ELW 시세). 페이지 내 응답 명세에 `nav`, `nPptTotAmt`(순자산총액), `bssIdxIdxNm`(기초지수의 명칭), `bssIdxClpr`(기초지수의 종가), `basDt`, `srtnCd` 필드가 있고, 요청 파라미터로 "기초지수_지수명이 일치/포함하는 데이터 검색"이 있다. 설명: "데이터 갱신주기는 일 1회", 기준일 다음 영업일 13시 이후 반영, 실시간 아님(메타데이터 '업데이트 주기: 실시간' 표기와 불일치). 무료, 자동승인, 개발계정 일 10,000건, 운영계정은 활용사례 등록으로 증설. 공공누리 4유형(출처표시·상업적 이용 금지·변경 금지), "제3자 무단 제공·재배포 금지", 상업적 이용은 KRX Data Marketplace에서 유료 구매. 등록 2021-11-16, 수정 2026-09-07 [D1].
- 금융위원회_주식시세정보(ID 15094808): 주식·수익증권·신주인수권 4개 오퍼레이션, 시가·종가·고가·저가·거래량. 갱신·인증·라이선스는 위와 동일. 수정 2026-09-07 [D2].
- 금융위원회_지수시세정보(ID 15094807): 주가지수·채권지수·파생지수, 2020-01-01 이후. "2024년 12월 6일 이후 일부 지수명이 바뀌었으므로 활용자 가이드 확인" [D3].
- 보수(총보수)는 세 API 어디에도 항목이 없다 → 보수는 이 경로로 못 받는다.

### KRX
- data.krx.co.kr: ETF 메뉴 URL을 열자 KRX Data Marketplace 접속 제한 안내가 왔다. 원문: "자동화 수단을 통한 비정상 대량 조회가 감지되어 해당 IP의 접속이 일시적으로 제한되었습니다." 일괄 데이터는 "KRX Open API(openapi.krx.co.kr) 등 공식 경로를 이용해 주시기 바랍니다", 화면 다운로드 기능이 공식 경로 [X1]. 화면의 제공 항목·로그인 조건은 그래서 미확인(pykrx README는 "일부 KRX API는 KRX 회원 로그인 필요"라고 적음 [L1]).
- openapi.krx.co.kr: 응답 본문 356바이트, 제목 "정보데이터시스템 - OPEN API"만 있고 나머지는 JS 로딩 → 신청 조건·인증키·갱신 시각·호출 한도·약관 모두 미확인 [X2]. 검색에 걸린 제3자 문서(카테고리별 승인, 매일 08시 갱신, 10,000건 한도)는 열어보지 않아 미검증.

### 라이브러리
- pykrx(`sharebook-kr/pykrx`, 마지막 커밋 2026-09-30, MIT): README "KRX와 네이버에서 데이터를 스크래핑", "데이터 저작권은 각 제공자에게", "도의적으로 무분별한 API 호출을 자제", 한 번에 많이 요청하면 KRX 서버가 차단할 수 있어 예제는 1초 지연. ETF 함수: `get_etf_ticker_list`, `get_etf_ohlcv_by_date/ticker`(NAV 열 포함), `get_etf_price_deviation`(괴리율), `get_etf_tracking_error`, `get_etf_portfolio_deposit_file`. 소스 `pykrx/website/krx/etx/core.py`의 ETF 클래스(`ETF_전종목기본종목`, `개별종목시세_ETF`, `전종목시세_ETF`)는 `KrxWebIo`(data.krx.co.kr 웹 요청)를 상속 [L1].
- FinanceDataReader(`FinanceData/FinanceDataReader`, 마지막 커밋 2026-05-13, MIT): 국내 가격은 기본 NAVER(2000년 이후), `KRX:` 접두어로 KRX, `StockListing('ETF/KR')`로 "한국 ETF 전종목" 목록. ETF 일별 시세의 소스는 README에 명시 없음 [L2].

### 그 밖에 열어봤으나 내용을 못 읽은 곳
- 금융투자협회 전자공시 ETF(dis.kofia.or.kr): 페이지 제목만 렌더링. 제공 항목·API 여부 미확인.
- 삼성자산운용 KODEX 200 상품 페이지(samsungfund.com … id=2ETF01): 네비게이션만 렌더링. iNAV·NAV·총보수 표시 여부 미확인.

## 우리 적용 — accounts.yaml `api:` 값·2단계 자동주문 설계에 주는 사실 (사용자 확인 전)
- 우리 용도(하루 한 번 종가·현재가, 종목명→코드):
  - **전일 종가·NAV·기초지수·순자산** → 공공데이터 증권상품시세정보 ETF 오퍼레이션이 전부 제공(다음 영업일 13시 이후, 서비스키 필요, 비상업 조건) [D1].
  - **장중 현재가** → 공식·무료 소스에서는 찾지 못함. 현재 쓰는 네이버 polling이 유일하게 확인된 경로이나 비공식·약관 조항 있음 [N2][N3]. 2단계 KIS 자동주문 때는 KIS 시세 API가 따로 있다(broker-apis.md).
  - **종목명→코드** → 네이버 자동완성(현재), 공공데이터 ETF API의 종목명 필드, FDR `StockListing('ETF/KR')` 세 곳에서 가능 [N1][D1][L2].
  - **총보수** → 이번에 확인한 어떤 API에도 없음. 운용사 페이지·KOFIA는 본문 미확인.
- `market.py`는 네트워크 실패 시 스냅샷 가격으로 폴백하도록 돼 있어, 네이버 차단 시 동작은 멈추지 않고 가격만 오래된 값이 된다(코드 docstring) [N1].

## 미확인 · 열린 질문
- 네이버 polling/ac 엔드포인트의 호출 빈도 제한 수치, 변경·차단 이력(공식 채널 없음).
- 네이버 약관 해당 조항 번호; 개인 비상업 하루 수십 회 호출이 "사람의 실제 이용 전제"에 반하는지는 해석 문제(여기서 판단하지 않음).
- KRX Open API: 신청 조건·인증키·갱신 시각·호출 한도·약관(JS 페이지 미열람).
- data.krx.co.kr 화면의 로그인 필요 범위·다운로드 제공 항목(IP 차단 안내로 미열람).
- 공공데이터 ETF API의 실제 응답 샘플(키 발급 후 확인 필요)과 "실시간" 메타데이터 표기 불일치의 의미.
- KOFIA ETF 공시, 운용사 iNAV 페이지의 제공 항목·자동 조회 가능 여부.
- FDR의 ETF 일별 시세 소스.

## 출처 (열어본 페이지만, 날짜)
- [N1] 저장소 `tools/market.py` (2026-10-26)
- [N2] 네이버 서비스 이용약관(시행일자 2026-10-01) — https://policy.naver.com/rules/service.html (2026-10-26, curl로 읽음)
- [N3] 직접 호출: https://finance.naver.com/robots.txt, https://m.stock.naver.com/robots.txt, https://polling.finance.naver.com/robots.txt, https://ac.stock.naver.com/robots.txt, https://polling.finance.naver.com/api/realtime/domestic/stock/069500, https://ac.stock.naver.com/ac?q=KODEX%20200&target=stock, https://m.stock.naver.com/api/stock/069500/basic (2026-10-26)
- [D1] 공공데이터포털 금융위원회_증권상품시세정보 — https://www.data.go.kr/data/15094806/openapi.do (2026-10-26); 검색 목록 https://www.data.go.kr/tcs/dss/selectDataSetList.do?dType=API&keyword=증권상품시세정보 (2026-10-26)
- [D2] 공공데이터포털 금융위원회_주식시세정보 — https://www.data.go.kr/data/15094808/openapi.do (2026-10-26)
- [D3] 공공데이터포털 금융위원회_지수시세정보 — https://www.data.go.kr/data/15094807/openapi.do (2026-10-26)
- [X1] KRX 정보데이터시스템 ETF 메뉴(접속 제한 안내 페이지 수신) — https://data.krx.co.kr/contents/MDC/MDI/mdiLoader/index.cmd?menuId=MDC0201030101 (2026-10-26)
- [X2] KRX Open API — https://openapi.krx.co.kr/ (2026-10-26, 제목만 렌더링)
- [L1] sharebook-kr/pykrx README·`pykrx/website/krx/etx/core.py`·저장소 메타(마지막 커밋 2026-09-30) — https://github.com/sharebook-kr/pykrx (2026-10-26)
- [L2] FinanceData/FinanceDataReader README·저장소 메타(마지막 커밋 2026-05-13) — https://github.com/FinanceData/FinanceDataReader (2026-10-26)
- 열어봤으나 본문을 못 읽은 페이지: https://dis.kofia.or.kr/websquare/index.jsp?w2xPath=/wq/fundann/DISFundAnnETF.xml , https://www.samsungfund.com/etf/product/view.do?id=2ETF01 , https://www.data.go.kr/data/15150946/openapi.do(주식발행공시, 무관), https://www.data.go.kr/data/15151192/openapi.do(ESG증권상품, 무관) — 2026-10-26

## 변경 이력
- 2026-10-26: 초기 작성
