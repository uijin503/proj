# 실시간 투자 정보 통합 앱 설계 문서

## 1. 앱 한 줄 정의
**뉴스·공시·공매도·기관동향을 실시간에 가깝게 통합 수집하고, AI로 중요도/위험도를 분석해 빠른 의사결정을 돕는 모바일 투자 인텔리전스 앱**.

---

## 2. 핵심 기능 요약

- 실시간 피드(웹소켓 + 폴링 백업) 기반 통합 데이터 제공
- 카테고리별 뉴스/이벤트 분류(다중 태깅 지원)
- 종목 단위 통합 뷰(뉴스 + 공시 + 공매도 + 기관동향)
- AI 분석(요약, 중요도, 호재/악재, 위험 경고, 이슈 클러스터링)
- 디스코드 웹훅 알림(중요 뉴스/공시/공매도 급변/기관 대량 매매)
- 사용자 맞춤 알림(카테고리·종목·중요도 기준)

> 주의: 이 앱은 투자 수익을 보장하지 않으며, 데이터 소스 지연/오류 가능성이 있어 최종 판단은 사용자가 수행해야 함.

---

## 3. 사용자 시나리오

### 시나리오 A: 출근길 3분 점검
1. 사용자 홈 진입
2. `AI 위험 경고 카드`에서 오늘 위험 이슈 확인
3. `오늘의 핵심 이슈`에서 군집화된 상위 이슈 3개 확인
4. 보유 종목 탭으로 이동해 공매도 급변/공시 여부 확인

### 시나리오 B: 급락 종목 원인 파악
1. 종목 검색(예: TSLA)
2. 종목 화면에서 최근 24시간 뉴스/공시/공매도/기관동향 타임라인 확인
3. AI 종합 판정(호재/악재/중립 + 신뢰도 + 위험 경고) 확인
4. 필요한 경우 디스코드로 해당 종목 알림 ON

### 시나리오 C: 테마/매크로 리스크 감시
1. 카테고리 `경제`, `정치`, `국제` 필터 사용
2. 중요도순 정렬로 고영향 이벤트 우선 파악
3. 연결 종목 자동 태그를 통해 영향받는 종목 확인

---

## 4. 전체 시스템 구조

## 4.1 아키텍처 개요

```text
[외부 소스]
  RSS/News API, SEC EDGAR, Finviz, Fintel, HedgeFollow
       |
       v
[수집 서버 Collector]
  - 소스별 커넥터
  - 주기 스케줄러/레이트리밋
  - 원천 정규화
       |
       v
[이벤트 버스/큐 Redis Streams]
       |
       v
[분석 서버 Analyzer]
  - NLP/LLM 분류·요약
  - 티커 추출/감성/위험도
  - 중복 제거/이슈 클러스터링
       |
       v
[PostgreSQL + Redis Cache]
       |
       +--> [API 서버 FastAPI]
       |       - REST API
       |       - 인증/권한
       |
       +--> [Realtime Gateway]
               - WebSocket push
               - 폴링 백업용 변경분 조회

[모바일 앱 React Native]
  - 실시간 피드 구독
  - 오프라인 캐시
  - 알림/설정

[Notification Worker]
  - Discord Webhook
  - (추후) FCM/APNs
```

## 4.2 권장 기술 스택

| 영역 | 선택 | 이유 |
|---|---|---|
| 모바일 | **React Native** | 빠른 MVP, JS 생태계(웹/앱 공유), 실시간 UI 라이브러리 풍부 |
| 백엔드 API | FastAPI | 비동기 처리, Pydantic 검증, WebSocket 지원 우수 |
| 수집/분석 | Python Worker | 데이터 처리/AI 생태계 강점 |
| DB | PostgreSQL | 관계형 모델+JSONB, 인덱싱/파티셔닝 강력 |
| 캐시/메시징 | Redis | 저지연 캐시 + Pub/Sub/Streams |
| 실시간 통신 | WebSocket | 서버→클라이언트 즉시 푸시 |
| 배포 | Docker + Kubernetes(또는 ECS) | 스케일 아웃/롤링 업데이트 |

