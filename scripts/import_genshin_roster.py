#!/usr/bin/env python3
"""Import the current Genshin character roster from genshin-db's public API."""
from __future__ import annotations
import json, re, sys, time
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen

API = "https://genshin-db-api.vercel.app/api/v5/characters"
ROOT = Path(__file__).resolve().parents[1]
DATA_FILE = ROOT / "data" / "genshin_characters.json"
ELEMENTS = {
    "Pyro": ("불", "♨", "#f19b68"), "Hydro": ("물", "≈", "#7bcdf2"),
    "Cryo": ("얼음", "❄", "#8ed5f4"), "Electro": ("번개", "⚡", "#c5a5ee"),
    "Anemo": ("바람", "✧", "#9ed9a5"), "Geo": ("바위", "◆", "#d6c69b"),
    "Dendro": ("풀", "❀", "#9ed9a5"),
}
WEAPONS = {"Sword":"한손검","Claymore":"양손검","Polearm":"장병기","Catalyst":"법구","Bow":"활"}
REGIONS = {"Mondstadt":"몬드","Liyue":"리월","Inazuma":"이나즈마","Sumeru":"수메르",
           "Fontaine":"폰타인","Natlan":"나타","Nod-Krai":"노드크라이",
           "Snezhnaya":"스네즈나야","Khaenri'ah":"켄리아","None":"미분류"}
TRAVELER_FORMS = [("Anemo","바람"),("Geo","바위"),("Electro","번개"),
                  ("Dendro","풀"),("Hydro","물"),("Pyro","불"),("Cryo","얼음")]

def api_get(params):
    url = API + "?" + urlencode(params)
    req = Request(url, headers={"User-Agent":"GameMate/1.0 roster importer"})
    with urlopen(req, timeout=30) as response:
        payload = json.loads(response.read().decode("utf-8"))
    return payload.get("result", payload) if isinstance(payload, dict) else payload

def unwrap(payload):
    if isinstance(payload, dict):
        if isinstance(payload.get("result"), dict): return payload["result"]
        if isinstance(payload.get("data"), dict): return payload["data"]
        return payload
    return {}

def slug(value):
    value = value.replace("'", "").replace(".", "")
    return re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_")

def pick(data, *keys, default=""):
    for key in keys:
        value = data.get(key)
        if value not in (None, ""): return value
    return default

def main():
    if not DATA_FILE.exists():
        print(f"데이터 파일을 찾을 수 없습니다: {DATA_FILE}")
        return 1
    old_payload = json.loads(DATA_FILE.read_text(encoding="utf-8"))
    old_characters = old_payload.get("characters", [])
    old_by_english = {str(c.get("english","")).casefold(): c for c in old_characters if c.get("english")}
    print("원신 캐릭터 목록을 가져오는 중입니다...")
    names_payload = api_get({"query":"names","matchCategories":"true","queryLanguages":"English"})
    if isinstance(names_payload, dict): names = list(names_payload.keys())
    elif isinstance(names_payload, list): names = [str(x) for x in names_payload if isinstance(x,str)]
    else: raise RuntimeError("캐릭터 이름 목록 응답 형식을 확인할 수 없습니다.")
    names = sorted(set(names), key=str.casefold)
    imported, failed = [], []
    for index, english_name in enumerate(names, start=1):
        if "traveler" in english_name.casefold(): continue
        try:
            raw = api_get({"query":english_name,"queryLanguages":"English","resultLanguage":"Korean"})
            data = unwrap(raw)
            if not data:
                failed.append(english_name); continue
            element_raw = str(pick(data,"element","vision",default=""))
            element_ko, symbol, accent = ELEMENTS.get(element_raw,("미확인","✦","#bdb4ff"))
            weapon_raw = str(pick(data,"weapontype","weaponType","weapon_type",default=""))
            region_raw = str(pick(data,"region","association","nation",default=""))
            existing = dict(old_by_english.get(english_name.casefold(),{}))
            localized = str(pick(data,"name","fullname",default=english_name))
            character = {
                **existing,
                "id": existing.get("id") or slug(english_name),
                "name": localized, "english": english_name,
                "rarity": int(pick(data,"rarity",default=existing.get("rarity",4)) or 4),
                "element": element_ko,
                "weapon": WEAPONS.get(weapon_raw,existing.get("weapon","미확인")),
                "region": REGIONS.get(region_raw,region_raw or existing.get("region","미분류")),
                "role": existing.get("role","전투 역할 정보 추가 예정"),
                "symbol": existing.get("symbol",symbol), "accent": existing.get("accent",accent),
                "summary": existing.get("summary") or str(pick(data,"description",default=f"{element_ko} 원소 캐릭터입니다.")),
                "recommended_weapons":existing.get("recommended_weapons",""),
                "recommended_artifacts":existing.get("recommended_artifacts",""),
                "artifact_main_stats":existing.get("artifact_main_stats",""),
                "artifact_sub_stats":existing.get("artifact_sub_stats",""),
                "talent_priority":existing.get("talent_priority",""),
                "recommended_team":existing.get("recommended_team",""),
                "memo":existing.get("memo",""), "data_version":"7.2",
            }
            imported.append(character)
        except Exception as exc:
            failed.append(f"{english_name} ({exc})")
        if index % 10 == 0: print(f"  {index}/{len(names)}명 확인 중...")
        time.sleep(0.12)
    for element, korean in TRAVELER_FORMS:
        element_ko, symbol, accent = ELEMENTS[element]
        imported.append({
            "id":f"traveler_{element.lower()}","name":f"여행자 ({korean})",
            "english":f"{element} Traveler","rarity":5,"element":element_ko,
            "weapon":"한손검","region":"여행자","role":"전투 역할 정보 추가 예정",
            "symbol":symbol,"accent":accent,"summary":f"{element_ko} 원소를 사용하는 여행자 형태입니다.",
            "recommended_weapons":"","recommended_artifacts":"","artifact_main_stats":"",
            "artifact_sub_stats":"","talent_priority":"","recommended_team":"","memo":"",
            "data_version":"7.2",
        })
    if not imported:
        print("가져온 캐릭터가 없습니다. 기존 데이터는 변경하지 않았습니다.")
        return 1
    imported_ids = {c["id"] for c in imported}
    for old in old_characters:
        if old.get("id") not in imported_ids: imported.append(old)
    DATA_FILE.write_text(json.dumps({"characters":imported},ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(f"완료: 기본 도감 {len(imported)}명 저장")
    if failed:
        print(f"확인하지 못한 캐릭터 {len(failed)}명: "+", ".join(failed))
        print("실패한 캐릭터는 기존 정보가 있으면 보존됩니다.")
    print("이제 GameMate를 다시 실행하면 갱신된 도감이 표시됩니다.")
    return 0

if __name__ == "__main__":
    try: raise SystemExit(main())
    except Exception as exc:
        print(f"가져오기 실패: {exc}")
        raise SystemExit(1)
