# 디스코드 모의투자 봇

디스코드 커뮤니티 안에서 실제 주식 시세를 기반으로 모의(가상) 자금으로 매매를
체험할 수 있는 봇입니다. 은행(계좌/송금/출석 보너스)과 증권(시세/매수/매도/
포트폴리오/순위) 기능을 슬래시 커맨드로 제공합니다.

## 기능

### 은행
- `/계좌` — 계좌 조회 (최초 실행 시 자동 개설, 초기 자금 지급)
- `/잔고` — 현재 보유 현금 확인
- `/송금 대상 금액` — 다른 유저에게 가상 자금 송금
- `/출석` — 하루 1회 출석 보너스 수령
- `/거래내역` — 최근 거래 내역 조회

### 증권
- `/시세 종목` — 실시간 시세 조회 (한국: 6자리 종목코드 또는 종목명, 미국: 티커)
- `/환율` — 현재 원/달러 환율 조회 (미국 주식 매매에 적용되는 환율)
- `/매수 종목 수량` — 매수
- `/매도 종목 수량` — 매도 (실현 손익 표시)
- `/포트폴리오` — 보유 종목 평가금액 및 손익 확인
- `/순위` — 총 자산(현금+주식평가액) 기준 서버 랭킹

미국 주식은 실시간 원/달러 환율을 적용해 원화로 환산한 금액이 계좌에서
차감/입금됩니다.

## 아키텍처

```
bot/
  config.py          # 환경변수 설정
  db/
    models.py        # User(계좌), Holding(보유종목), Transaction(거래내역)
    base.py          # SQLAlchemy async 엔진/세션
  services/
    market.py        # yfinance 기반 시세/환율 조회, 종목 코드 매핑
    bank.py           # 계좌 생성, 송금, 출석 보너스, 거래내역
    trading.py        # 매수/매도, 포트폴리오 평가
  cogs/
    bank.py           # 은행 관련 슬래시 커맨드
    trading.py        # 증권 관련 슬래시 커맨드
    leaderboard.py    # 순위 커맨드
  main.py             # 봇 엔트리포인트
data/kr_stocks.json    # 한글 종목명 -> 종목코드 매핑 (자주 쓰이는 종목 위주)
scripts/init_db.py     # DB 테이블 생성 스크립트
```

새로운 자산군(예: 부동산)을 추가할 때는 이 구조를 그대로 따라가면 됩니다:
`services/realestate.py`에 매수/매도/평가 로직을, `cogs/realestate.py`에
관련 슬래시 커맨드를 추가하고, `db/models.py`에 `Property`/`PropertyHolding`
같은 테이블을 추가하는 식입니다. `Holding`과 유사하게 실제 시세(예: 부동산
실거래가 API)를 조회해 원화로 환산하고 `cost_basis_krw` 방식으로 손익을
계산하면 기존 증권 로직과 동일한 패턴을 재사용할 수 있습니다.

## 실행 방법

### 1. 의존성 설치

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. 환경변수 설정

```bash
cp .env.example .env
```

`.env`를 열어 다음 값을 채워주세요.

- `DISCORD_TOKEN`: [Discord Developer Portal](https://discord.com/developers/applications)에서
  발급받은 봇 토큰. 애플리케이션 생성 → Bot 탭에서 토큰 생성 → `applications.commands`,
  `bot` 스코프와 필요한 권한을 부여해 서버에 초대.
- `DATABASE_URL`: PostgreSQL 접속 문자열 (`postgresql+asyncpg://...` 형식)
- `INITIAL_BALANCE`: 최초 계좌 개설 시 지급하는 가상 자금 (기본 1천만원)
- `DAILY_BONUS`: 출석 보너스 금액
- `GUILD_ID`: (선택) 개발 중 특정 서버에 슬래시 커맨드를 즉시 반영하고 싶을 때 설정

### 3. PostgreSQL 준비

로컬에 Docker가 있다면:

```bash
docker compose up -d
```

### 4. DB 테이블 생성

```bash
python -m scripts.init_db
```

### 5. 봇 실행

```bash
python -m bot.main
```

## 테스트

네트워크 호출이 필요 없는 순수 로직(포맷팅, 종목 코드 매핑)에 대한 단위 테스트가
포함되어 있습니다.

```bash
pip install -r requirements-dev.txt
pytest
```

## 참고

- 시세는 [yfinance](https://github.com/ranaroussi/yfinance)를 통해 Yahoo Finance에서
  가져옵니다. 한국 종목은 `.KS`(코스피)/`.KQ`(코스닥) 접미사를 자동으로 시도합니다.
- `data/kr_stocks.json`에 없는 한국 종목은 6자리 종목코드를 직접 입력하면 됩니다.
- 실거래가 아닌 모의투자이므로 매수/매도는 실시간 종가 기준 체결로 즉시 처리됩니다
  (호가창, 체결 지연 등은 구현하지 않았습니다).