> Flutter도 우수하지만, 본 프로젝트는 백엔드/AI와의 JSON 중심 협업 및 MVP 속도를 고려해 React Native를 우선 추천.

## 4.3 배포 구조(권장)

- `api-service` (FastAPI)
- `ws-gateway` (FastAPI/ASGI separate deployment)
- `collector-workers` (Celery/RQ/Arq)
- `analyzer-workers` (GPU 옵션 가능)
- `notification-worker`
- `postgres` (Managed 권장)
- `redis` (Managed 권장)
- `object-storage` (원문/로그 백업)

Windows + VS Code 개발:
- Python venv + Poetry/uv
- Node.js LTS + pnpm
- Docker Desktop
- VS Code extension: Python, Pylance, ESLint, Prettier, Docker

---

## 5. 화면별 상세 기획 (모바일 기준)

## 5.1 홈 화면
섹션 구성:
1. 상단 시장 상태 바(미국장/프리마켓/애프터마켓, 데이터 지연 표시)
2. **AI 위험 경고 카드** (Red/Amber/Green)
3. 실시간 속보 티커
4. 주요 공시 카드(최근 제출 순)
5. 오늘의 핵심 이슈(클러스터 카드)

카드 항목 예:
- 제목
- 태그: `[경제][증시][악재]`
- 중요도(1~10)
- 발생시각 / 소스지연(예: +45초)

## 5.2 카테고리 뉴스 화면
탭:
- 전체 / 경제 / 정치 / 증시 / 코인 / 기업 / 국제 / 속보 / 공시 / 공매도 / 기관동향

정렬:
- 최신순(default)
- 중요도순
- 위험도순

필터:
- 시장(미국/글로벌)
- 시가총액
- 사용자 관심종목만

## 5.3 종목별 화면
섹션:
- 종목 헤더(가격/등락률/거래량)
- AI 요약 패널(최근 24h 핵심)
- 뉴스
- 공시
- 공매도(Short Interest, Borrow Fee)
- 기관동향(13F/헤지펀드 변화)
- 이슈 타임라인(시간축 통합)

## 5.4 공시 화면
- 문서 리스트(SEC/EDGAR)
- 필터: Form Type(8-K, 10-Q, 10-K, S-1 등)
- 제출 시각, 회사, 중요도
- AI 1줄 요약 + 리스크 코멘트

## 5.5 공매도 화면
- 종목별 Short Interest
- Borrow Fee
- Days to Cover
- Squeeze Risk Score
- 섹터/동종 비교

## 5.6 기관동향 화면
- 13F 변동 Top N
- 신규 진입/청산
- 대규모 매수/매도 이벤트
- 유명 기관(예: Bridgewater 등) 추적

## 5.7 알림 설정 화면
- 카테고리 알림 on/off
- 종목별 알림
- 최소 중요도 임계값(예: 7 이상)
- 공시 전용 알림
- 디스코드 웹훅 URL 등록/테스트

---

## 6. 데이터 소스별 역할 정리

| 소스 | 핵심 용도 | 수집 데이터 | 실시간성 수준 | API/스크래핑 및 안정성 | 노출 탭 | AI 활용 |
|---|---|---|---|---|---|---|
| 일반 뉴스 RSS/뉴스 API | 속보/매크로/기업 뉴스 확보 | 제목, 본문, 발행시각, 출처, URL | 높음(수초~수분) | 공식 API 우선, RSS 백업. 소스별 포맷 차이 큼 | 홈, 카테고리, 종목 | 요약, 분류, 티커 추출, 감성 |
| SEC/EDGAR | 공식 공시 신뢰 원천 | CIK, 티커, form type, filing time, 문서 링크 | 중~높음(보통 분 단위 반영) | 공식 제공 채널 존재. 레이트리밋/접속정책 준수 필수 | 공시, 종목, 홈 | 공시 요약, 뉴스 신뢰도 교차검증 |
| Finviz | 스크리너/시장 개요 | 기술지표, 밸류 지표, 스크리너 결과 | 중간(분~시간 단위) | 비공식 수집 시 구조 변경 리스크 높음. ToS 준수 필요 | 종목, 스크리너(2차) | 종목 컨텍스트 점수 보정 |
| Fintel | 공매도/기관 추적 보강 | short interest, borrow fee, ownership 변화 | 중간(일/주기 갱신 가능) | 공식 API 여부 플랜 의존. 비공식 수집은 유지보수 위험 | 공매도, 기관동향, 종목 | 숏 리스크·기관흐름 위험 신호 강화 |
| HedgeFollow | 헤지펀드 포트폴리오 변동 | 13F 기반 보유 변화, 신규/청산 | 낮음~중간(공시 주기성) | 비공식 스크래핑 가능성 큼. 구조 변경/법적 검토 필요 | 기관동향, 종목 | 중장기 수급 시그널 생성 |

