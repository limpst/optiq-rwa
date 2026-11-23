"""Write the live status page docs/status.md (README stays static and links to it).

Schedule (launchd, see scripts/daily.sh):
  hourly  `daily.sh status`  -> docs/status.md, force-pushed as the single commit of branch `status` (main history untouched)
  daily   `daily.sh settle`  -> docs/status.md committed to main together with the DB snapshot

Sources (all local, no network):
  data/optiq.db                       live snapshot counts, latest index prices, universe filter, paper NAV
  results/regime_history.csv          latest walk-forward regime label per coin
  results/regime_validation_nav_*.csv OOS walk-forward NAV metrics (full period)
  results/regime_validation_curves.csv OOS walk-forward NAV curves (recent 30-night window, with its own DSR)

Run: PYTHONPATH=src python scripts/update_status.py [--max-age-min 45]
Exit code 3 when the newest snapshot is older than --max-age-min (collector stalled: Mac asleep, launchd not loaded,
network down). The page is still written; daily.sh turns code 3 into one alert per stall episode.
"""
from __future__ import annotations

import argparse
import datetime as dt
import pathlib
import sqlite3
import sys

import pandas as pd

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from optiq_rwa.backtest.metrics import add_dsr, nav_metrics  # noqa: E402
from optiq_rwa.config import SETTINGS               # noqa: E402

OUT, RES = ROOT / "docs" / "status.md", ROOT / "results"
KST = dt.timezone(dt.timedelta(hours=9))
RECENT = 30


def kst(ms) -> str:
    return dt.datetime.fromtimestamp(ms / 1000, KST).strftime("%Y-%m-%d %H:%M")


def pct(x, d=1) -> str:
    if x is None or pd.isna(x):
        return "–"
    return f"{0:.{d}f}%" if abs(x) < 0.5 * 10 ** -(d + 2) else f"{x * 100:+.{d}f}%"


def num(x, d=2) -> str:
    return "–" if x is None or pd.isna(x) else f"{x:.{d}f}"


def md_table(rows: list[list], head: list[str], align: str | None = None) -> str:
    a = align or "|".join("---" for _ in head)
    return "\n".join(["| " + " | ".join(head) + " |", "|" + a + "|"] + ["| " + " | ".join(map(str, r)) + " |" for r in rows])


def snapshot_age_min(con) -> float:
    last = con.execute("select max(ts_ms) from snapshots").fetchone()[0]
    return float("inf") if last is None else (dt.datetime.now(dt.timezone.utc).timestamp() * 1000 - last) / 60_000


def live_section(con) -> list[str]:
    out = ["### 라이브 수집 (Deribit 공개 API, 15분 주기)"]
    n, first, last = con.execute("select count(*), min(ts_ms), max(ts_ms) from snapshots").fetchone()
    if not n:
        return out + ["", "아직 snapshot 없음."]
    cut = last - 24 * 3600 * 1000
    n24 = con.execute("select count(*) from snapshots where ts_ms > ?", (cut,)).fetchone()[0]
    sid = con.execute("select max(snap_id) from snapshots").fetchone()[0]
    px = dict(con.execute("select index_name, price from index_price where snap_id = ?", (sid,)).fetchall())
    age = snapshot_age_min(con)
    rows = [["snapshot 수 (전체 / 최근 24h)", f"{n:,} / {n24}"],
            ["기간 (KST)", f"{kst(first)} → {kst(last)}"],
            ["마지막 snapshot 경과", f"{age:,.0f}분" + (" ⚠️ 수집 정지 의심" if age > 45 else "")]]
    for k in ("btc_usd", "eth_usd", "sol_usd"):
        if k in px:
            rows.append([f"index {k.split('_')[0].upper()}", f"{px[k]:,.2f} USD"])
    vd = pd.read_sql("select * from volume_daily where date = (select max(date) from volume_daily)", con)
    if not vd.empty:
        ok = vd[vd.universe_pass == 1].sort_values("volume_usd", ascending=False).base.tolist()
        rows.append([f"universe 통과 ({vd.date.iloc[0]})", ", ".join(ok) or "없음"])
    return out + ["", md_table(rows, ["항목", "값"])]


def paper_section(con) -> list[str]:
    out = ["### Paper trading (실시간 표본 외, dry-run)"]
    nav = pd.read_sql("select * from paper_nav order by date", con)
    if nav.empty:
        n_ord = con.execute("select count(*) from paper_orders").fetchone()[0]
        return out + ["", f"결제된 NAV 기록 없음 (주문 {n_ord}건). 첫 settle(17:30 KST) 이후 채워집니다."]
    stats = {}
    for s, g in nav.groupby("strategy"):
        g = g.sort_values("date")
        m = nav_metrics(g.nav.iloc[1:] / g.nav.iloc[0], SETTINGS.rwa_rate) if len(g) > 1 else {}
        stats[s] = dict(days=len(g), last=g.date.iloc[-1], nav=g.nav.iloc[-1], ret=g.nav.iloc[-1] / g.nav.iloc[0] - 1,
                        mdd=m.get("max_drawdown"), fees=g.fees_usd.iloc[-1], n_open=int(g.n_open.iloc[-1]))
    rows = [[s, v["days"], v["last"], f"{v['nav']:,.0f}", pct(v["ret"], 2), pct(v["mdd"], 2), int(v["n_open"])]
            for s, v in stats.items() if not s.endswith("_gated")]
    out += ["", md_table(rows, ["전략", "일수", "최근", "NAV", "누적", "MDD", "미결제"])]
    gated = pd.read_sql("select strategy, count(distinct date) as nights, count(*) as legs from paper_orders "
                        "where status='gated' group by strategy", con).set_index("strategy")
    traded = pd.read_sql("select strategy, count(distinct date) as nights from paper_orders where status='filled' group by strategy",
                         con).set_index("strategy")
    rows = []
    for s, v in stats.items():
        if s.endswith("_gated") or f"{s}_gated" not in stats:
            continue
        w = stats[f"{s}_gated"]
        rows.append([s, pct(v["ret"], 2), pct(w["ret"], 2), pct(w["ret"] - v["ret"], 2), pct(v["mdd"], 2), pct(w["mdd"], 2),
                     f"{v['fees']:,.0f} → {w['fees']:,.0f}",
                     f"{int(traded.nights.get(f'{s}_gated', 0))} / {int(gated.nights.get(f'{s}_gated', 0))}"])
    if rows:
        out += ["", "#### 실행 게이트 적용 전 / 후 (아이디어 8: 기대이익 − 스프레드·수수료 > 0 인 패키지만 진입)", "",
                md_table(rows, ["전략", "누적 (전)", "누적 (후)", "차이", "MDD (전)", "MDD (후)", "수수료 USD 전 → 후", "진입 / 보류 밤 (후)"])]
    return out


