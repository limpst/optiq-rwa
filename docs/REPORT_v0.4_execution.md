# OptiQ-RWA — v0.4 실행 규칙 실험: 게이트 · spread · maker · intraday · condor
# OptiQ-RWA — v0.4 execution-rule experiments: gate, spread, maker, intraday, condor

출처: GitHub [limpst/optiq-rwa](https://github.com/limpst/optiq-rwa) main (2026-11-23) · `results/maker_backfill.md` · `results/intraday_backfill.md` · `paper/gate_view.py` · 대시보드 [artifact](https://claude.ai/artifact/QbAXfoRRHvuhBF4nSW5Vd7) v23
단계: 8 (거래비용) · 10 (주문 실행) · 11 (모니터링). 기여 WP: OptiQ-RWA.

## Notation

| 기호 | 정의 |
|---|---|
| spread | (ask − bid) / mid. 매수자는 mid 보다 ask/mid − 1 만큼 비싸게 산다 |
| fee | Deribit 체결 수수료 min(notional 0.03%, 프리미엄 12.5%). 0DTE 는 12.5% 상한이 걸림 |
| payback | 결제 payoff / 지불 가격. 1 미만이면 손해 |
| 게이트 (Idea 8) | 기대 결제가치 (보정 payback 의 단측 한계 × mid) − 체결가 − fee > 0 일 때만 주문 |
| maker | mid 에 지정가를 걸어 두고 이후 snapshot 에서 시장이 통과하면 체결로 보는 paper 규칙 |
| 역선택 | 지정가 / 체결 순간 mid − 1. 양수면 그 순간의 공정가보다 비싸게 산 것 |
| tp / sl | 목표 되사기 (ask 기준) / 손절 (mid 기준) |
| cw | cheap-wing: wing ask ≤ short bid × 0.5 일 때만 condor 를 보냄 |
| DSR | Deflated Sharpe Ratio. 탐색 수 · 비정규성 · 표본 길이로 보정한 Sharpe (v0.3 보고서) |

## 요약

- 결론: 0DTE option 의 매수 edge 는 체결 방식으로 만들 수 없다. spread (BTC m≈1 콜 ask 가 mid 보다 10.5%) 와 수수료 상한 (12.5%) 을 합치면 손익분기 payback 이 1.24 인데 실현 payback 은 0.6~0.8 이다. 게이트는 점추정으로도 열리지 않고, maker 지정가는 역선택 (고정 mid 26%, pegged 16%) 으로만 체결된다.
- 정정: 없음. 단, 이전 보고의 "z·se 가 게이트를 막는다" 는 추정은 틀렸다. 점추정으로도 닫히므로 원인은 spread + fee 다.
- 열린 항목: 매도 쪽은 3밤 모두 OTM 으로 끝나 꼬리 밤을 못 봤다. condor 는 wing ask > short bid 로 진입부터 순지출이다. 13개 paper 전략이 11-24 04:20 KST 부터 같은 호가로 돌아 밤마다 비교한다.

## 실험 설정

| 항목 | 값 |
|---|---|
| 데이터 | 라이브 Deribit order book snapshot 15분, 2026-11-20 ~ 23 (181개), depth 5, universe + SOL_USDC |
| 진입 시각 | 19:20 UTC (04:20 KST) snapshot, 만기 6~26h |
| 체결 가정 | taker: 매수 ask · 매도 bid. maker: mid 지정가, 이후 snapshot 에서 ask ≤ 지정가 (매수) · bid ≥ 지정가 (매도) 면 체결 |
| 수수료 | Deribit 공식 요율 (taker 3 bps · cap 12.5%, USDC 데일리 maker 0) |
| 표본 | 3밤. 꼬리 밤 없음 |

## 결과

### 1. spread 분포 (snapshot 778개)

| base | spread 중앙값 | p10 · p90 | ask/mid − 1 |
|---|---:|---|---:|
| BTC | 21% | 14% · 40% | 10.5% |
| ETH | 21% | 13% · 43% | 10.7% |
| SOL_USDC | 48% | 25% · 132% | 24% |

- 가장 좁은 시간대 (BTC 10:00 UTC) 도 p10 이 14% 라 "좁은 밤만 산다" 는 조건으로 풀리지 않는다.

### 2. 게이트 역산 (현재 호가, 9 leg)

| 조건 | 열린 leg |
|---|---:|
| z = 1.645 (기본) | 0 / 9 |
| z = 1.0 | 0 / 9 |
| 점추정 | 0 / 9 |

- BTC m=1 콜: mid 39.8, ask 49.0, fee 6.1. 점추정 payback 0.82 × 39.8 = 32.5 < 55.1. 매수 게이트가 열리려면 payback 하한이 1.38 을 넘어야 한다.

### 3. maker 지정가 백필 (3밤)

| 규칙 | leg 체결률 | 체결까지 | 역선택 | 체결된 콜 payback |
|---|---:|---:|---:|---:|
| 고정 mid, 콜 매수 | 100% | 2.8 h | +26% | 0.00 |
| pegged (15분 mid 추적), 콜 매수 | 92% | 1.1 h | +16% | 0.00 |
| 고정 mid, condor 패키지 | 10% | 1.9 h | +29~43% | – |

- 체결은 option 이 싸진 뒤 (시간 가치 소멸 · spot 이탈) 지정가에 닿는 것이다. 체결된 콜 13개는 전부 0 으로 끝났다.

### 4. intraday 매도 (m≈±1.5 strangle leg, 27 leg)

| 규칙 | 평균 /$ 프리미엄 | 최악 | 조기 청산 |
|---|---:|---:|---:|
| 만기 보유 | 0.875 | 0.875 | 0% |
| 목표 50% 되사기 | 0.432 | 0.312 | 82% |
| 목표 50% + 손절 2배 (ask 기준) | −0.523 | −3.148 | 89% |
| 목표 50% + 손절 2배 (mid 기준) | 0.432 | 0.312 | 82% |

- option mid 는 진입 +6h 에 25~45% 로 떨어진다. ask 기준 손절은 spread 스파이크에 헛걸린다. 손절은 mid 로 판단하고 체결만 ask 로 한다.
- 보유의 최악 0.875 는 수수료만 뺀 값이다. 3밤에 꼬리가 없었을 뿐이다.

### 5. condor 구조

- wing (m≈2.5) ask 합 > short (m≈1.5) bid 합 → 진입부터 순지출 (스크래치 실행 −3,306 USD / 250k notional). 예: ETH 1760-C bid 0.17 vs 1780-C ask 0.35.
- 대응: `short_condor_cw` 쌍둥이 (wing ask ≤ short bid × 0.5 만). 지금 호가로는 ETH 만 통과.

### 6. 오늘 밤부터 돌아가는 paper 전략 13개

| 묶음 | 전략 | 실행 규칙 |
|---|---|---|
| 기준 | yield_calls · short_condor · regime_switch | taker 즉시 체결 |
| 게이트 | *_gated (z 1.645) · *_gated_z1 (z 1.0) | Idea 8 게이트 통과 시만 |
| maker | yield_calls_maker · short_condor_maker | mid 지정가, 17:30 결제 때 판정 |
| 관리 | short_condor_tp50 | 목표 50% (ask) · 손절 1배 (mid) |
| 구조 | short_condor_cw | cheap-wing |

## 정정 · 철회

| 항목 | 전 | 후 |
|---|---|---|
| 게이트가 닫힌 원인 | z·se (얇은 보정 표본) | spread + 수수료 상한. 점추정으로도 닫힘 |
| 손절 트리거 | ask 합 | mid 합 (ask 스파이크 면역), 체결은 ask |

## 열린 항목

| 항목 | 상태 |
|---|---|
| 꼬리 밤 표본 | 0 / 3밤. 매도 DSR · 손절 규칙 판단 보류 |
| 라이브 payback 재추정 | 라이브 체인 (`data/live/`) 축적 중 (다른 세션) |
| pegged maker 쌍둥이 | 백필만. 15분 작업에 fill 판정을 붙여야 함 |
| 운영 | 11-21 · 22 주문 실패 (DB 잠금) 수정 완료, 11-24 04:20 첫 전체 실행 |

## English summary

Execution rules cannot manufacture a buying edge in 0DTE crypto options. With BTC m≈1 call asks 10.5% above mid and the 12.5% fee cap, break-even payback is 1.24 against realised 0.6–0.8; the idea-8 gate stays shut even at the point estimate, so spread plus fee, not the z·se bound, is binding. Resting limits at mid fill (100% static, 92% pegged) only after the option has cheapened, paying 26% (16% pegged) above the mid at fill, and every filled call expired worthless. On the selling side, 27 strangle legs over three nights all expired OTM (0.875 per $ after fees); a 50% buy-back closes 82% of legs within 5.7h for 0.43 per $, and an ask-based 2x stop is triggered by spread spikes (mean −0.52, worst −3.15) while a mid-based stop is not. Condors start cash-negative because wing asks exceed short bids. Thirteen paper strategies now run nightly on identical quotes to compare these rules.
