# Upbit AI Auto Trader (Desktop, PySide6)

안정성 중심의 업비트 자동매매 데스크톱 앱입니다. 현재 버전은 **실행 가능한 시뮬레이션 모드**를 기본 제공하며, 실제 서명 주문/실거래 WebSocket은 확장 지점으로 분리해 두었습니다.

## 실행
```bash
cd upbit_auto_trader
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python main.py
```

## 빠른 동작 확인 (헤드리스)
```bash
cd upbit_auto_trader
python - <<'PY'
import time
from core.engine import TradingEngine

engine = TradingEngine()
import threading
thr = threading.Thread(target=engine.run_forever, daemon=True)
thr.start()
time.sleep(2)
print(engine.get_status())
engine.stop()
thr.join(timeout=2)
PY
```

## 구현된 핵심 동작
- UI 스레드 / 매매 엔진 스레드 완전 분리 (`QThread`)
- AI 판단 비동기 큐 처리 (엔진 루프 non-blocking)
- Token Bucket 기반 API 트래픽 제어 (0.1초 대기)
- 전략 점수(80점 이상) + 리스크 + AI JSON 파싱의 3단계 진입 게이트
- RAG 장기기억(SQLite) 저장/검색
- AES-256-GCM 기반 로컬 비밀키 암호화 유틸
- 긴급 정지 버튼(확인 팝업 + 포지션 강제청산 훅)
- 로그/메모리 1,000개 제한 관리

## 폴더 구조
- `upbit_auto_trader/app`: PySide6 UI
- `upbit_auto_trader/core`: 엔진, 리스크, 스케줄러, 보안
- `upbit_auto_trader/ai`: Gemini 연동, 프롬프트, RAG 인터페이스
- `upbit_auto_trader/upbit`: 업비트 API/피드/호가 계산
- `upbit_auto_trader/database`: SQLite 저장소
- `upbit_auto_trader/calendar`: 매매 캘린더 요약
- `upbit_auto_trader/reports`: 일일 자동 리포트
- `upbit_auto_trader/notifications`: Discord/Telegram 알림 추상화
- `upbit_auto_trader/backtest`: 백테스트 엔진
- `upbit_auto_trader/design`: 스타일 테마
