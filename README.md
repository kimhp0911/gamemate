# GameMate

원신과 붕괴: 스타레일을 위한 개인 게임 데이터 관리 프로그램입니다. Windows 데스크톱에서 실행하는 Python + PySide6 앱입니다.

## 실행 환경

- Windows 10/11
- Python 3.11 이상

## 설치 및 실행

PowerShell에서 저장소 폴더로 이동한 뒤 아래 명령을 실행하세요.

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
python -m app.main
```

## 현재 포함된 기능

- GameMate 대시보드와 게임별 메뉴
- 원신 캐릭터 도감: 이름 검색, 원소/등급 필터, 상세 정보
- 캐릭터 추가·수정·삭제
- 추천 무기·성유물, 주옵션·부옵션, 특성 우선순위, 추천 파티 및 개인 메모 편집
- 사용자 편집 데이터 JSON 백업 및 복원
- SQLite 기반 로컬 데이터베이스와 추천 데이터 로더

## 데이터 위치

- `data/genshin_characters.json`: 기본 원신 캐릭터 데이터
- `data/user_genshin_customizations.json`: 내 캐릭터 편집 내용 (첫 실행 시 생성 가능)
- `gamemate.db`: 로컬 데이터베이스 (실행 시 생성)

개인 편집 데이터와 로컬 DB는 Git에 올리지 않도록 설정되어 있습니다. 백업 기능을 이용해 별도로 보관하세요.

## 개발 메모

계정 연동 및 자동 추천은 별도 검증과 개발이 필요한 기능입니다. HoYoverse 비밀번호, 쿠키, 인증 토큰을 수집하거나 저장하지 않는 방향을 기본으로 합니다.


## 원신 전체 캐릭터 도감 가져오기

현재 원신 버전 7.2 기준 캐릭터 기본 정보를 공개 데이터베이스에서 가져오는 스크립트를 포함합니다. 기존 GameMate 캐릭터의 개인 메모와 추천 입력값은 가능한 한 보존하며, 추천 빌드나 전투 역할을 임의로 만들어 넣지 않습니다.

GameMate 저장소 폴더에서 CMD를 열고 아래 명령을 실행하세요.

```cmd
python scripts/import_genshin_roster.py
```

가져오기가 끝나면 평소처럼 실행합니다.

```cmd
python -m app.main
```

- 데이터 출처: [genshin-db](https://github.com/theBowja/genshin-db) 공개 데이터 및 API
- 원신 버전 표기: 7.2
- 여행자는 원소별 형태를 별도 항목으로 표시합니다.
- API에서 확인되지 않은 추천 무기·성유물·파티 정보는 빈칸으로 두어 잘못된 공략이 들어가지 않도록 합니다.
