# OptiQ-RWA — v0.2 라이브 수집 · paper trading · 실데이터 backtest
# OptiQ-RWA — v0.2 live collection, paper trading, real-data backtest

출처: GitHub [limpst/optiq-rwa](https://github.com/limpst/optiq-rwa) commit c74821d · 결과 `results/real/SUMMARY_REAL.md`, `results/SUMMARY.md` · 대시보드 [artifact](https://claude.ai/artifact/QbAXfoRRHvuhBF4nSW5Vd7) · 로컬 http://127.0.0.1:8793
단계: 2 (데이터) · 4 (알파 검증) · 9 (backtest) · 10 (주문 실행 dry-run). 기여 WP: OptiQ-RWA.

## Notation

| 기호 | 정의 |
|---|---|
| RWA | Real-World Asset. 토큰화 국채. 연 4.5% 이자 가정 |
| 0DTE | 당일 (하룻밤) 만기 option. Deribit 08:00 UTC 결제 |
| IV | implied volatility (연율) |
| σ√T | IV × √(h/8760). 하룻밤 표준 움직임 |
| m | ln(K/S) / σ√T. strike 거리 (σ√T 단위) |
| payback_ask | 1달러 ask 지불당 회수액 |
| P(ITM) | 만기에 결제가가 strike 를 넘을 확률 |
| NAV | paper 계좌 평가액 (USD) |
| universe | 하루 option 거래량 10억 원 이상인 base |

## 요약

- 결론: 지난 6개월 BTC 데일리 콜을 ask 에 사면 1달러당 0.59 (m=1) 를 돌려줬다. 매일 매수 (Idea 1) 는 RWA 이자보다 1.3%p 낮았고, m=1.5 strangle 매도는 61밤에서 +3.6%p 였다. 참고 사례 (SOL, 0.65) 와 같은 방향이다.
- 정정: 없음 (v0.1 의 매도 전략 wing 비용 누락 정정은 v0.1 에서 반영됨).
- 열린 항목: 실제 호가 이력이 없어 backtest 호가는 체결 VWAP + 모델 spread 다. 라이브 snapshot 으로 지금부터 쌓는다. SOL 과거 chain 은 매우 얇다.

## 실험 설정

| 항목 | 값 |
|---|---|
| 실데이터 | Deribit 체결 이력 (history.deribit.com), 19:20 UTC ±20분 VWAP, 2026-05-01 ~ 11-18 |
| BTC chain | 201밤, 1,494 traded strikes (m 격자당 59~147밤) |
| SOL chain | 95밤, 275 traded strikes (m 격자당 2~61밤) |
| spread 모델 | half-spread = 10% × mid + 2bp (synthetic 과 동일) |
| warmup | 40밤, 이후 표본 외 |
| 라이브 수집 | 15분 snapshot, 9 base, book summary 전 종목 + depth 5 (universe + SOL_USDC) |
| universe 필터 | 24h option volume_usd × 1,400 ≥ 10억 원 |
| paper | NAV 1,000,000 USD, 매수 = best ask, 매도 = best bid, 결제 = delivery price |

## 결과

### Universe (2026-11-20 24h)

| base | 거래량 (억 원) | 통과 |
|---|---:|:--:|
| BTC | 796.5 | ✅ |
| ETH | 116.5 | ✅ |
| BTC_USDC | 33.0 | ✅ |
| SOL_USDC | 6.7 | ❌ |
| ETH_USDC · HYPE · XRP · AVAX · TRX | 0.2~4.8 | ❌ |

- SOL_USDC 는 10억 원 기준의 2/3 다. 호가가 얇아 전략 자본은 넣지 않고 focus base 로 수집만 한다.

### Idea 4 · 확률 보정 (BTC, calls)

| m | n | P(ITM) 모델 | P(ITM) 실제 | payback_mid | payback_ask |
|---:|---:|---:|---:|---:|---:|
| 0.0 | 114 | 48.7% | 46.5% | 0.80 | 0.70 |
| 0.5 | 127 | 29.7% | 23.6% | 0.63 | 0.53 |
| 1.0 | 127 | 14.3% | 10.2% | 0.77 | 0.59 |
| 1.5 | 125 | 6.9% | 5.6% | 0.96 | 0.62 |

- 실제 ITM 비율이 모든 m 에서 모델보다 낮다. 지난 6개월 BTC IV 는 실현 변동성보다 높았다 (rich_iv 쪽). 그래서 콜 매수의 payback 이 1 을 밑돈다.
- mid 와 ask 의 차이 (0.77 → 0.59) 가 spread 비용이다. spread 모델이 10% 이므로 실제 호가로 다시 재야 한다.

### Idea 1 · 3 (BTC, 표본 외)

| 전략 | 밤 수 | 연 수익 | RWA 대비 | 최악 밤 |
|---|---:|---:|---:|---:|
| RWA only | - | 4.5% | 0 | 0 |
| 매일 콜 매수 m=1, bm=1 | 97 | 3.2% | −1.3%p | 0.0% |
| 매일 콜 매수 m=1, bm=3 | 97 | 0.3% | −4.2%p | −0.02% |
| strangle 매도 m=1.5, wing 없음, frac 0.5 | 61 | 8.1% | +3.6%p | −0.5% |
| iron condor m=1.5 / wing 2.5, frac 0.5 | 13 | 0.9% | −3.6%p | −0.02% |

- 매수는 모든 파라미터에서 RWA 보다 못했다. 이유는 payback_ask < 1. 그래서 매수는 IV 가 싼 밤 (이벤트) 으로 제한해야 한다.
- wing 없는 매도가 가장 좋았지만 61밤 표본이고 꼬리 (큰 밤) 를 한 번도 맞지 않았다. wing 을 산 13밤은 손해였다. 매도 우위는 더 긴 표본과 실제 wing 호가가 있어야 판단할 수 있다.

### Paper book

- 2026-11-20 기준 주문 없음. 첫 dry-run 주문은 04:20 KST (19:20 UTC), 첫 결제는 17:30 KST 에 난다.

## 정정 · 철회

| 항목 | 전 | 후 |
|---|---|---|
| 없음 | - | - |

## 열린 항목

| 항목 | 상태 |
|---|---|
| 실제 bid/ask 이력 | 라이브 snapshot 으로 축적 중 (2026-11-20 시작) |
| 이벤트 캘린더 | 없음 → FOMC · CPI · 언락 날짜 수집 예정 |
| 국면 판별 | 미구현 → 진행 중 |
| QUBO SA < greedy | 진행 중 (벤치 + MILP) |
| SOL 표본 | 얇음. 수치는 참고만 |
| API key 권한 | trade 포함. read-only key 로 교체 권고 |

## English summary

Over the last six months BTC daily calls bought at the ask returned 0.59 per dollar at m=1 (mid 0.77); realised P(ITM) sat below the model at every strike, so IV was rich versus realised volatility. Buying calls every night under-performed the RWA yield by 1.3 pp; selling an m=1.5 strangle without wings earned +3.6 pp over 61 nights but never met a tail night, and the winged condor lost on its 13-night sample. The universe filter (KRW 1bn/day) passes only BTC, ETH and BTC_USDC; SOL_USDC is at 0.67bn and is collected as a focus base only. v0.2 adds a 15-minute Deribit snapshot collector into SQLite, a dry-run paper engine (no private endpoints), period returns, a FastAPI + lightweight-charts dashboard and launchd jobs. Quotes in the historical backtest are trade VWAPs plus a modelled spread, not executable prices.