### 실무 권장
- **1순위: 공식 API/공식 피드**
- 스크래핑은 `fallback`로 분리하고 장애 허용 설계(실패해도 전체 서비스는 정상)
- 소스별 `data_freshness_seconds`를 저장해 사용자에게 지연을 투명하게 표시

---

## 7. AI 분석 흐름

## 7.1 파이프라인 단계
1. `Ingest`: 원문 수신
2. `Normalize`: 스키마 통일
3. `Dedup`: 해시/유사도 기반 중복 제거
4. `Classify`: 멀티 라벨 카테고리
5. `Entity`: 티커/회사/인물 추출
6. `Summarize`: 1줄 요약
7. `Score`: 중요도(1~10), 감성(호재/악재/중립), 위험도
8. `Cluster`: 동일 이슈 군집화
9. `Cross-link`: 공시/공매도/기관 데이터 연결
10. `Alert`: 규칙+ML 하이브리드 경고 생성

## 7.2 핵심 규칙 예시
- `if earnings_news && same_day_8k_negative && short_interest_up && institutional_selling:`
  - 위험경고=`HIGH`
- `if positive_news && no_official_filing_support:`
  - 신뢰도 하향
- 동일 이슈 기사 N개 → 사용자 화면엔 **대표 카드 1개 + 관련 기사 수(N)**

## 7.3 AI 출력 스키마 예시

```json
{
  "news_id": "n_20260406_00123",
  "summary_one_line": "A사가 예상보다 낮은 가이던스를 발표하며 시간외 하락.",
  "categories": ["기업", "증시", "속보"],
  "tickers": ["A"],
  "sentiment": "bearish",
  "importance_score": 9,
  "risk_flag": true,
  "risk_reason": ["가이던스 하향", "공매도 증가"],
  "cluster_id": "cl_20260406_77",
  "confidence": 0.86
}
```

---

## 8. DB 설계 (PostgreSQL)

## 8.1 핵심 테이블

| 테이블 | 역할 | 주요 컬럼 |
|---|---|---|
| users | 사용자 계정 | id, email, password_hash, created_at |
| categories | 카테고리 마스터 | id, name, slug |
| news | 뉴스/이벤트 원문+AI 결과 | id, source, title, body, published_at, importance_score, sentiment, risk_flag, cluster_id |
| news_categories | 뉴스-카테고리 다대다 | news_id, category_id |
| tickers | 종목 마스터 | id, symbol, company_name, exchange |
| news_tickers | 뉴스-종목 다대다 | news_id, ticker_id, relevance_score |
| filings | SEC/EDGAR 공시 | id, ticker_id, cik, form_type, filed_at, url, ai_summary, importance_score |
| short_interest | 공매도 스냅샷 | id, ticker_id, as_of_date, short_interest, borrow_fee, days_to_cover, squeeze_score |
| hedgefund_changes | 기관/헤지펀드 보유변화 | id, fund_name, ticker_id, report_period, action, shares_change, position_value |
| clustered_issues | 이슈 군집 | id, title, representative_news_id, related_count, risk_level, started_at, updated_at |
| alerts | 시스템 생성 알림 | id, user_id(nullable), alert_type, severity, payload_json, created_at |
| user_watchlist | 사용자 관심종목 | user_id, ticker_id, created_at |
| user_notification_settings | 사용자 알림설정 | user_id, min_importance, discord_webhook_url, category_prefs_json, filing_only |
| sent_logs | 알림 발송 로그 | id, alert_id, channel(discord/push), status, sent_at, response_code |
| ingestion_jobs | 수집 작업 추적 | id, source, status, started_at, finished_at, error_message |

