# Upbit AI Auto Trader (Desktop)

PySide6 기반의 로컬 전용 업비트 AI 자동매매 플랫폼 초기 구조입니다.

## 특징
- UI 스레드/매매 엔진 분리(QThread)
- 로그 1000개 제한 + 주기적 GC
- 리스크 매니저(일 손실 제한, 동시 보유 제한, 연속 손절 제한)
- Token Bucket Rate Limiter 모듈
- Gemini 비동기 큐 서비스 스켈레톤
- SQLite 거래 기록 저장소
- 다크 테마 + 긴급 정지 버튼

## 실행
```bash
cd upbit_auto_trader
python main.py
```

## 구조
```text
upbit_auto_trader/
├─ main.py
├─ config.yaml
├─ requirements.txt
├─ app/
├─ core/
├─ ai/
├─ upbit/
├─ database/
├─ calendar/
├─ reports/
├─ notifications/
├─ backtest/
└─ design/
```
