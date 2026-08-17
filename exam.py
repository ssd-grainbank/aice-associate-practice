#!/usr/bin/env python3
"""AICE Associate 모의 시험지 — 주피터 방식.

    python3 exam.py        세트 목록 보기
    python3 exam.py 3      3번 세트(11~15번 문제) 풀기
    python3 exam.py 3 -a   정답을 미리 보며 따라치기(학습 모드)
"""
import os
import sys
import time
import traceback
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
sys.path.insert(0, str(ROOT))

from bank import SETS, SET_TITLES, SETUP  # noqa: E402

W = 76
DIM = "\033[2m"; B = "\033[1m"; R = "\033[0m"
GREEN = "\033[32m"; RED = "\033[31m"; CYAN = "\033[36m"; YEL = "\033[33m"


def clear():
    os.system("clear")


def pause(msg):
    try:
        input(msg)
    except EOFError:
        print()


def rule(ch="─"):
    return ch * W


def show_menu():
    print(f"\n{B}AICE Associate 연습문제 100선 — 20세트{R}\n{rule('═')}")
    doms = {"데이터 분석": CYAN, "데이터 전처리": YEL, "AI 모델링": GREEN}
    for i, (_, qs) in enumerate(SETS):
        lo, hi = qs[0]["no"], qs[-1]["no"]
        dom = max(set(q["domain"] for q in qs), key=lambda d: sum(1 for q in qs if q["domain"] == d))
        c = doms.get(dom, "")
        pts = sum(q["score"] for q in qs)
        print(f"  {B}{i + 1:>2}{R}. {SET_TITLES[i]:<26} {DIM}{lo:>3}~{hi:<3}번{R}  {c}{dom:<8}{R} {pts:>2}점")
    print(rule("═"))
    print(f"\n  실행:  {B}aice 1{R}       (1세트 풀기)")
    print(f"  학습:  {B}aice 1 -a{R}    (정답 보며 따라치기 — 막힐 때)")
    print(f"\n  {DIM}어느 폴더에서든 됩니다. 목록 다시 보기: aice{R}\n")


def run_cell(code, ns):
    """주피터 셀처럼 실행. 마지막 줄이 표현식이면 그 값을 돌려준다."""
    body = code.strip()
    if not body:
        return None, None
    lines = body.split("\n")
    try:
        try:
            last = compile(lines[-1], "<cell>", "eval")
            if len(lines) > 1:
                exec(compile("\n".join(lines[:-1]), "<cell>", "exec"), ns)
            return eval(last, ns), None
        except SyntaxError:
            exec(compile(body, "<cell>", "exec"), ns)
            return None, None
    except Exception:
        return None, traceback.format_exc().strip().split("\n")[-1]


def needs_more(lines):
    """아직 문장이 안 끝났으면 True. (여러 줄 답을 이어 받기 위한 판단)"""
    src = "\n".join(lines)
    if src.rstrip().endswith((":", "\\", ",", "(", "[", "{")):
        return True
    try:
        compile(src, "<c>", "exec")
        return False
    except SyntaxError:
        # 괄호/따옴표가 안 닫힌 상태면 더 받는다. 그냥 오타면 그대로 실행해 오류를 보여준다.
        return src.count("(") > src.count(")") or src.count("[") > src.count("]") or src.count('"""') % 2 == 1
    except Exception:
        return False


def ask_cell(n):
    """[n]: 칸에 코드 입력. 한 줄이 완성되면 엔터 한 번으로 바로 실행됩니다.

    아무것도 안 친 채 엔터 두 번이면 빈 문자열을 돌려줍니다(포기 = 정답 보기)."""
    print(f"{CYAN}[{n}]:{R} ", end="", flush=True)
    lines = []
    empties = 0
    while True:
        try:
            raw = input()
        except EOFError:
            break
        if raw.strip() == "":
            if lines:          # 빈 줄 = 지금까지 친 것 실행
                break
            empties += 1
            if empties >= 2:   # 빈 채로 엔터 두 번 = 포기
                break
            print(f"{CYAN}[{n}]:{R} ", end="", flush=True)  # 한 번 더 기회
            continue
        empties = 0
        lines.append(raw)
        if not needs_more(lines):   # 문장이 완성됐으면 바로 실행
            break
        print(f"{CYAN}   :{R} ", end="", flush=True)
    print()
    return "\n".join(lines)


def render(q, idx, total, remaining):
    mins, secs = divmod(max(0, int(remaining)), 60)
    print(f"╔{rule('═')}╗")
    head = f"AICE Associate 모의 — {idx}/{total}문항"
    tail = f"남은시간 {mins:02d}:{secs:02d}"
    print(f"║ {B}{head}{R}{' ' * max(1, W - len(head) - len(tail) - 2)}{DIM}{tail}{R} ║")
    print(f"╠{rule('═')}╣")
    tag = f"[문제 {q['no']}]"
    dom = q["domain"]
    pts = f"({q['score']}점)"
    print(f"║ {B}{tag}{R} {DIM}{dom}{R}{' ' * max(1, W - len(tag) - len(dom) - len(pts) - 4)}{B}{pts}{R} ║")
    print(f"╟{rule('─')}╢")
    for raw in q["text"].split("\n"):
        line = raw.strip()
        while line:
            chunk, line = line[:W - 4], line[W - 4:]
            print(f"║  {chunk}{' ' * max(1, W - len(chunk) - 3)}║")
    if q.get("data"):
        note = f"사용 파일: {q['data']}"
        print(f"║  {DIM}{note}{R}{' ' * max(1, W - len(note) - 3)}║")
    print(f"╚{rule('═')}╝\n")


