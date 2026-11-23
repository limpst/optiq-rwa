# OptiQ-RWA

**RWA 기반 수익 + 크립토 데일리(0DTE) 옵션 오버레이 최적화**

토큰화 실물자산(RWA, 예: 토큰화 국채)으로 안정적인 기초 수익을 확보하고, 그 수익을 예산으로 삼아 크립토 데일리 옵션 포지션을 운용·최적화하는 사이드 프로젝트입니다. 데일리 옵션은 손실이 프리미엄으로 제한되고 하룻밤 사이에 수익이 크게 날 수 있는 구조지만, 평균적으로 싸지는 않습니다. 이 프로젝트는 **어떤 시장 조건에서, 어떤 구조가, 언제 의미가 있는지**를 데이터로 판별하는 것이 목표입니다.

> 상태: 🧪 v0.2 — 라이브 Deribit 수집 (SQLite · 15분 launchd) · dry-run paper 엔진 · 실데이터 backtest · 대시보드. 실주문 없음.

## 링크 (2026-11-20)

| 무엇 | 어디 |
|---|---|
| 대시보드 artifact (claude.ai, 비공개 링크) | https://claude.ai/artifact/QbAXfoRRHvuhBF4nSW5Vd7 |
| 로컬 대시보드 | http://127.0.0.1:8793 (`PYTHONPATH=src uvicorn optiq_rwa.dashboard.app:app --port 8793`) |
| 정적 대시보드 (GitHub Pages 를 docs/ 로 켜면 공개) | `docs/index.html` |
| 보고서 v0.2 (라이브 수집 · paper · 실데이터) | `docs/REPORT_v0.2.md` · [Notion](https://app.notion.com/p/41e6585be6ea81d3b1b9c648d0ef4632) |
| 보고서 v0.3 (TC · SR/IR/MDD/DSR · 국면 검증) | `docs/REPORT_v0.3_risk_tc.md` · [Notion](https://app.notion.com/p/41e6585be6ea810fb0d0dfde5e0f0181) |
| 결과 | `results/SUMMARY.md` (합성 sweep) · `results/real/SUMMARY_REAL.md` (실데이터) · `results/regime_validation.md` · `results/qubo_bench.md` |
| Deribit 수수료 (공식) | https://support.deribit.com/hc/en-us/articles/25944746248989-Fees |
| 참고 사례 | [SOL daily call, LinkedIn](https://lnkd.in/p/gN5Us43k) |


## 실시간 현황

| 무엇 | 어디 | 갱신 |
|---|---|---|
| 라이브 수집 · paper NAV(게이트 전/후) · 현재 국면 · OOS walk-forward(전체 + 최근 30밤 DSR) | [`status` 브랜치](https://github.com/limpst/optiq-rwa/blob/status/README.md) | 매시간 (커밋 1개를 force-push, main 기록 무변경) |
| 같은 내용의 일별 스냅샷 | [`docs/status.md`](docs/status.md) | 매일 17:30 KST settle 때 DB 와 함께 main 커밋 |
| 실패 · 정지 알림 | macOS 알림 + `data/logs/alerts.log`, `.env` 의 `OPTIQ_ALERT_WEBHOOK` 이 있으면 Teams / Slack 으로 전송 | 단계 실패 즉시 · 수집 45분 정지 시 1회 |

---

## v0.2 — 라이브 데이터 · paper trading · 대시보드 (2026-11-20)

단계: 2 (데이터) · 4 (알파 검증) · 9 (backtest) · 10 (주문 실행, dry-run). 기여 WP: OptiQ-RWA.

### 구성

| 모듈 | 역할 |
|---|---|
| `src/optiq_rwa/data/store.py` | SQLite 한 파일 (`data/optiq.db`) + Parquet 일별 export (`data/parquet/`) |
| `src/optiq_rwa/data/live.py` | 15분 snapshot: instruments · book summary (전 종목) · order book depth 5 + greeks (universe + focus base, 가까운 만기 2개, \|m\| ≤ 2.5) · index · delivery price |
| `src/optiq_rwa/paper/engine.py` | dry-run 주문. 매수 = best ask, 매도 = best bid. 결제 = Deribit delivery price. private endpoint 호출 없음 |
| `src/optiq_rwa/backtest/periods.py` | 일 · 주 · 월 기간별 수익 · 초과 · MDD |
| `src/optiq_rwa/dashboard/app.py` | FastAPI + TradingView lightweight-charts. `scripts/export_dashboard.py` 가 정적 `docs/index.html` 생성 |
| `scripts/run_real_backtest.py` | `data/raw/*_chain.parquet` (Deribit 체결 이력) 로 Idea 1 · 3 · 4 backtest → `results/real/` |
| `scripts/launchd/` | `com.optiq.snapshot` (900초) · `com.optiq.readme` (3600초, `daily.sh status` → `status` 브랜치) · `com.optiq.trade` (04:20 KST) · `com.optiq.settle` (17:30 KST, 결제 · NAV · export · 라이브 체인 · OOS walk-forward 재계산 · `docs/status.md` · DB commit) |
| `scripts/update_status.py` | `docs/status.md` 생성: 라이브 수집 현황 · paper NAV · 실행 게이트 전/후 비교 · 현재 국면 · OOS walk-forward 지표(전체 + 최근 30밤, 최근 구간 DSR 별도) |
| `src/optiq_rwa/paper/gate.py` | 아이디어 8 실행 게이트: 기대 결제가치(아이디어 4 보정 payback × 라이브 mid) − ask/bid − 수수료 > 0 인 패키지만 진입. payback 은 점추정이 아니라 단측 하한(매수 payback − z·se, 매도 + z·se, z = `OPTIQ_GATE_Z` 기본 1.645)이고, 라이브 호가 밤이 쌓일수록 n_live / (n_live + 60) 가중으로 라이브 추정치 쪽으로 재보정. paper 엔진에 `*_gated` 쌍둥이 전략으로 적용, 보류는 `status='gated'` 로 기록 |
| `src/optiq_rwa/data/livechain.py` | 라이브 호가(19:20 UTC snapshot, 실제 best bid/ask)로 매일 밤 체인 생성(BTC · ETH · SOL, ETH 는 라이브 전용) → `data/live/`. walk-forward 스크립트는 과거 체결 체인 + 라이브 밤을 이어 붙여 표본 외 구간을 매일 늘림 |
| `scripts/notify.sh` | 스케줄 단계 실패 알림 (macOS 알림 · `alerts.log` · 선택: Teams / Slack webhook). 매시간 작업은 마지막 snapshot 이 45분 넘게 없으면 수집 정지로 보고 정지 1회당 한 번 알림 |

### Universe 필터 (하루 option 거래량 10억 원 이상, 2026-11-20 24h)

| base | 24h volume | 통과 |
|---|---:|:--:|
| BTC (inverse) | 882억 원 | ✅ |
| ETH (inverse) | 116억 원 | ✅ |
| BTC_USDC | 33억 원 | ✅ |
| SOL_USDC | 6.7억 원 | ❌ (focus base 로 수집만) |
| ETH_USDC · HYPE · XRP · AVAX · TRX | 0.2~4.8억 원 | ❌ |

### 실데이터 backtest (Deribit 체결 VWAP chain, 2026-05-01 ~ 11-18)

호가는 19:20 UTC ±20분 체결 VWAP + 모델 spread(10% + 2bp). 실제 체결 가능 가격이 아니다. 자세한 표: `results/real/SUMMARY_REAL.md`.

| 코인 | 항목 | 값 |
|---|---|---|
| BTC | m=1 콜 payback (mid / ask) | 0.77 / 0.59 |
| BTC | 모델 P(ITM) vs 실제, m=1 | 14.3% vs 10.2% |
| BTC | Idea 1 매일 콜 매수 (m=1, bm=1) | 연 3.2% (RWA 4.5% 대비 −1.3%p) |
| BTC | Idea 3 strangle 매도 m=1.5 wing 없음 frac 0.5 (61밤) | 연 8.1% (+3.6%p), 최악 밤 −0.5% |
| SOL | m=1 콜 payback (mid / ask) | 0.78 / 0.66 (32밤, 얇음) |

해석: 참고 사례 (SOL, ask 기준 0.65) 와 같은 결과다. 지난 6개월 BTC · SOL 데일리 콜은 ask 로 사면 1달러당 0.6~0.7 달러를 돌려줬다. 매수는 IV 가 싼 밤을 골라야 하고, 매도는 꼬리 (wing) 비용을 낸 뒤에도 남는지 더 긴 표본이 필요하다.

### 국면 판별 (regime) · 이벤트 캘린더 (2026-11-20 추가)

- `src/optiq_rwa/risk/regime.py`: walk-forward 특징 (IV/RV · 최근 20/60밤 payback · P(ITM) 격차 · IV 백분위) → 합성 4 시나리오 중심점에 nearest-centroid. 결과 `results/regime_summary.md`, `results/regime_history.csv`. `scripts/run_regime.py`.
- 현재 라벨: BTC · SOL · ETH 모두 **rich_iv** (IV 가 실현 변동성보다 비쌈) → action "프리미엄 매도 (Idea 3, wing 포함)". BTC 는 5~7월 rich_iv, 8~9월 fair_iv, 11월 다시 rich_iv.
- 한계: rich_iv 만 다른 셋과 또렷이 갈린다. base · fair_iv · events_underpriced 는 특징이 거의 같다. 실데이터 chain 이 얇아 (BTC 7 · SOL 2.6 호가/밤) 라벨은 신호가 아니라 기울기로 읽는다.
- `data/events.csv` + `src/optiq_rwa/data/events.py`: FOMC 2026 (8회, 확정) · 2027 (8회, tentative) · US CPI 2026~27-02 (BLS) · HYPE 언락 (uncertain). 19:20 UTC 진입이면 FOMC · CPI 수치는 이미 나온 뒤라 "event night" 은 사후 움직임이다.
- 실데이터 재실행: BTC event night 7밤의 m=1 콜은 전부 0 으로 끝났다 (payback 0). event_only 매수도 RWA 에 못 미쳤다 (−0.8%p). 합성 sweep 의 "이벤트 과소평가" 가정은 지난 6개월 BTC 에서는 성립하지 않았다 (n=7, 참고만).

### 거래비용 (TC) · SR / IR / MDD / DSR · 하이라이트 규칙 (2026-11-20 추가)

- `src/optiq_rwa/backtest/costs.py`: Deribit 수수료 모형. 체결 수수료 = min(기초자산 0.03%, option 가격의 12.5%) (maker · taker 동일), 결제 수수료 0.015% (12.5% 상한, 데일리 option 은 면제 → 기본 0), spread 는 ask/bid 체결로 이미 반영. cost model: `none` · `base` · `stress` (spread 2배 + slippage 50% + 결제 수수료). 출처: Deribit 공식 요율표 (support.deribit.com/hc/en-us/articles/25944746248989-Fees, 2026-11-20 확인). Standard tier 3/3 bps · cap 12.5%, USDC 데일리 linear option 은 maker 0 bps (2026-11-10 ~ 2027-01-31), taker 3 bps. 매수 + 매도 leg 가 섞인 combo (iron condor) 는 싼 쪽 수수료가 0 — 아직 모형에 넣지 않음 (보수적).
- 0DTE OTM option 은 가격이 싸서 **12.5% 상한이 걸린다**. 1달러 프리미엄당 수수료 0.047 (SOL) ~ 0.083 (BTC) · stress 0.47.
- `src/optiq_rwa/backtest/metrics.py`: SR (0 대비 Sharpe), IR (RWA 4.5% 대비), MDD, CVaR, skew · kurtosis, **DSR** (Bailey & López de Prado 2014 deflated Sharpe; RWA 초과수익 기준, N = 같은 아이디어의 파라미터 설정 수). 하이라이트 규칙: SR > 0 · IR > 0.5 · MDD ≥ −15% · DSR ≥ 0.95 · 60밤 이상.
- 합성 sweep (TC 3종): 하이라이트 통과 8 / 588, 전부 events_underpriced 의 Idea 2. rich_iv 매도는 IR 1.4 이지만 skew −5 · kurtosis 40 때문에 DSR ≈ 0. 실데이터 BTC 는 통과 0. `results/SUMMARY.md`, `docs/REPORT_v0.3_risk_tc.md`.
- paper 엔진: 체결 시 `fee_usd` · `slippage_usd` (depth 5 호가를 걸어 VWAP 체결) · `levels_used` 기록, NAV 에서 수수료 차감. `preview` 로 지금 주문 시 수수료를 미리 본다.
- QUBO: SA 가 greedy 보다 못하던 원인은 soft 예산 벌점 (P2 = 2×scale) 이 첫 flip 을 전부 막은 것. P2 = 0.1×scale, 500 sweeps × 4 restarts + repair + polish 로 MILP 와 같은 해 (gap 0.00%). `solver="milp"` 추가. 벤치: `results/qubo_bench.md`.

### 국면 라벨 검증 (2026-11-20, `scripts/run_regime_validation.py`)

- BTC 202밤: rich_iv 밤의 strangle 매도 P&L (+0.0001/$ notional) 이 다른 라벨 밤 (+0.0004) 보다 **높지 않다**. −1% 최악 밤도 rich_iv 안에 있었다. regime_follow IR −0.05 < always_short IR 1.63. **라벨은 아직 신호가 아니다.**
- m=1 콜 매수는 모든 라벨에서 손실 (1달러당 −0.3 ~ −1.0).
- 어느 경로도 하이라이트 규칙을 통과하지 못했다 (DSR 최대 0.24 BTC always_short · 0.51 SOL).
- 결과: `results/regime_validation.md`, 대시보드 "라벨 검증" 패널.

### 저장 정책 · paper 첫 결과 (2026-11-23)

- **저장 정책 (사용자 선택 2026-11-23)**: SQLite `data/optiq.db` 는 로컬에만 둔다 (gitignore). GitHub 에는 Parquet (zstd) 일별 파일 + results + docs 만 매일 commit (`scripts/publish_data.sh`). `book_summary` 는 만기 8일 이내 종목만 저장한다 (거래량 필터는 전 종목으로 계산한 뒤 집계만 보관). snapshot 1개 ≈ 0.65 MB (전: 1.4 MB). 과거 commit 에 남은 DB blob (12.5 · 59 MB) 은 history 에 그대로 있다.
- **DB 잠금 버그 (2026-11-21 · 22 paper 주문 실패)**: 04:20 KST 작업이 snapshot 을 한 번 더 돌리는 동안 15분 snapshot 과 write lock 이 겹쳐 `database is locked`. 수정: snapshot 은 단계마다 commit, busy_timeout 60 s, daily 작업은 15분 snapshot 의 최신 호가만 쓴다.
- **게이트 역산 (`paper/gate_view.py`, 2026-11-23)**: 지금 보정 (BTC m=1 콜 payback 0.82, se 0.16 → 하한 0.56) 으로는 매수 게이트가 열리려면 ask 가 약 60% 내려야 하고, 매도 (m=1.5) 는 bid 가 56~94% 올라야 한다. 모든 leg 가 막혀 있고, z=1.0 완화 쌍둥이 (`*_gated_z1`) 와 점추정으로도 열리지 않는다. 즉 지금 묶는 것은 z·se 가 아니라 **spread** (매수 ask 가 mid 보다 약 20% 높음) + 12.5% 수수료다. 매수 게이트가 열리려면 payback 하한이 (ask + fee)/mid ≈ 1.4 를 넘어야 한다. 대시보드 "실행 게이트가 열리려면" 표.
- **라이브 spread 분포 (2026-11-20 ~ 23, snapshot 778개, 대시보드 "m≈1 콜 spread · 시간대별")**: 가장 가까운 만기 m≈1 콜의 (ask − bid)/mid 중앙값 BTC 21% (p10 14% · p90 40%), ETH 21%, BTC_USDC 25%, SOL_USDC 48%. 매수자는 mid 보다 BTC 10.5% · SOL 24% 비싸게 산다. 수수료 상한 12.5% 까지 더하면 BTC 매수 손익분기 payback ≈ 1.24. 가장 좁은 시간대 BTC 10:00 UTC · ETH 17:00 UTC (표본 3일, 참고만).
- **paper 첫 결과 (2026-11-20 밤, 11-21 08:00 UTC 결제)**: yield_calls 콜 3건 매수 74.0 USD → 결제 후 −81.4 USD (수수료 7.4 포함, 전부 OTM). short_condor · regime_switch 는 ETH condor 4 leg (프리미엄 수취 180, 지불 105) → +43.3 USD (수수료 31.7 포함). NAV: yield_calls 1,000,412 · condor 1,000,537 (RWA 이자 493 포함). 11-21 · 22 밤은 잠금 버그로 주문 없음.

### 실행

```bash
cp .env.example .env                      # Deribit key 는 선택 (paper 는 public API 만 사용)
PYTHONPATH=src python -m optiq_rwa.data.live snapshot      # 1회 수집 (~90초)
PYTHONPATH=src python -m optiq_rwa.data.live status
PYTHONPATH=src python -m optiq_rwa.paper.engine trade      # dry-run 주문 (만기 6~26시간 남은 chain)
PYTHONPATH=src python -m optiq_rwa.paper.engine settle && PYTHONPATH=src python -m optiq_rwa.paper.engine nav
PYTHONPATH=src python scripts/run_real_backtest.py                # TC 3종 · SR/IR/MDD/DSR · 기간별 수익
PYTHONPATH=src python scripts/run_regime.py && PYTHONPATH=src python scripts/run_regime_validation.py
PYTHONPATH=src python scripts/run_qubo_bench.py
PYTHONPATH=src uvicorn optiq_rwa.dashboard.app:app --port 8793   # http://127.0.0.1:8793
PYTHONPATH=src python scripts/export_dashboard.py                 # docs/index.html
./scripts/install_launchd.sh                                      # 자동 수집 · paper 일과 등록
pytest -q                                                         # 17 tests
```

### 한계 (v0.2)

- Deribit 은 과거 호가창을 제공하지 않는다. 실제 bid/ask 이력은 라이브 snapshot 으로 지금부터 쌓인다.
- SOL 과거 chain 은 strike 당 2~61 밤으로 매우 얇다.
- paper NAV 는 열린 포지션을 0 으로 평가한다 (매수 보수적 · 매도 과대).
- 이벤트 캘린더가 없어 event-only 모드는 실데이터에서 돌리지 않았다.
- API key 는 trade 권한이 있다. 코드는 private endpoint 를 호출하지 않지만 read-only key 로 바꾸는 것이 안전하다.

---

## 출발점: 참고 사례

Deribit SOL 데일리 콜 사례 분석([Pawel Lachowicz, LinkedIn](https://lnkd.in/p/gN5Us43k)) 요약:

- **σ√T가 전부:** 남은 시간 12.7시간, IV 58.9%이면 σ√T ≈ 2.2%. 데일리 옵션 하나는 "아침까지 약 2% 움직이는가"에 거는 베팅입니다.
- **손실 상한:** 같은 판단을 100배 무기한선물로 하면 작은 하락에도 청산되지만, 데일리 콜은 프리미엄만 잃습니다.
- **가격 안에 확률이 들어 있음:** 손익분기점(약 1σ 거리)을 넘은 비율이 모델 예측 약 16%보다 낮은 약 10%였고, 지불 1달러당 회수액은 중간가 기준 0.84, 매도호가 기준 0.65였습니다.
- **호가 차이가 큼:** 프리미엄 0.23짜리 옵션의 호가가 0.20/0.30으로, 차이가 프리미엄의 1/3이었습니다.

---

## 다섯 가지 아이디어 (모두 구현)

| # | 아이디어 | 구현 | 핵심 질문 |
|---|---|---|---|
| 1 | **수익으로 사는 옵션** | `strategies/core.py::yield_funded_calls` | RWA 이자만 써서 원금을 지키며 상승 노출을 살 수 있나? 모드: 매일 / 이벤트 밤만 / 적립 후 이벤트에 집중 |
| 2 | **이벤트 밤 선택 (QUBO)** | `optimize/qubo.py`, `core.py::qubo_event_selector` | 주 단위로 (날짜 × 코인 × 행사가) 후보 중 예산 안에서 최적 조합을 고를 수 있나? SA와 그리디 비교 |
| 3 | **RWA 담보 프리미엄 매도** | `core.py::short_premium` | 매수자가 평균적으로 손해라면 매도로 이득을 볼 수 있나? 스트랭글 / 보호 윙을 사는 아이언콘도르 |
| 4 | **확률 보정 리스크 모델** | `risk/calibration.py` | 모델 확률과 실제 확률의 차이, 1달러당 회수액(중간가·매도호가), 축소추정한 기대이익 |
| 5 | **무기한선물 vs 데일리 콜** | `core.py::perp_vs_option` | 같은 판단을 10~100배 무기한선물(경로상 청산)과 데일리 콜로 실행하면 결과가 어떻게 다른가 |

---

## 빠른 시작

```bash
pip install -e .            # 또는: pip install numpy pandas scipy tabulate pytest
PYTHONPATH=src python scripts/run_sweep.py          # 전체 스윕 (~2분)
PYTHONPATH=src python scripts/run_sweep.py --quick  # 1 seed
PYTHONPATH=src pytest -q tests

# 실데이터 (로컬에서 실행, Deribit 공개 API)
PYTHONPATH=src python -m optiq_rwa.data.deribit --coin SOL --start 2026-02-01 --end 2026-11-01
```

결과는 `results/`에 저장됩니다: `SUMMARY.md`, `sweep_summary.csv`, `sweep_results.csv`, `calibration.csv`, `perp_vs_option.csv`.

---

## 전략 스윕 설계

**합성 시장** (`data/synthetic.py`): BTC·ETH·SOL, 19:20 UTC 진입 → 08:00 UTC 만기(12.7시간), 1시간 단위 가격 경로.
- 공통 변동성 국면, 코인 간 상관 0.7, 두꺼운 꼬리(t 분포, 자유도 4), 밤사이 급변(3%)
- 이벤트 밤(12%, 미리 알려짐)에는 실현 변동성 ×1.6
- 행사가별 스큐, 호가 차이는 중간가의 10% + 2bp

**시장 시나리오** (같은 전략을 시장 가정만 바꿔 평가):

| 시나리오 | IV 프리미엄(VRP) | 이벤트 밤 IV 가산 | 의미 |
|---|---|---|---|
| `rich_iv` | +20% | ×1.8 | 옵션이 비싼 시장 |
| `base` | +5% | ×1.4 | 참고 사례와 비슷한 수준 (비이벤트 m=1 콜 회수액: 중간가 ≈0.89, 매도호가 ≈0.74) |
| `events_underpriced` | +10% | ×1.1 | 이벤트 위험이 IV에 덜 반영된 시장 |
| `fair_iv` | 0% | ×1.6 | 공정가 |

**전략 파라미터:** 아이디어 1은 m ∈ {0, 0.5, 1, 1.5} × 모드 3개 × 예산배수 {1, 3}, 아이디어 2는 {greedy λ=0, greedy λ=0.5, SA λ=0.5}, 아이디어 3은 m ∈ {1, 1.5, 2} × 매도 비중 {0.5, 1} × 이벤트 회피 여부 × 윙 {없음, m=2}. 시드 3개.

**워크포워드:** 900일 중 처음 200일은 학습만 하고, 모든 전략을 나머지 700일 표본 외 구간에서 같은 조건으로 평가합니다. QUBO 기대이익 모델은 28일마다 과거 전체 데이터로 다시 학습합니다. m은 행사가 거리를 σ√T 단위로 나타낸 값입니다(m=1이면 약 1σ OTM).

---

## 스윕 결과 (합성 데이터, 시드 평균, 표본 외)

벤치마크(RWA만 보유): 연 4.6%. 각 칸은 시나리오별 Sharpe(초과수익 기준) 1위 설정입니다.

| 시나리오 | ① 수익으로 사는 콜 | ② QUBO 이벤트 선택 | ③ 프리미엄 매도 |
|---|---|---|---|
| `rich_iv` | 8.5%, 단 MDD −8.6%, 최악 시드 −3.5% ❌ | 4.2% ❌ (안 사는 게 정답) | **53.4%**, MDD −13.9% ✅ |
| `base` | **5.7%**, MDD −0.1% ✅ (m=1, 이벤트 밤만, 예산 ×3) | 4.7% ≈ 벤치마크 | −1.8% ❌ |
| `events_underpriced` | 5.1%, Sharpe 1.7 ✅ | **6.9%**, Sharpe 1.4 ✅ | 5.6%, MDD −6.8% |
| `fair_iv` | 5.0% (이벤트 밤, m=1.5) | 4.3% ❌ | −9.0% ❌ |

**아이디어 4 (base, 콜):** 비이벤트 밤에는 OTM 콜의 실제 ITM 비율이 모델보다 낮았습니다(m=1에서 모델 16.8%, 실제 13.6%). 매도호가 기준 회수액은 0.73~0.84입니다. 이벤트 밤은 반대로 회수액이 1.2~2.8로 1을 넘었습니다. 이벤트 위험이 가격에 덜 반영되면 그만큼이 기대이익이 됩니다.

**아이디어 5 (base, 매 거래 $1 위험 노출, 매일 밤):** 100배 무기한선물은 **65.9%가 경로상 청산**, 25배는 9.9%가 청산됐습니다. 데일리 콜(m=1)은 85.5%의 밤에 프리미엄을 전부 잃지만, 중간 청산이 없고 최대 손실이 처음부터 확정돼 있습니다.

### 결론
1. **알파는 상품 구조가 아니라 가격에서 나옵니다.** 같은 구조라도 시장 가정에 따라 1위와 꼴찌가 바뀝니다. IV가 비싸면 매도, 이벤트가 과소평가되면 매수가 유리합니다. 따라서 **실데이터로 어느 시나리오에 해당하는지 판별하는 것(아이디어 4)이 첫 번째 과제**입니다.
2. **"매일 사기"는 모든 시나리오에서 열위입니다.** 언제 살지 고르는 것(이벤트 밤, QUBO)이 핵심입니다.
3. **매도는 보호 윙 비용까지 반영해야 합니다.** 처음 버전에서는 손실 상한을 비용 없이 적용해 성과가 부풀려졌고, 윙을 매도호가로 사도록 고친 뒤에는 `rich_iv` 외 시나리오에서 우위가 사라졌습니다.
4. **현재 SA가 그리디보다 못합니다**(base 기준 회수액 0.95 vs 1.42). 패널티 계수와 SA 반복 횟수 튜닝이 필요합니다. 아래 로드맵에 넣었습니다.

> ⚠️ 모든 수치는 **가정에 기반한 합성 데이터**입니다. 실제 수익을 보장하지 않으며, 투자 조언이 아닙니다.

---

## 로드맵

### ✅ Phase 0~4 (v0.1, 합성 데이터)
- [x] 저장소 구조, 가격 계산 유틸, 테스트
- [x] 시나리오별 합성 시장 생성기와 Deribit 데이터 수집기(공개 API, 로컬 실행용)
- [x] 아이디어 4: 확률 보정, 회수액, 축소추정 기대이익 모델
- [x] 아이디어 1·2·3·5 전략과 QUBO(SA·그리디)
- [x] 워크포워드 스윕 (시나리오 4 × 전략 약 50개 × 시드 3)

### 🔜 Phase 5 — 실데이터 검증 (다음 단계)
- [ ] `data/deribit.py`로 SOL·BTC·ETH 데일리 옵션 2026년 2월~11월 데이터 수집
- [ ] 실데이터로 아이디어 4 실행 → 실제 시장이 어느 시나리오에 가까운지 판별
- [ ] 이벤트 캘린더(FOMC, CPI, 토큰 언락) 정리
- [ ] 진짜 매수·매도 호가 확보: 매일 `get_order_book` 스냅샷 저장(체결 VWAP 대체)

### Phase 6 — 최적화 고도화
- [ ] SA 튜닝(패널티 계수, 반복 횟수, 재시작), 정확해(MILP)와 비교
- [ ] 기대이익 모델에 IV/RV 비율, 기간구조, 펀딩비 피처 추가
- [ ] 켈리 방식으로 투입 규모 결정, 매수·매도 동적 전환(국면 판별)

### Phase 7 — 확장
- [ ] 실제 RWA 수익률 시계열 연결(토큰화 국채)
- [ ] 스마트컨트랙트 볼트 프로토타입·프론트엔드 연동

---

## 디렉터리 구조

```
optiq-rwa/
├── src/optiq_rwa/
│   ├── pricing.py            # σ√T, Black-Scholes(현물=1 기준), ITM 확률
│   ├── data/synthetic.py     # 시나리오별 합성 시장
│   ├── data/deribit.py       # Deribit 공개 히스토리 → 같은 스키마
│   ├── risk/calibration.py   # 아이디어 4
│   ├── optimize/qubo.py      # 아이디어 2: QUBO 구성, SA, 그리디
│   ├── strategies/core.py    # 아이디어 1·2·3·5
│   └── backtest/             # 스윕, 성과 지표
├── scripts/run_sweep.py
├── results/                  # 스윕 결과 (SUMMARY.md, CSV)
└── tests/
```

## 역할

| 영역 | 담당 |
|---|---|
| 프로젝트 리드, 최적화(QUBO) | @limpst |
| 데이터 분석, 리스크 모델링·시뮬레이션 (Phase 5 우선) | 협업자 |
| 스마트컨트랙트, 프론트엔드 | Phase 7에서 재논의 |

## 참고자료
- Deribit API: https://docs.deribit.com
- 크립토 데일리 옵션 사례 분석 (Pawel Lachowicz, LinkedIn): https://lnkd.in/p/gN5Us43k

## Contact
- LinkedIn: [linkedin.com/in/hylee80](https://linkedin.com/in/hylee80)

---

## 아이디어 확장 (6~10): 실물 RWA 수익 × 데일리 옵션 오버레이 상호작용

아이디어 1~5 는 옵션 쪽 성과를 하나씩 봅니다. 확장 아이디어 6~10 은 **두 슬리브가 서로 어떻게 맞물리는지**를 봅니다: 실물 RWA 수익 슬리브(토큰화 국채)가 옵션 슬리브에 예산과 담보를 공급하고, 옵션 손익이 다시 RWA 원금·예산으로 돌아가는 고리입니다.

```
 실물 RWA 슬리브 (토큰화 국채, 원금 보존)
   │  ① 이자 = 옵션 예산          ② 토큰 = 매도 증거금 (haircut 적용)
   ▼                              ▼
 데일리(0DTE) 옵션 오버레이 ── 매수(아이디어 1·2) / 매도(아이디어 3)
   │  ③ 실행 게이트: 기대이익 − TC > 0 인 밤에만 진입
   ▼
 일일 손익 ── ④ 이익: 예산 적립 or 원금 재투자 / 손실: 예산 한도 내 흡수
```

> 표기: 이 섹션에서 위험가중 노출은 **RW 노출**로 씁니다 (RWA = 실물자산과 혼동 방지).

| # | 아이디어 | 적용 위치 | 상호작용 질문 |
|---|---|---|---|
| 6 | **수익원 · 거래소 공통 인터페이스** | `data/` 아래 `Venue` 추상 클래스 + factory. `deribit.py` 를 첫 구현체로, 실물 RWA 수익원도 같은 스키마(노출, 수익률, 비용)로 정규화 | RWA 수익원 · 옵션 거래소를 바꿔 끼워도 전략 · 백테스트 코드가 그대로인가? |
| 7 | **자본조정 수익 (슬리브별 RW 노출)** | `backtest/metrics.py`. 자본조정 수익 = 초과수익 ÷ Σ(노출 × 위험가중치). RWA 슬리브는 낮은 가중치, 옵션 매수는 프리미엄 100%, 매도는 최대손실 기준 | RWA 이자 1단위로 산 옵션(1)과 RWA 담보로 판 옵션(3) 중 자본 효율이 높은 쪽은? |
| 8 | **실행 경제성 게이트** ✅ paper 적용 | `backtest/costs.py` · `paper/engine.py`. 아이디어 4 의 축소추정 기대이익 − TC(수수료 · spread · slippage) ≤ 0 이면 주문 보류, 예산은 다음 밤으로 이월 | 비용을 넘는 밤에만 쓰고 나머지 이자를 적립하면 SR · MDD 가 어떻게 바뀌나? |
| 9 | **예산 · 담보 상호작용 패널** | `dashboard/`. 누적 이자 예산, 사용 · 이월 예산, 담보 haircut 후 매도 한도, 게이트 보류 건수 | RWA 금리 · haircut 이 바뀌면 옵션 운용 한도가 얼마나 움직이나? |
| 10 | **국면 스트레스: 예산 소진 일수** | `risk/regime.py` 국면을 시나리오로 하룻밤 꼬리손실 Monte Carlo | 최악 국면에서 RWA 이자 예산이 옵션 손실을 몇 밤 버티고, 언제 원금을 건드리나? |

### 다음 단계 (로드맵 반영 제안)
- [x] Phase 6: 아이디어 8 게이트를 paper 엔진에 연결 (`paper/gate.py`, `*_gated` 쌍둥이 전략) — 전/후 비교는 실시간 현황 페이지
- [ ] Phase 6: 아이디어 7 자본조정 수익을 `results/sweep_summary.csv` 열로 추가
- [ ] Phase 7: 아이디어 6 인터페이스로 실물 RWA 수익률 시계열 연결 (기존 Phase 7 항목과 통합)
- [ ] Phase 7: 아이디어 9 패널 · 아이디어 10 스트레스 테스트

### 개선 제안
1. **위험가중치 근거 표** — 슬리브별 가중치를 BCBS 암호자산 기준(SCO60)의 그룹 분류(1a/1b/2a/2b)와 토큰화 국채의 기초자산 기준으로 정하고 출처를 남길 것.
2. **담보 haircut 실측** — RWA 토큰을 증거금으로 받는 거래소 · 프로토콜의 실제 haircut 과 금리 변화를 시계열로 붙여 아이디어 3 매도 한도를 동적으로 계산.
3. **`Venue` 출력 스키마를 먼저 고정** — dataclass(venue_id, exposure, weight, yield_or_edge, tc, gate_pass)와 테스트(`tests/`)를 먼저 작성.
4. **이익 처리 규칙 비교** — 옵션 이익을 (a) 예산 적립 (b) RWA 원금 재투자 (c) 절반씩 으로 나눠 sweep 해서 장기 NAV 비교.

**더 깊이 들어갈 수 있는 지점:** 아이디어 7 의 RW 노출을 QUBO(아이디어 2) 제약으로 넣으면 "이자 예산 제약" 대신 "자본 소모 제약" 하의 이벤트 밤 선택 문제로 확장되고, 아이디어 9 의 담보 한도를 두 번째 제약으로 더해 매수 · 매도 혼합 선택까지 한 번에 풀 수 있습니다.