def regime_section() -> list[str]:
    f = RES / "regime_history.csv"
    if not f.exists():
        return []
    h = pd.read_csv(f)
    last = h.sort_values("date").groupby("coin").tail(1)
    rows = [[r.coin, r.date, r.label, num(r.ivrv), r.action] for r in last.itertuples()]
    return ["### 현재 국면 (walk-forward 라벨, 과거 밤만 사용)", "",
            md_table(rows, ["코인", "기준일", "라벨", "IV/RV", "행동"])]


def oos_section() -> list[str]:
    files = sorted(RES.glob("regime_validation_nav_*.csv"))
    if not files:
        return []
    full = pd.concat(pd.read_csv(f) for f in files)
    cur = RES / "regime_validation_curves.csv"
    recent = {}
    if cur.exists():
        c = pd.read_csv(cur, index_col=0).sort_index()
        for col in c.columns:
            s = c[col].dropna().tail(RECENT + 1)
            if len(s) > 2:
                coin, strat = col.split("|", 1)
                recent[col] = dict(coin=coin, strategy=strat, **nav_metrics(s.iloc[1:] / s.iloc[0], SETTINGS.rwa_rate))
        if recent:   # DSR inside the recent window: N = strategies per coin, same window length
            rt = add_dsr(pd.DataFrame(recent.values()), group_cols=("coin",))
            rt.loc[rt.ann_vol.fillna(0) < 1e-8, "dsr"] = float("nan")          # rwa_only: no risk, DSR undefined
            recent = {f"{r.coin}|{r.strategy}": r._asdict() for r in rt.itertuples(index=False)}
    rows = []
    for r in full.itertuples():
        rm = recent.get(f"{r.coin}|{r.strategy}", {})
        name = f"**{r.strategy}**" if str(r.highlight) == "True" else r.strategy
        rows.append([r.coin, name, int(r.n_nights), pct(r.ann_return), pct(r.excess_vs_rwa), num(r.sharpe), num(r.ir_vs_rwa),
                     pct(r.max_drawdown, 2), num(r.dsr), pct(rm.get("ann_return")), pct(rm.get("max_drawdown"), 2), num(rm.get("dsr"))])
    head = ["코인", "전략", "밤", "연수익", "RWA 대비", "SR", "IR", "MDD", "DSR",
            f"최근 {RECENT}밤 연수익", f"최근 {RECENT}밤 MDD", f"최근 {RECENT}밤 DSR"]
    return ["### OOS walk-forward (실데이터 체인, base TC)", "",
            "국면 라벨은 그날 이전 밤의 특징만으로 정하고(look-ahead 없음), 모든 전략을 같은 표본 외 구간에서 평가합니다. "
            "굵게 = highlight 규칙 통과. 최근 30밤 DSR 은 그 구간 안에서 전략 수(N)로 다시 계산 — 전체 DSR 과 차이가 크면 국면 전환 직후 과적합 신호. "
            "체인 = 과거 체결 이력 + 매일 추가되는 라이브 호가 밤(`data/live/`). 상세: `results/regime_validation.md`.", "",
            md_table(rows, head)]


def build() -> str:
    now = dt.datetime.now(KST).strftime("%Y-%m-%d %H:%M KST")
    parts = ["# OptiQ-RWA 실시간 현황", "", f"자동 생성: {now} · `scripts/update_status.py` (매시간 `status` 브랜치, 매일 17:30 KST main). 손으로 고치지 마세요.", ""]
    con = sqlite3.connect(SETTINGS.db_path)
    try:
        for sec in (live_section(con), paper_section(con)):
            parts += sec + [""]
    finally:
        con.close()
    for sec in (regime_section(), oos_section()):
        if sec:
            parts += sec + [""]
    return "\n".join(parts)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--max-age-min", type=float, default=None, help="exit 3 if the newest snapshot is older than this")
    a = ap.parse_args()
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(build())
    print(f"wrote {OUT.relative_to(ROOT)}")
    if a.max_age_min is not None:
        con = sqlite3.connect(SETTINGS.db_path)
        try:
            age = snapshot_age_min(con)
        finally:
            con.close()
        if age > a.max_age_min:
            print(f"STALE: newest snapshot is {age:,.0f} min old (limit {a.max_age_min:.0f})")
            return 3
    return 0


if __name__ == "__main__":
    sys.exit(main())
