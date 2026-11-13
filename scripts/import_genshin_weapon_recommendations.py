#!/usr/bin/env python3
"""Import curated Genshin weapon rankings from Genshin Builds into GameMate."""
from __future__ import annotations

import json
import re
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from urllib.request import Request, urlopen

REPO = "https://raw.githubusercontent.com/Genshin-Impact-Helper-Team/genshin-builds/main/"
TREE_API = "https://api.github.com/repos/Genshin-Impact-Helper-Team/genshin-builds/git/trees/main?recursive=1"
ROOT = Path(__file__).resolve().parents[1]
ROSTER_FILE = ROOT / "data" / "genshin_characters.json"
OUTPUT_FILE = ROOT / "data" / "genshin_weapon_recommendations.json"

# Folder names that differ from the character's English display name.
ALIASES = {
    "raiden shogun": ["shogun-raiden"],
    "kamisato ayaka": ["kamisato-ayaka"],
    "kamisato ayato": ["kamisato-ayato"],
    "kaedehara kazuha": ["kaedehara-kazuha"],
    "sangonomiya kokomi": ["sangonomiya-kokomi"],
    "arataki itto": ["arataki-itto"],
    "kujou sara": ["kujou-sara"],
    "shikanoin heizou": ["shikanoin-heizou"],
    "kuki shinobu": ["kuki-shinobu"],
    "yae miko": ["yae-miko"],
    "yun jin": ["yun-jin"],
    "yanfei": ["yanfei"],
    "hu tao": ["hu-tao"],
    "tartaglia": ["tartaglia"],
    "wanderer": ["wanderer"],
    "layla": ["layla"],
    "lynette": ["lynette"],
    "freminet": ["freminet"],
    "gaming": ["gaming"],
    "chevreuse": ["chevreuse"],
    "cloud retainer": ["xianyun"],
    "xianyun": ["xianyun"],
    "mualani": ["mualani"],
    "kachina": ["kachina"],
    "xilonen": ["xilonen"],
    "citlali": ["citlali"],
    "lan yan": ["lan-yan"],
    "ifa": ["ifa"],
    "jahoda": ["jahoda"],
    "skirk": ["skirk"],
    "columbina": ["columbina"],
    "nefer": ["nefer"],
    "lauma": ["lauma"],
    "flins": ["flins"],
    "varka": ["varka"],
    "mavuika": ["mavuika"],
    "chasca": ["chasca"],
    "ororon": ["ororon"],
    "ineffa": ["ineffa"],
    "varesa": ["varesa"],
    "mona": ["mona"],
    "aloy": ["aloy"],
}

def get_text(url: str, timeout: int = 30) -> str:
    request = Request(url, headers={"User-Agent": "GameMate/1.0 (weapon guide importer)"})
    with urlopen(request, timeout=timeout) as response:
        return response.read().decode("utf-8")

def slug(value: str) -> str:
    value = value.casefold().replace("'", "").replace(".", "")
    return re.sub(r"[^a-z0-9]+", "-", value).strip("-")

def fetch_json(url: str):
    return json.loads(get_text(url))

def fetch_weapon_file(path: str):
    try:
        return path, fetch_json(REPO + path)
    except Exception as exc:
        print(f"  건너뜀: {path} ({exc})")
        return path, None

def main() -> int:
    if not ROSTER_FILE.exists():
        print(f"캐릭터 도감 파일을 찾을 수 없습니다: {ROSTER_FILE}")
        return 1

    roster = json.loads(ROSTER_FILE.read_text(encoding="utf-8")).get("characters", [])
    print("추천 무기 데이터 출처의 캐릭터 목록을 확인하는 중...")
    tree = fetch_json(TREE_API)
    weapon_paths = [
        item["path"] for item in tree.get("tree", [])
        if item.get("type") == "blob"
        and item.get("path", "").startswith("src/content/")
        and item.get("path", "").endswith("/weapons.json")
    ]

    folders = {}
    for path in weapon_paths:
        parts = path.split("/")
        if len(parts) >= 7:
            folder = "/".join(parts[:5])
            folders.setdefault(folder, []).append(path)

    print(f"무기 추천 파일 {len(weapon_paths)}개를 찾았습니다. 필요한 데이터를 내려받습니다.")
    fetched = {}
    with ThreadPoolExecutor(max_workers=10) as pool:
        futures = [pool.submit(fetch_weapon_file, path) for path in weapon_paths]
        for future in as_completed(futures):
            path, payload = future.result()
            if payload:
                fetched[path] = payload

    # Weapon IDs are translated to readable English display names by the source project.
    weapon_names = fetch_json(REPO + "src/i18n/en/weapons.json")
    changelog = fetch_json(REPO + "src/content/site/changelog.json")
    version = ""
    groups = changelog.get("groups", [])
    if groups:
        version = groups[0].get("version", "")

    output = {}
    unmatched = []
    matched = 0
    for character in roster:
        english = str(character.get("english") or character.get("name") or "").strip()
        candidates = ALIASES.get(english.casefold(), [])
        if not candidates:
            candidates = [slug(english)]
        # Traveler has element-specific guide folders but shares the same character slug.
        if "traveler" in english.casefold() or "여행자" in str(character.get("name", "")):
            candidates = ["traveler"]

        selected_folder = None
        for folder in folders:
            folder_slug = folder.split("/")[-1]
            if folder_slug in candidates:
                selected_folder = folder
                break
        if not selected_folder:
            unmatched.append(character.get("name", english))
            continue

        builds = []
        for path in sorted(folders[selected_folder]):
            payload = fetched.get(path)
            if not payload:
                continue
            build_parts = path.split("/")[5:-1]
            build_label = " / ".join(part.replace("-", " ").title() for part in build_parts) or "공통 추천"
            tiers = []
            for tier in payload.get("weapons", []):
                names = []
                for item in tier.get("items", []):
                    weapon_id = item if isinstance(item, str) else item.get("name", "")
                    display = weapon_names.get(weapon_id, weapon_id.replace("-", " ").title())
                    if display and display not in names:
                        names.append(display)
                if names:
                    tiers.append({"weapons": names})
            if tiers:
                builds.append({"build": build_label, "tiers": tiers[:6]})

        if builds:
            output[character.get("id", slug(english))] = {
                "builds": builds,
                "source": "Genshin Builds (Genshin Impact Helper Team)",
                "source_url": "https://genshin-impact-helper-team.github.io/genshin-builds/",
                "source_version": version,
            }
            matched += 1
        else:
            unmatched.append(character.get("name", english))

    if not output:
        print("가져온 추천 무기 데이터가 없습니다. 기존 데이터는 변경하지 않았습니다.")
        return 1

    payload = {
        "source": "Genshin Builds — Genshin Impact Helper Team",
        "source_url": "https://genshin-impact-helper-team.github.io/genshin-builds/",
        "source_version": version,
        "characters": output,
    }
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_FILE.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"완료! {matched}/{len(roster)}명 캐릭터의 추천 무기 데이터를 저장했습니다.")
    print(f"저장 위치: {OUTPUT_FILE}")
    if unmatched:
        print(f"가이드가 없거나 이름을 연결하지 못한 캐릭터 {len(unmatched)}명: " + ", ".join(unmatched))
    print("이제 GameMate를 다시 실행하면 캐릭터 상세 정보에 추천 무기가 표시됩니다.")
    return 0

if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"가져오기 실패: {exc}")
        raise SystemExit(1)
