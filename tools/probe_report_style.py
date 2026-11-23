# -*- coding: utf-8 -*-
"""보고서 문체 검증 probe — 2026-09-14 검토 의견이 실제로 지켜졌는지 기계로 확인한다.

왜 필요한가
  요구사항 문서(REPORT_WRITING_REQUIREMENTS_2026-09-14.md)와 전역 규칙에 이미 적혀 있었는데도,
  같은 날 저녁에 쓴 문서가 다시 "읽는 법 ①②③ · benchmark = 옆집 · ~예요" 로 나갔다. 규칙이
  존재하는 것과 지켜지는 것은 다르다. 사람이 매번 읽어서 잡는 대신 이 probe 가 잡는다.

무엇을 보나 (위반 = 실패)
  M1 비유·지어낸 한글 용어  옆집 · 바구니 · 미끄럼틀 · 용돈 · 약을 쓴 셈 · 시간비 · 국소 하강 …
  M2 대화체 어미           ~예요 · ~에요 · ~해요 · ~죠 · ~네요 (결과·기술 보고서)
  M3 안내 절               "읽는 법" 절, "이 문서는 …입니다" 류 메타 문장, 번호 독서 안내
  M4 정의 없는 축약어      LW · NS · PIT · TE · IR · DSR · KRD · ECL · YTM · QUBO · SA · MDD
  M5 이모지 소제목         `## 🔬 …` (결과·기술 보고서)
  M6 기초 개념 설명        "채권 금리는 … 하나가 아니" 류의 기본 지식 설명
  M7 CONFIDENTIAL 꼬리말   "CONFIDENTIAL — Qunova internal / QOP 팀 내부용 … 투자 권유가 아닙니다" (2026-09-18 지시)
  M8 정의가 첫 언급보다 뒤  축약어를 먼저 쓰고 나중에 풀어 쓴 경우 (2026-10-24 지시, T2 사례)

  인용을 위해 금지어를 담아야 하는 문서(검토 기록·요구사항·근본원인)는 파일 첫 30줄에
  `<!-- style-probe: allow-quotes -->` 를 두면 M1~M6 전부를 건너뛴다.

쓰는 법
  python tools/probe_report_style.py                 # 기본 경로 전수 검사
  python tools/probe_report_style.py --paths a.md b.md
  python tools/probe_report_style.py --json out.json
종료 코드: 위반 0 이면 0, 있으면 1 (CI·발송 전 게이트로 쓸 수 있다).
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WORKSHOP = Path.home() / "thailand-qubo-workshop"

# 검사 대상 — 회사로 나가는 문서 전부
DEFAULT_GLOBS = [
    (ROOT / "docs" / "ref", "*.md"),
    (ROOT, "DAILY_REPORT_*.md"),
    (ROOT, "UPDATE_*.md"),
    (ROOT / "reports" / "daily", "*.md"),
    (WORKSHOP / "reports" / "experiments", "*.md"),
    (WORKSHOP / "reports" / "papers", "*.md"),
]

ALLOW_MARK = "style-probe: allow-quotes"

# M7 — 2026-09-18 지시: 이 꼬리말은 어떤 산출물에도 붙이지 않는다. 2026-09-17 에 실수로 들어간 뒤 메일·Teams 카드·
# 보고서·용어집으로 복제됐고, 생성기에서 뺀 뒤에도 새 문서에 다시 나타났다(2026-09-20 문서 4편).
CONFIDENTIAL_PAT = re.compile(r"CONFIDENTIAL\s*[—–-]\s*(Qunova internal|QOP\s*팀|이\s*리포트는)")

METAPHORS = {
    "옆집": "benchmark",
    "바구니": "portfolio",
    "미끄럼틀": "roll-down",
    "용돈": "excess return / economic value",
    "더 번 것": "excess return",
    "약을 쓴 셈": "(비유 — 삭제하고 원인을 쓴다)",
    "계절": "regime",
    "형·동생": "(비유 — 삭제)",
    # 2026-09-18 지시(용어 규칙 표): 영어 표현을 한글로 새로 지어내지 않는다 — 읽는 사람이 되묻는다
    "시간비": "TTS ratio (time-to-solution ratio)",
    "국소 하강": "local search (1-swap descent)",
}

# 대화체 어미 — 문장 끝에서만 (코드·인용 안은 이미 제거한 뒤 검사)
# 줄 끝뿐 아니라 문장 중간도 잡는다 — 2026-09-15 에 줄 끝만 보다가 11건을 놓쳤다.
# 앞 음절을 제한해 '필요·중요·수요' 같은 명사를 오탐하지 않는다 (같은 날 오탐 3건).
CHATTY = re.compile(r"(?:[어아에여예해봐와워줘까][요]|이에요|예요|거예요|더라고요|하죠|네요)(?=[.,)\]\s”\"—]|$)")

ABBR = {
    "LW": r"Ledoit[–\-]?\s?Wolf",
    "NS": r"Nelson[–\-]?\s?Siegel",
    "PIT": r"point[- ]in[- ]time",
    "TE": r"tracking error|추적오차",
    "IR": r"information ratio|정보비율",
    "DSR": r"deflated Sharpe",
    "KRD": r"key[- ]rate duration",
    "ECL": r"expected credit loss|기대손실",
    "YTM": r"yield[- ]to[- ]maturity|yield to maturity",
    "QUBO": r"quadratic unconstrained binary",
    "MDD": r"maximum drawdown|최대낙폭",
    "SA": r"simulated annealing",
    # 2026-10-24 — 덱 6번 "T2 ≤ 1" 이 정의 없이 먼저 나왔다
    "T2": r"Tier[ -]?2",
}

META = [
    re.compile(r"^\s*#+.*읽는 법"),
    re.compile(r"^\s*>?\s*(📖|📘)?\s*\*\*?읽는 법"),
    re.compile(r"이 문서(는|가)\s*(무엇|뭐|…)?[^\n]{0,40}(입니다|예요|이에요)"),
    re.compile(r"[①②③]\s*(이|이것|이 문서|순서|reader|reader 는)"),
]

BASICS = [
    re.compile(r"채권 금리는[^\n]{0,30}(만기|하나)"),
    re.compile(r"(초등학생|유치원)[^\n]{0,20}(기준|눈높이|reader)"),
]

CODE_BLOCK = re.compile(r"```.*?```", re.S)
INLINE_CODE = re.compile(r"`[^`\n]*`")
TABLE_QUOTE = re.compile(r"^\s*\|.*(금지|banned|예 \(|violat).*\|\s*$", re.I)


def strip_code(text: str) -> str:
    text = CODE_BLOCK.sub(lambda m: "\n" * m.group(0).count("\n"), text)
    return INLINE_CODE.sub("``", text)


def scan(path: Path) -> list[dict]:
    raw = path.read_text(encoding="utf-8", errors="replace")
    head = "\n".join(raw.splitlines()[:30])
    allow_quotes = ALLOW_MARK in head
    text = strip_code(raw)
    lines = text.splitlines()
    out: list[dict] = []

    def add(code, line_no, line, msg):
        out.append({"file": str(path), "line": line_no, "rule": code,
                    "text": line.strip()[:160], "message": msg})

    for i, line in enumerate(lines, start=1):
        if TABLE_QUOTE.match(line):
            continue
        if not allow_quotes:
            for word, better in METAPHORS.items():
                if word in line:
                    add("M1", i, line, f"비유 '{word}' → 표준 용어 '{better}' 로")
            for pat in BASICS:
                if pat.search(line):
                    add("M6", i, line, "독자가 아는 기초 개념 설명 — 삭제하거나 데이터 한 줄로 대체")
            for sent in re.split(r"(?<=[.!?])\s+|\n", line):
                s = sent.strip()
                if s and CHATTY.search(s):
                    add("M2", i, s, "대화체 어미 — 결과·기술 보고서는 실무 보고체")
                    break
        if not allow_quotes:
            for pat in META:
                if pat.search(line):
                    add("M3", i, line, "안내 절·메타 문장 — 요약 3줄로 대체")
                    break
            if re.match(r"^\s*#{1,6}\s+[^\w\s(]", line) and re.search(r"[\U0001F300-\U0001FAFF]", line):
                add("M5", i, line, "이모지 소제목 — 결과·기술 보고서에서는 쓰지 않는다")
            if CONFIDENTIAL_PAT.search(line):
                add("M7", i, line, "CONFIDENTIAL 꼬리말 — 2026-09-18 지시로 금지. 그 줄을 지운다")

    # M4 정의 없는 축약어 — 문서 전체에서 한 번이라도 풀어 썼는지
    # M8 은 규칙이 생긴 날(M8_CUTOFF) 이후 문서와 날짜 없는 현행 문서에만 건다 — 옛 문서는 보낸 기록이다
    d = _doc_date(path)
    m8_on = d is None or d >= M8_CUTOFF
    for abbr, expansion in ({} if allow_quotes else ABBR).items():
        hit = re.search(rf"(?<![A-Za-z]){abbr}(?![A-Za-z])", text)
        if hit and not re.search(expansion, text, re.I):
            line_no = text[:hit.start()].count("\n") + 1
            add("M4", line_no, lines[line_no - 1] if line_no <= len(lines) else abbr,
                f"축약어 {abbr} 가 정의 없이 쓰였다 — Notation 에 풀어 쓴다")
        elif hit and m8_on:
            # M8 정의가 첫 언급보다 뒤 — 같은 줄 또는 앞줄에 풀어 써야 한다.
            # 제목 줄(#)은 정의를 담을 수 없으니 건너뛰고 본문 첫 언급을 본다.
            body = [m for m in re.finditer(rf"(?<![A-Za-z]){abbr}(?![A-Za-z])", text)
                    if not lines[text[:m.start()].count("\n")].lstrip().startswith("#")]
            first_def = re.search(expansion, text, re.I)
            line_no = text[:body[0].start()].count("\n") + 1 if body else 0
            def_line = text[:first_def.start()].count("\n") + 1
            if body and def_line > line_no:
                add("M8", line_no, lines[line_no - 1] if line_no <= len(lines) else abbr,
                    f"축약어 {abbr} 정의가 첫 언급(L{line_no})보다 뒤(L{def_line})에 있다 — 첫 언급에서 풀어 쓴다")
    return out


CUTOFF = "2026-09-14"          # 요구사항이 확정된 날. 이후 문서에만 강제한다.
M8_CUTOFF = "2026-10-24"       # M8(정의가 첫 언급보다 뒤) 규칙이 생긴 날
DATE_IN_NAME = re.compile(r"(20\d{2})[-_]?(\d{2})[-_]?(\d{2})")


def _doc_date(p: Path) -> str | None:
    m = DATE_IN_NAME.search(p.name)
    return f"{m.group(1)}-{m.group(2)}-{m.group(3)}" if m else None


def targets(paths: list[str] | None, scope: str = "new") -> list[Path]:
    """scope=new  요구사항 확정일(2026-09-14) 이후 문서 + 날짜 없는 현행 참조 문서
       scope=all  전부 (옛 보고서 포함 — 이력 문서라 고치지 않고 backlog 로만 센다)

    옛 일일 보고를 고치지 않는 이유: 그날 실제로 보낸 글의 기록이다. 기록을 나중에
    고치면 무엇을 보냈는지 알 수 없게 된다. 규칙은 **앞으로 쓰는 글**에 적용한다.
    """
    if paths:
        return [Path(p) for p in paths]
    files: list[Path] = []
    for base, pattern in DEFAULT_GLOBS:
        if base.is_dir():
            files += sorted(base.glob(pattern))
    if scope == "all":
        return files
    keep = []
    for f in files:
        d = _doc_date(f)
        if d is None:
            keep.append(f)                      # 날짜 없는 문서 = 계속 고쳐 쓰는 현행 참조
        elif d >= CUTOFF:
            keep.append(f)
    return keep


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--paths", nargs="*")
    ap.add_argument("--json", dest="json_out")
    ap.add_argument("--scope", choices=["new", "all"], default="new")
    ap.add_argument("--quiet", action="store_true", help="위반만 출력")
    a = ap.parse_args()

    files = targets(a.paths, a.scope)
    findings: list[dict] = []
    for f in files:
        try:
            findings += scan(f)
        except Exception as e:                                   # noqa: BLE001
            print(f"[skip] {f}: {type(e).__name__}: {e}")

    by_file: dict[str, list[dict]] = {}
    for v in findings:
        by_file.setdefault(v["file"], []).append(v)

    print(f"검사 파일 {len(files)}개 · 위반 {len(findings)}건 · 위반 문서 {len(by_file)}개\n")
    for f in sorted(by_file, key=lambda k: -len(by_file[k])):
        rel = os.path.relpath(f, ROOT.parent)
        rules = {}
        for v in by_file[f]:
            rules[v["rule"]] = rules.get(v["rule"], 0) + 1
        print(f"── {rel}  ({', '.join(f'{k}×{n}' for k, n in sorted(rules.items()))})")
        for v in by_file[f][:8]:
            print(f"   {v['rule']} L{v['line']:>4}  {v['message']}")
            print(f"        | {v['text']}")
        if len(by_file[f]) > 8:
            print(f"   … 그 외 {len(by_file[f]) - 8}건")
    if not findings:
        print("위반 없음 — 2026-09-14 요구사항을 전부 통과했다.")
    if a.json_out:
        Path(a.json_out).write_text(json.dumps(
            {"files_scanned": len(files), "violations": findings}, ensure_ascii=False, indent=1),
            encoding="utf-8")
        print(f"\nsaved {a.json_out}")
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
