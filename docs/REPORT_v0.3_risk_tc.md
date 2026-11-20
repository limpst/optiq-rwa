# OptiQ-RWA — v0.3 거래비용 · SR/IR/MDD/DSR · 국면 라벨 검증
# OptiQ-RWA — v0.3 transaction costs, SR/IR/MDD/DSR, regime-label validation

출처: GitHub [limpst/optiq-rwa](https://github.com/limpst/optiq-rwa) main · `results/real/SUMMARY_REAL.md` · `results/regime_validation.md` · `results/qubo_bench.md` · `results/SUMMARY.md` (sweep) · 대시보드 [artifact](https://claude.ai/artifact/QbAXfoRRHvuhBF4nSW5Vd7) · 로컬 http://127.0.0.1:8793
단계: 4 (알파 검증) · 8 (거래비용 모형) · 9 (backtest) · 11 (성과 요인 분석). 기여 WP: OptiQ-RWA.

## Notation

| 기호 | 정의 |
|---|---|
| TC | transaction cost. 체결 수수료 + 결제 수수료 + spread + slippage |
| fee | Deribit option 체결 수수료 = min(기초자산 notional 0.03%, option 가격 12.5%) |
| SR | Sharpe ratio, 0 대비, 연율 = mean(r)/sd(r)·√365 |
| IR | information ratio, RWA 4.5% 대비 = (mean(r) − rwa/365)/sd(r)·√365 |
| MDD | 최대 낙폭 |
| DSR | deflated Sharpe ratio (Bailey & López de Prado 2014). RWA 초과수익의 SR 이 같은 탐색 N 개 중 최대 기대 SR 을 넘을 확률 |
| 하이라이트 | SR > 0 · IR > 0.5 · MDD ≥ −15% · DSR ≥ 0.95 · 60밤 이상 |
| payback | 1달러 지불당 회수액 |
| rich_iv | IV 가 실현 변동성보다 비싼 국면 라벨 |

## 요약

- 결론: base TC 를 넣으면 BTC 실데이터에서 하이라이트 규칙을 통과하는 전략은 **없다**. 합성 sweep 에서는 588 설정 중 8개 (events_underpriced 의 Idea 2 QUBO 선택) 만 통과하고, rich_iv 매도는 꼬리 (skew −5) 때문에 DSR 에서 떨어진다. 가장 좋은 strangle 매도 (m=1.5, frac 0.5) 의 최종 NAV 는 TC 없음 1.0130 → base 1.0106 → stress 0.9954 다. 0DTE OTM option 은 가격이 싸서 수수료 12.5% 상한이 걸리고, 프리미엄 1달러당 0.05~0.08 달러가 수수료다.
- 정정: QUBO SA 가 greedy 보다 못하던 것은 soft 예산 벌점이 너무 커서 SA 가 빈 해에 갇힌 구현 문제였다. 고친 뒤 SA = MILP (gap 0.00%). v0.1 의 "SA < greedy" 는 철회한다.
- 열린 항목: 국면 라벨 (rich_iv) 이 매도 우위를 골라내지 못한다 (BTC regime_follow IR −0.05 vs always_short 1.63). 라벨은 아직 신호가 아니다. 실제 호가 이력은 라이브 snapshot 으로 쌓는 중이다.

## 실험 설정

| 항목 | 값 |
|---|---|
| 실데이터 | Deribit 체결 VWAP chain, BTC 201밤 · SOL 95밤 (2026-05-01 ~ 11-18) |
| cost model | none · base (fee 0.03%/12.5% cap, 데일리 결제 수수료 면제) · stress (spread 2배, slippage +50%, 결제 수수료 0.015%) |
| 수수료 출처 | 2차 자료 (jeangalea.com, coincodecap). support.deribit.com 요율표는 직접 확인 못 함 |
| DSR N | 같은 아이디어의 파라미터 설정 수 (실데이터: 코인 × cost model × 아이디어, sweep: 시나리오 × cost model × seed × 아이디어) |
| 라벨 | `risk/regime.py` nearest-centroid, walk-forward 특징, 참조 = 합성 4 시나리오 |

## 결과

### TC 가 수익에 미치는 영향 (BTC, 같은 전략)

| 전략 | none | base | stress |
|---|---:|---:|---:|
| strangle 매도 m=1.5 wing 없음 frac 0.5 (61밤) 최종 NAV | 1.0130 | 1.0106 | 0.9954 |
| 프리미엄 1달러당 수수료 | 0 | 0.083 | 0.466 |

- base TC 는 수익의 약 1/5 을 가져간다. stress 는 수익을 없앤다. 매도 우위는 spread 모델 (10%) 가정에 크게 걸려 있어, 실제 호가 spread 를 라이브 snapshot 으로 재야 한다.

### SR · IR · MDD · DSR (BTC, base TC, IR 상위)

| 전략 | 밤 | 연 수익 | SR | IR | MDD | DSR | 통과 |
|---|---:|---:|---:|---:|---:|---:|:--:|
| strangle 매도 m=2.0 frac 0.25 | 41 | 6.0% | 76 | 17.5 | 0.0% | 1.00 | ✗ (41밤 < 60) |
| strangle 매도 m=1.5 frac 0.5 | 61 | 6.5% | 3.4 | 0.98 | −0.6% | 0.00 | ✗ (DSR) |
| 매일 콜 매수 m=1 bm=1 | 97 | 2.8% | 5.2 | −3.3 | 0.0% | 0.00 | ✗ |
| 이벤트 밤 콜 매수 m=1 bm=3 | 97 | 3.7% | 21 | −4.9 | 0.0% | 0.00 | ✗ |

- m=2.0 매도는 41밤 동안 한 번도 맞지 않아 분산이 0 에 가깝다. SR · DSR 이 큰 것은 꼬리를 표본에서 못 봤기 때문이다. 60밤 조건으로 걸렀다.
- SR 은 RWA 이자 (무위험 drift) 가 들어가서 거의 항상 양수다. 판별력은 IR 과 DSR 에 있다.

### 국면 라벨 검증 (BTC 202밤)

| 라벨 | 밤 | 콜 매수 1달러당 | strangle 매도 1달러 notional 당 | 매도 최악 밤 |
|---|---:|---:|---:|---:|
| rich_iv | 101 | −0.53 | +0.0001 | −0.0103 |
| fair_iv | 57 | −0.39 | +0.0004 | −0.0012 |
| base | 29 | −0.31 | +0.0005 | +0.0002 |

- rich_iv 밤의 매도 P&L 이 다른 밤보다 높지 않고, −1% 최악 밤도 rich_iv 안에 있었다. 라벨은 "IV 가 비싸다" 는 말은 맞히지만 "팔면 번다" 는 말은 못 맞힌다. 이유: 라벨 특징 (IV/RV · payback) 이 매도 손익의 꼬리를 보지 못한다.
- 콜 매수는 모든 라벨에서 손실이다.

### QUBO solver (results/qubo_bench.md, 84 변수 · K=7 · 30 seed)

| solver | MILP 대비 gap (lam 0.5) | 시간 |
|---|---:|---:|
| greedy | 1.09% (최악 6.9%) | ~0 s |
| 이전 SA (P2 = 2×scale, 120 sweeps) | 83.9% | 6 ms |
| 새 SA (P2 = 0.1×scale, 500×4, repair + polish) | 0.00% | 0.1 s |
| MILP (scipy) | 0 | 25 ms |

### 합성 sweep (TC 3종 · DSR, 4 시나리오 × 3 seed × 700 표본 외 밤)

하이라이트 통과: **8 / 576** (시나리오 × cost model × 설정). 전부 events_underpriced 시나리오의 Idea 2 (QUBO 이벤트 선택) 이고, stress TC 에서는 하나도 남지 않는다.

| 시나리오 | TC | 아이디어 | 설정 | 연 수익 | IR | MDD | DSR | DSR (seed 최소) |
|---|---|---|---|---:|---:|---:|---:|---:|
| events_underpriced | base | 2_qubo_event_selector | {'solver': 'greedy', 'lam': 0.0, 'budget_mult': 1.0} | 7.3% | 1.12 | -0.05% | 0.990 | 0.973 |
| events_underpriced | base | 2_qubo_event_selector | {'solver': 'greedy', 'lam': 0.5, 'budget_mult': 1.0} | 6.4% | 1.16 | -0.05% | 0.983 | 0.974 |
| events_underpriced | base | 2_qubo_event_selector | {'solver': 'milp', 'lam': 0.5, 'budget_mult': 1.0} | 5.8% | 1.09 | -0.05% | 0.958 | 0.937 |
| events_underpriced | base | 2_qubo_event_selector | {'solver': 'sa', 'lam': 0.5, 'budget_mult': 1.0} | 5.7% | 1.05 | -0.05% | 0.950 | 0.916 |
| events_underpriced | none | 2_qubo_event_selector | {'solver': 'greedy', 'lam': 0.0, 'budget_mult': 1.0} | 7.9% | 1.22 | -0.05% | 0.997 | 0.992 |
| events_underpriced | none | 2_qubo_event_selector | {'solver': 'greedy', 'lam': 0.5, 'budget_mult': 1.0} | 6.9% | 1.34 | -0.05% | 0.998 | 0.995 |
| events_underpriced | none | 2_qubo_event_selector | {'solver': 'milp', 'lam': 0.5, 'budget_mult': 1.0} | 6.0% | 1.25 | -0.05% | 0.986 | 0.979 |
| events_underpriced | none | 2_qubo_event_selector | {'solver': 'sa', 'lam': 0.5, 'budget_mult': 1.0} | 6.0% | 1.21 | -0.05% | 0.981 | 0.964 |

- rich_iv 의 프리미엄 매도 (`{'m': 1.0, 'frac': 1.0, 'skip_events': False, 'wing_m': None}`) 는 base TC 에서 연 29.0% · IR 1.39 · MDD -14.8% 이지만 **DSR 0.000** 으로 탈락한다. 밤 수익의 skew 가 약 −5, kurtosis 약 40 이라 DSR 의 비정규성 보정이 Sharpe 를 크게 깎는다. 매도 전략의 "높은 Sharpe" 는 꼬리를 대가로 산 것이라는 뜻이다. (TC 없음: 연 53.4%, DSR 0.029.)
- DSR 의 trials N 은 같은 아이디어의 파라미터 설정 수로 잡았다 (아이디어를 섞으면 V[SR] 이 부풀어 모두 0 이 된다). 이 선택이 결과를 좌우하므로 표에 seed 최소 DSR 도 같이 둔다.
- 실데이터 (BTC) 에서는 같은 규칙으로 통과 0 개. 41밤 m=2.0 매도도 같은 아이디어 안에서 보정하면 DSR 0.02 다.

## 정정 · 철회

| 항목 | 전 | 후 |
|---|---|---|
| QUBO SA vs greedy | SA 가 greedy 보다 못함 (v0.1 sweep) | 구현 문제 (soft 예산 벌점 과대). 고친 SA = MILP |
| 하이라이트 규칙 | SR>0 · IR>0.5 · MDD≥−15% · DSR≥0.95 | + 60밤 이상 (무분산 표본 차단) |

## 열린 항목

| 항목 | 상태 |
|---|---|
| Deribit 수수료 공식 확인 | 2차 자료. support.deribit.com 직접 확인 필요 |
| 실제 spread · depth | 라이브 snapshot 4개 (2026-11-20). 1주 이상 쌓인 뒤 spread 모델 교체 |
| 라벨 → 매도 꼬리 | 꼬리 특징 (실현 점프 빈도 · skew) 추가 필요 |
| paper 첫 주문 · 결제 | 2026-11-21 04:20 · 17:30 KST |

## English summary

Adding Deribit transaction costs removes every highlight-rule pass on real BTC data. The best short strangle (m=1.5, frac 0.5) ends at NAV 1.0130 without costs, 1.0106 with the base fee and 0.9954 under stress; cheap 0DTE options hit the 12.5% fee cap, so fees take 5-8 cents per premium dollar. The regime label does not isolate the selling edge: strangle P&L on rich_iv nights is not higher than elsewhere and the worst night sits inside rich_iv, so a regime-following path (IR −0.05) trails always-short (IR 1.63). The earlier "SA worse than greedy" result was an implementation artefact (over-sized soft budget penalty); the fixed SA matches the exact MILP. Highlight rule: SR > 0, IR > 0.5, MDD ≥ −15%, DSR ≥ 0.95, at least 60 nights.
