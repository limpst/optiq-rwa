"""Rewrite the auto-generated status block in README.md (between AUTO:STATUS markers).

Sources (all local, no network):
  data/optiq.db                       live snapshot counts, latest index prices, universe filter, paper NAV
  results/regime_history.csv          latest walk-forward regime label per coin
  results/regime_validation_nav_*.csv OOS walk-forward NAV metrics (full period)
  results/regime_validation_curves.csv OOS walk-forward NAV curves (recent 30-night window)

Run: PYTHONPATH=src python scripts/update_readme.py        (launchd: daily.sh readme / settle)
"""
from __future__ import annotations

import datetime as dt
import pathlib
import sqlite3
import sys

import pandas as pd

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from optiq_rwa.backtest.metrics import nav_metrics  # noqa: E402
from optiq_rwa.config import SETTINGS               # noqa: E402

README, RES = ROOT / "README.md", ROOT / "results"
START, END = "<!-- AUTO:STATUS:START -->", "<!-- AUTO:STATUS:END -->"
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


def live_section(con) -> list[str]:
    out = ["### 라이브 수집 (Deribit 공개 API, 15분 주기)"]
    n, first, last = con.execute("select count(*), min(ts_ms), max(ts_ms) from snapshots").fetchone()
    if not n:
        return out + ["", "아직 snapshot 없음."]
    cut = last - 24 * 3600 * 1000
    n24 = con.execute("select count(*) from snapshots where ts_ms > ?", (cut,)).fetchone()[0]
    sid = con.execute("select max(snap_id) from snapshots").fetchone()[0]
    px = dict(con.execute("select index_name, price from index_price where snap_id = ?", (sid,)).fetchall())
    rows = [["snapshot 수 (전체 / 최근 24h)", f"{n:,} / {n24}"],
            ["기간 (KST)", f"{kst(first)} → {kst(last)}"]]
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
    rows = []
    for s, g in nav.groupby("strategy"):
        g = g.sort_values("date")
        m = nav_metrics(g.nav / g.nav.iloc[0], SETTINGS.rwa_rate) if len(g) > 1 else {}
        rows.append([s, len(g), g.date.iloc[-1], f"{g.nav.iloc[-1]:,.0f}", pct(g.nav.iloc[-1] / g.nav.iloc[0] - 1, 2),
                     pct(m.get("max_drawdown"), 2), int(g.n_open.iloc[-1])])
    return out + ["", md_table(rows, ["전략", "일수", "최근", "NAV", "누적", "MDD", "미결제"])]


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
                recent[col] = nav_metrics(s / s.iloc[0], SETTINGS.rwa_rate)
    rows = []
    for r in full.itertuples():
        rm = recent.get(f"{r.coin}|{r.strategy}", {})
        name = f"**{r.strategy}**" if str(r.highlight) == "True" else r.strategy
        rows.append([r.coin, name, int(r.n_nights), pct(r.ann_return), pct(r.excess_vs_rwa), num(r.sharpe), num(r.ir_vs_rwa),
                     pct(r.max_drawdown, 2), num(r.dsr), pct(rm.get("ann_return")), pct(rm.get("max_drawdown"), 2)])
    head = ["코인", "전략", "밤", "연수익", "RWA 대비", "SR", "IR", "MDD", "DSR", f"최근 {RECENT}밤 연수익", f"최근 {RECENT}밤 MDD"]
    return ["### OOS walk-forward (실데이터 체인, base TC)", "",
            "국면 라벨은 그날 이전 밤의 특징만으로 정하고(look-ahead 없음), 모든 전략을 같은 표본 외 구간에서 평가합니다. "
            "굵게 = highlight 규칙 통과. 상세: `results/regime_validation.md`.", "",
            md_table(rows, head)]


def build() -> str:
    now = dt.datetime.now(KST).strftime("%Y-%m-%d %H:%M KST")
    parts = [START, f"## 실시간 현황 (자동 갱신: {now})", "",
             "> 이 섹션은 `scripts/update_readme.py` 가 매시간(launchd `com.optiq.readme`)과 매일 settle(17:30 KST) 때 다시 씁니다. 손으로 고치지 마세요.", ""]
    con = sqlite3.connect(SETTINGS.db_path)
    try:
        for sec in (live_section(con), paper_section(con)):
            parts += sec + [""]
    finally:
        con.close()
    for sec in (regime_section(), oos_section()):
        if sec:
            parts += sec + [""]
    parts.append(END)
    return "\n".join(parts)


def main() -> int:
    text = README.read_text()
    block = build()
    if START in text and END in text:
        a, rest = text.split(START, 1); _, b = rest.split(END, 1)
        new = a + block + b
    else:  # first run: insert right before the first section after the link table
        key = "\n---\n"
        i = text.find(key, text.find("## 링크"))
        new = text[:i] + "\n\n" + block + "\n" + text[i:] if i > 0 else text.rstrip() + "\n\n" + block + "\n"
    if new != text:
        README.write_text(new)
        print("README status block updated")
    else:
        print("README unchanged")
    return 0


if __name__ == "__main__":
    sys.exit(main())