## 8.2 인덱스 권장
- `news(published_at desc)`
- `news(importance_score desc)`
- `news(risk_flag, published_at desc)`
- `news_categories(category_id, news_id)`
- `news_tickers(ticker_id, news_id)`
- `filings(ticker_id, filed_at desc)`
- `short_interest(ticker_id, as_of_date desc)`
- `hedgefund_changes(ticker_id, report_period desc)`
- `alerts(user_id, created_at desc)`

## 8.3 간단 DDL 예시

```sql
create table news (
  id text primary key,
  source text not null,
  title text not null,
  body text,
  url text,
  published_at timestamptz not null,
  ingested_at timestamptz not null default now(),
  importance_score int check (importance_score between 1 and 10),
  sentiment text check (sentiment in ('bullish','bearish','neutral')),
  risk_flag boolean default false,
  risk_score numeric(5,2),
  cluster_id text,
  ai_summary text,
  confidence numeric(4,3),
  raw_json jsonb
);
```

---

## 9. API 설계

## 9.1 REST API

### 1) GET /news
쿼리: `category`, `ticker`, `sort=latest|importance|risk`, `limit`, `cursor`

```json
{
  "items": [
    {
      "id": "n_001",
      "title": "A사 가이던스 하향",
      "summary": "예상보다 낮은 전망 제시",
      "categories": ["기업", "증시", "속보"],
      "tickers": ["A"],
      "importance_score": 9,
      "risk_flag": true,
      "published_at": "2026-04-06T12:00:12Z",
      "cluster": {"id": "cl_77", "related_count": 20}
    }
  ],
  "next_cursor": "eyJwdWJsaXNoZWRfYXQiOiIyMDI2..."
}
```

### 2) GET /news/{id}
```json
{
  "id": "n_001",
  "title": "A사 가이던스 하향",
  "body": "...",
  "ai": {
    "summary_one_line": "실적 전망 하향으로 변동성 확대 가능",
    "sentiment": "bearish",
    "importance_score": 9,
    "risk_flag": true
  },
  "related_filings": [{"id": "f_9001", "form_type": "8-K"}],
  "related_short_interest": {"borrow_fee": 11.2},
  "related_institutional_flow": {"net_action": "sell"}
}
```

### 3) GET /categories
```json
{
  "items": [
    "전체","경제","정치","증시","코인","기업","국제","속보","공시","공매도","기관동향"
  ]
}
```

### 4) GET /tickers/{symbol}
```json
{
  "symbol": "TSLA",
  "overview": {
    "ai_summary": "최근 24시간 악재 우세",
    "risk_level": "high"
  },
  "latest_news": [],
  "latest_filings": [],
  "short_interest": [],
  "hedgefund_changes": []
}
```

### 5) GET /filings
쿼리: `symbol`, `form_type`, `since`

### 6) GET /short-interest
쿼리: `symbol`, `since`

### 7) GET /hedgefund-flows
쿼리: `symbol`, `fund_name`, `period`

### 8) GET /alerts
쿼리: `severity`, `unread_only`

## 9.2 WebSocket API

- Endpoint: `WS /realtime-feed`
- Client subscribe 메시지:

```json
{
  "action": "subscribe",
  "channels": ["news", "filings", "short_interest", "institutional", "alerts"],
  "categories": ["속보", "공시"],
  "tickers": ["TSLA", "NVDA"],
  "min_importance": 7
}
```

- Server push 이벤트 예시:

```json
{
  "event": "news.upsert",
  "event_id": "evt_20260406_100001",
  "sent_at": "2026-04-06T12:00:15Z",
  "payload": {
    "id": "n_001",
    "title": "A사 가이던스 하향",
    "importance_score": 9,
    "risk_flag": true,
    "cluster_id": "cl_77"
  }
}
```