def main():
    args = [a for a in sys.argv[1:]]
    show_answer = "-a" in args or "--answer" in args
    nums = [a for a in args if a.isdigit()]

    if not nums:
        show_menu()
        return

    n = int(nums[0])
    if not 1 <= n <= 20:
        print(f"{RED}세트 번호는 1~20 사이입니다.{R}")
        return

    if not DATA.exists() or not (DATA / "customers.csv").exists():
        print(f"{YEL}데이터가 없습니다. 먼저 만듭니다...{R}")
        os.system(f'cd "{DATA}" && python3 make_data.py')

    os.chdir(DATA)  # 문제에서 "customers.csv" 처럼 파일명만 쓰도록
    _, questions = SETS[n - 1]
    ns = {"__name__": "__main__"}
    # 이 세트를 풀 수 있는 상태를 조용히 만들어 둔다 (앞 세트에서 이어지는 부분)
    setup = SETUP.get(n, "")
    if setup:
        run_cell(setup, ns)
    total_score = sum(q["score"] for q in questions)
    earned = 0
    log = []
    start = time.time()
    limit = 20 * 60

    clear()
    print(f"""
{B}세트 {n} — {SET_TITLES[n - 1]}{R}
{rule()}
  · {len(questions)}문항 / {total_score}점 / 권장 20분
  · 실제 시험과 같습니다. 보기는 없습니다. 코드를 직접 칩니다.
  · {CYAN}[n]:{R} 칸에 코드를 치고 {B}엔터 두 번{R}이면 실행됩니다.
  · 앞 문제의 결과가 뒤 문제로 이어집니다. 순서대로 푸세요.
  · 틀리면 정답이 나올 때까지 같은 문제를 다시 풉니다.
  · 모르면 빈 채로 엔터 두 번 → 정답과 해설이 나오고 다음으로 넘어갑니다.
{'  · ' + YEL + '학습 모드: 정답이 먼저 표시됩니다.' + R if show_answer else ''}
""")
    pause(f"  {B}엔터를 누르면 시작합니다.{R} ")

    for i, q in enumerate(questions, 1):
        clear()
        render(q, i, len(questions), limit - (time.time() - start))

        if show_answer:
            print(f"{YEL}  ── 정답 ──{R}")
            for ln in q["answer"].split("\n"):
                print(f"  {DIM}{ln}{R}")
            print()

        tries = 0
        while True:  # 맞히거나 포기할 때까지 같은 문제를 다시 받는다
            code = ask_cell(i)
            ns["__code__"] = code  # 채점 함수가 "실제로 친 코드"를 확인할 수 있게 전달

            if not code.strip():
                print(f"{YEL}  ── 넘어감. 정답 ──{R}")
                for ln in q["answer"].split("\n"):
                    print(f"  {DIM}{ln}{R}")
                run_cell(q["answer"], ns)  # 뒤 문제가 이어지도록 정답을 실행
                log.append((q, 0, "미응답" if tries == 0 else "포기"))
                break

            value, error = run_cell(code, ns)
            if error:
                print(f"{RED}  ✗ 오류: {error}{R}")
            elif value is not None:
                print(f"{DIM}  ── 출력 ──{R}")
                for ln in str(value).split("\n")[:15]:
                    print(f"  {ln}")

            ok = False
            if not error:
                try:
                    ok = bool(q["check"](ns))
                except Exception:
                    ok = False

            print()
            if ok:
                earned += q["score"]
                print(f"{GREEN}  ✓ 정답  +{q['score']}점{R}")
                log.append((q, q["score"], "정답"))
                break

            tries += 1
            print(f"{RED}  ✗ 아직 아닙니다 — 다시 풀어보세요.{R}")
            print(f"  {DIM}모르겠으면 빈 채로 엔터 두 번 → 정답이 나옵니다.{R}\n")

        print(f"  {DIM}{q['why']}{R}\n")
        pause(f"  {DIM}엔터로 다음{R} ")

    used = int(time.time() - start)
    pct = round(earned / total_score * 100)
    clear()
    print(f"\n{B}세트 {n} 채점 결과 — {SET_TITLES[n - 1]}{R}\n{rule('═')}")
    for q, got, mark in log:
        c = GREEN if got else RED
        title = q["text"].split("\n")[0][:40]
        print(f"  {c}{mark:>4}{R}  {q['no']:>3}번  {title:<42} {got:>2}/{q['score']}")
    print(rule("═"))
    grade = GREEN if pct >= 80 else (YEL if pct >= 60 else RED)
    print(f"  {B}{earned} / {total_score}점{R}   {grade}{pct}점 환산{R}   소요 {used // 60}분 {used % 60}초")
    print(f"  {DIM}실제 시험 합격선은 80점입니다.{R}")
    nxt = n + 1
    if nxt <= 20:
        print(f"\n  다음 세트:  {B}aice {nxt}{R}   {DIM}({SET_TITLES[nxt - 1]}){R}")
        print(f"  다시 풀기:  {B}aice {n}{R}\n")
    else:
        print(f"\n  {B}20세트 전부 완주했습니다.{R}\n")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n중단했습니다.\n")
