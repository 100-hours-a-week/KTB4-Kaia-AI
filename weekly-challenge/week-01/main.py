import argparse
import re
from pathlib import Path


TEMPLATES = {
    "1": ("학습노트", "## 핵심 개념\n## 왜 중요한가\n## 예시 / 코드\n## 느낀 점 / 의문점"),
    "2": ("아이디어",  "## 아이디어 요약\n## 배경 / 동기\n## 구체화 방안\n## 다음 액션"),
    "3": ("회고",     "## 잘 된 것\n## 아쉬운 것\n## 배운 것\n## 다음에 할 것"),
}

STOPWORDS = {
    "이", "그", "저", "있다", "없다", "하다", "되다",
    "the", "and", "or", "is", "in", "on", "at", "to", "for", "of", "a", "an",
}


# --- 핵심 로직 ---

def find_unorganized_files(vault_path: str) -> list[Path]:
    vault = Path(vault_path)
    return [
        f for f in vault.rglob("*.md")
        if "[[" not in f.read_text(encoding="utf-8", errors="ignore")
    ]


def extract_keywords(content: str) -> set[str]:
    content = re.sub(r"\[\[.*?\]\]", "", content)
    content = re.sub(r"[#*`_>|\-=]", " ", content)
    return {
        w for w in content.split()
        if len(w) >= 2 and not w.isdigit() and w.lower() not in STOPWORDS
    }


def suggest_links(current_file: Path, vault_path: str, top_n: int = 5) -> list[tuple[Path, set]]:
    current_words = extract_keywords(current_file.read_text(encoding="utf-8", errors="ignore"))
    results = []
    for f in Path(vault_path).rglob("*.md"):
        if f == current_file:
            continue
        common = current_words & extract_keywords(f.read_text(encoding="utf-8", errors="ignore"))
        if common:
            results.append((f, common))
    results.sort(key=lambda x: len(x[1]), reverse=True)
    return results[:top_n]


# --- 커맨드 핸들러 ---

def cmd_scan(args):
    vault_path = args.vault or input("Obsidian 볼트 경로를 입력하세요: ").strip()

    if not Path(vault_path).is_dir():
        print(f"경로를 찾을 수 없습니다: {vault_path}")
        return

    print("\n볼트 스캔 중...\n")
    files = find_unorganized_files(vault_path)

    if not files:
        print("정리가 필요한 파일이 없습니다.")
        return

    print(f"[[ 링크가 없는 파일 {len(files)}개 ]]\n")
    for i, f in enumerate(files, 1):
        print(f"  {i}. {f.relative_to(vault_path)}")

    raw = input("\n번호 선택: ").strip()
    if raw.lower() == "q":
        return
    if not raw.isdigit() or not (1 <= int(raw) <= len(files)):
        print("잘못된 입력입니다.")
        return

    chosen = files[int(raw) - 1]
    content = chosen.read_text(encoding="utf-8", errors="ignore")

    print(f"\n{'=' * 50}")
    print(f"  {chosen.name}")
    print(f"{'=' * 50}")
    print(content)
    print(f"{'=' * 50}\n")

    # 링크 제안
    print("[[ 링크 연결 제안 ]]")
    suggestions = suggest_links(chosen, vault_path)
    if suggestions:
        for i, (path, common) in enumerate(suggestions, 1):
            keywords = ", ".join(sorted(common)[:5])
            print(f"  {i}. [[{path.stem}]]  (공통 키워드: {keywords})")
    else:
        print("  연결 가능한 파일이 없습니다.")

    # 템플릿 제안
    print("\n[[ 템플릿 제안 ]]")
    for key, (name, _) in TEMPLATES.items():
        print(f"  {key}. {name}")

    tmpl_raw = input("\n번호 선택: ").strip()
    if tmpl_raw.lower() == "q":
        return
    if tmpl_raw not in TEMPLATES:
        print("잘못된 입력입니다.")
        return

    name, structure = TEMPLATES[tmpl_raw]
    print(f"\n[ {name} 템플릿 ]")
    for line in structure.split("\n"):
        print(f"  {line}")
    print("\n이 구조를 참고해서 노트를 정리해보세요.")


# --- argparse ---

def main():
    parser = argparse.ArgumentParser(description="Obsidian 노트 정리 도우미")
    subparsers = parser.add_subparsers(dest="command")

    scan_parser = subparsers.add_parser("scan", help="링크 없는 노트 찾기 + 제안")
    scan_parser.add_argument("--vault", help="Obsidian 볼트 경로 (생략 시 실행 중 입력)")
    scan_parser.set_defaults(func=cmd_scan)

    args = parser.parse_args()
    if args.command:
        args.func(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