```json
{
  "event": "alert.created",
  "event_id": "evt_20260406_100099",
  "payload": {
    "severity": "high",
    "type": "risk_warning",
    "message": "실적+공시+공매도+기관매도 동시 발생"
  }
}
```

---

## 10. 실시간 처리 구조

## 10.1 갱신 주기(현실적 권장값)
- 일반 뉴스 RSS/API: **15~60초 주기** 폴링 + 공급자 push 있으면 병행
- SEC/EDGAR: **60~180초 주기** 확인
- Finviz/Fintel/HedgeFollow: **5~30분 주기**(소스 정책/갱신주기 따름)
- 종목 시세(연동 시): 별도 시세 벤더 정책 기준

## 10.2 웹소켓 + 폴링 백업
1. 서버는 새 이벤트 발생 시 WS로 즉시 push
2. 앱은 `last_event_id` 저장
3. 네트워크 끊김 시 재연결 후 `GET /news?since_event_id=...`로 누락 복구
4. WS 미지원 환경 대비 20~60초 폴링 fallback

## 10.3 중복 전송 방지
- 이벤트 고유키: `event_id`
- 클라이언트 dedup set(최근 N개)
- 서버 측 idemponent upsert
- 뉴스 dedup: URL canonical + 제목/본문 해시 + 임베딩 유사도

## 10.4 지연 표기
- 각 카드에 `source_published_at`, `ingested_at`, `delivered_at` 표시 가능
- 사용자에게 “실시간에 가깝지만 원천 지연 가능” 명시

---

## 11. 디스코드 연동 구조

## 11.1 트리거
- 중요 뉴스 발생(importance >= threshold)
- 신규 공시 감지(특정 form type 우선)
- 공매도 급변(전일/전주 대비 급등)
- 기관 대규모 매수/매도

## 11.2 메시지 포맷 예시

```json
{
  "username": "Market Sentinel",
  "embeds": [
    {
      "title": "[HIGH] 위험 경고 - TSLA",
      "description": "실적 가이던스 하향 + 공매도 증가 + 기관 순매도 감지",
      "color": 15158332,
      "fields": [
        {"name": "중요도", "value": "9/10", "inline": true},
        {"name": "카테고리", "value": "기업, 증시, 공시", "inline": true},
        {"name": "발생시각", "value": "2026-04-06T12:00:12Z", "inline": false}
      ],
      "url": "https://yourapp.example/news/n_001"
    }
  ]
}
```

## 11.3 안정성
- 웹훅 실패 시 재시도(지수 백오프)
- `sent_logs`에 성공/실패/응답코드 저장
- 같은 이벤트 반복 발송 방지(dedup key: `alert_id+channel`)

---

## 12. 폴더 구조 (권장 Monorepo)

```text
realtime-invest/
  apps/
    mobile/                     # React Native
      src/
        screens/
        components/
        hooks/
        services/
        store/
        navigation/
  services/
    api/                        # FastAPI REST + WS
      app/
        api/
        models/
        schemas/
        repositories/
        ws/
        core/
    collector/                  # 소스 수집 워커
      connectors/
        news/
        sec_edgar/
        finviz/
        fintel/
        hedgefollow/
      jobs/
      normalizers/
    analyzer/                   # AI 분석 워커
      pipelines/
      models/
      rules/
      clustering/
    notifier/                   # Discord/Push 알림
      channels/
      templates/
  packages/
    shared-types/
    shared-utils/
  infra/
    docker/
    k8s/
    terraform/
  docs/
    architecture.md
    api-spec.yaml
```

---

## 13. MVP 개발 순서

## Phase 0: 기초 인프라 (1주)
- FastAPI 기본 골격, PostgreSQL/Redis 연결
- 사용자/인증 최소 구조
- 뉴스 저장/조회 기본 API

## Phase 1: 핵심 수집 + 홈 피드 (2~3주)
- RSS/뉴스 API 수집기
- SEC/EDGAR 수집기
- 뉴스/공시 홈 노출
- WebSocket 실시간 피드 기본

## Phase 2: AI 최소 기능 (2주)
- 1줄 요약
- 카테고리 멀티라벨
- 중요도/호재악재
- 종목 추출

