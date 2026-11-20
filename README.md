# OptiQ-RWA

**RWA 기반 수익 + 크립토 데일리(0DTE) 옵션 오버레이 최적화**

토큰화 실물자산(RWA, 예: 토큰화 국채)으로 안정적인 기초 수익을 확보하고, 그 수익을 예산으로 삼아 크립토 데일리 옵션 포지션을 운용·최적화하는 사이드 프로젝트입니다. 데일리 옵션은 손실이 프리미엄으로 제한되고 하룻밤 사이에 수익이 크게 날 수 있는 구조지만, 평균적으로 싸지는 않습니다. 이 프로젝트는 **어떤 시장 조건에서, 어떤 구조가, 언제 의미가 있는지**를 데이터로 판별하는 것이 목표입니다.

> 상태: 🧪 v0.2 — 라이브 Deribit 수집 (SQLite · 15분 launchd) · dry-run paper 엔진 · 실데이터 backtest · 대시보드. 실주문 없음.

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
| `scripts/launchd/` | `com.optiq.snapshot` (900초) · `com.optiq.trade` (04:20 KST) · `com.optiq.settle` (17:30 KST, 결제 · NAV · export · DB commit) |

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

### 실행

```bash
cp .env.example .env                      # Deribit key 는 선택 (paper 는 public API 만 사용)
PYTHONPATH=src python -m optiq_rwa.data.live snapshot      # 1회 수집 (~90초)
PYTHONPATH=src python -m optiq_rwa.data.live status
PYTHONPATH=src python -m optiq_rwa.paper.engine trade      # dry-run 주문 (만기 6~26시간 남은 chain)
PYTHONPATH=src python -m optiq_rwa.paper.engine settle && PYTHONPATH=src python -m optiq_rwa.paper.engine nav
PYTHONPATH=src python scripts/run_real_backtest.py
PYTHONPATH=src uvicorn optiq_rwa.dashboard.app:app --port 8793   # http://127.0.0.1:8793
PYTHONPATH=src python scripts/export_dashboard.py                 # docs/index.html
./scripts/install_launchd.sh                                      # 자동 수집 · paper 일과 등록
pytest -q                                                         # 7 tests
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