## Phase 3: 종목 화면 통합 (2주)
- 종목별 뉴스/공시 연결
- 기본 타임라인
- watchlist + 알림 설정

## Phase 4: 알림 (1주)
- Discord webhook 연동
- 중요도 threshold 및 카테고리별 알림

**MVP 완료 기준**
- “홈/카테고리/종목/공시/알림설정” 화면 동작
- 웹소켓 실시간 갱신 + 폴링 백업
- 기본 AI 요약/분류/스코어 동작

---

## 14. 2차 고도화 기능

1. Finviz/Fintel/HedgeFollow 심화 연동
2. 이슈 클러스터 고도화(멀티모달, 이벤트 그래프)
3. 개인화 랭킹(사용자 행동 기반)
4. 앱 푸시(FCM/APNs) 정식 도입
5. 백테스트형 “알림 성능 리포트”
6. 리스크 대시보드(섹터/테마 Heatmap)
7. 다국어(영/한) 자동 요약

---

## 15. 실제 구현 시 주의점

1. **법적/약관 준수**: Finviz/Fintel/HedgeFollow는 공식 API 계약 여부 확인 필수.
2. **스크래핑 리스크**: HTML 구조 변경 시 장애 가능성 큼 → connector 격리 + feature flag.
3. **지연 투명성**: “완전 실시간”이 아닌 “실시간에 근접”임을 UI/정책에 명시.
4. **AI 오판 리스크**: 점수/판정은 참고 정보이며 투자 조언이 아님을 명확히 고지.
5. **비용 관리**: LLM 호출은 배치/캐시/우선순위 큐로 최적화.
6. **관측성**: 소스별 수집 성공률, end-to-end latency, 알림 성공률 대시보드 필수.
7. **보안**: 웹훅 URL 암호화 저장, PII 최소화, 감사로그 유지.

---

## 16. 최종 요약

- 본 설계는 **웹소켓 + 짧은 주기 폴링 + 수집/분석 서버 분리**를 통해 현실적인 저지연 구조를 달성한다.
- 사용자에게는 과도한 정보 홍수 대신 **이슈 클러스터 + 위험 경고 중심 UI**를 제공해 빠른 판단을 돕는다.
- MVP는 뉴스/공시/기본 AI/디스코드 알림에 집중하고, 공매도/기관동향 심화는 2차에서 확장한다.
- 데이터 지연·비공식 수집 리스크를 전제로 한 안정성 설계(백업 경로, dedup, 관측성)가 핵심이다.

---

## 가장 먼저 만들어야 할 파일 목록

```text
# Backend
services/api/app/main.py
services/api/app/api/v1/news.py
services/api/app/api/v1/filings.py
services/api/app/ws/realtime.py
services/api/app/models/news.py
services/api/app/models/filing.py
services/api/app/schemas/news.py
services/api/app/core/config.py

services/collector/jobs/news_polling_job.py
services/collector/jobs/sec_polling_job.py
services/collector/connectors/news/rss_connector.py
services/collector/connectors/sec_edgar/sec_connector.py
services/collector/normalizers/news_normalizer.py

services/analyzer/pipelines/news_pipeline.py
services/analyzer/rules/risk_rules.py
services/analyzer/clustering/issue_clusterer.py

services/notifier/channels/discord_webhook.py
services/notifier/templates/high_risk_alert.json

# Infra
infra/docker/docker-compose.yml
infra/k8s/api-deployment.yaml
infra/k8s/worker-deployment.yaml

# Mobile
apps/mobile/src/screens/HomeScreen.tsx
apps/mobile/src/screens/CategoryScreen.tsx
apps/mobile/src/screens/TickerScreen.tsx
apps/mobile/src/screens/FilingsScreen.tsx
apps/mobile/src/screens/ShortInterestScreen.tsx
apps/mobile/src/screens/InstitutionalScreen.tsx
apps/mobile/src/screens/NotificationSettingsScreen.tsx
apps/mobile/src/services/realtime.ts
apps/mobile/src/services/api.ts

# Docs
docs/architecture.md
docs/api-spec.yaml
docs/mvp-checklist.md
```
