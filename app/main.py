import sys
import json
import uuid
import re
from pathlib import Path
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QListWidget, QStackedWidget, QFrame, QPushButton,
    QLineEdit, QScrollArea, QSizePolicy, QGridLayout, QComboBox,
    QDialog, QFormLayout, QTextEdit, QDialogButtonBox, QMessageBox, QFileDialog
)

from app.database import init_db
from app.recommendation import load_sample_recommendations


APP_STYLE = """
QMainWindow, QWidget {
    background: #0b0e16;
    color: #edf0fa;
    font-family: 'Malgun Gothic';
    font-size: 13px;
}
QFrame#sidebar { background: #101522; border-right: 1px solid #20283a; }
QLabel#brand { color: #f4f5ff; font-size: 23px; font-weight: 800; padding: 3px 4px; }
QLabel#brandAccent { color: #9b8cff; font-size: 23px; font-weight: 800; }
QLabel#sideCaption { color: #68748d; font-size: 10px; font-weight: 700; padding: 18px 12px 6px; }
QListWidget { background: transparent; border: 0; outline: 0; padding: 4px 8px; }
QListWidget::item { color: #9ba6bd; padding: 13px 12px; border-radius: 9px; margin: 3px 0; }
QListWidget::item:hover { background: #1a2233; color: #f2f3ff; }
QListWidget::item:selected { background: #292449; color: #c9c0ff; font-weight: 700; border-left: 3px solid #9b8cff; }
QLabel#eyebrow { color: #a69aff; font-size: 11px; font-weight: 800; letter-spacing: 1px; }
QLabel#pageTitle { color: #f5f6ff; font-size: 28px; font-weight: 800; }
QLabel#muted { color: #929db4; }
QLineEdit#search { background: #151b29; border: 1px solid #252e42; border-radius: 10px; padding: 10px 14px; color: #f1f2fa; min-width: 210px; }
QLineEdit#search:focus { border: 1px solid #8e80e8; }
QComboBox { background:#151b29; border:1px solid #252e42; border-radius:9px; padding:9px 11px; color:#e8ebf6; min-width:100px; }
QComboBox:hover { border:1px solid #7167b7; }
QComboBox QAbstractItemView { background:#151b29; color:#e8ebf6; selection-background-color:#39305f; border:1px solid #303951; }
QPushButton#characterCard { text-align:left; background:#141b2a; color:#e9ecf7; border:1px solid #273249; border-radius:12px; padding:13px; font-size:12px; font-weight:700; }
QPushButton#characterCard:hover { background:#1b2436; border:1px solid #8e80e8; color:#ffffff; }
QScrollArea#catalogScroll { border:0; background:transparent; }
QPushButton { background: #282344; color: #ded9ff; border: 1px solid #40366e; border-radius: 9px; padding: 10px 15px; font-weight: 700; }
QPushButton:hover { background: #39305f; }
QPushButton#primary { background: #8e80e8; color: #111020; border: 0; padding: 11px 17px; }
QPushButton#primary:hover { background: #a69aff; }
QPushButton#quiet { background: #171e2d; color: #c3cbe0; border: 1px solid #293349; }
QFrame#hero { background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #28234b, stop:0.55 #1a2540, stop:1 #132c39); border: 1px solid #3a3a61; border-radius: 18px; }
QFrame#gameCard { background: #141b2a; border: 1px solid #273249; border-radius: 15px; }
QFrame#gameCard:hover { border: 1px solid #7167b7; }
QFrame#statCard { background: #141b2a; border: 1px solid #263148; border-radius: 13px; }
QFrame#panel { background: #121927; border: 1px solid #263148; border-radius: 14px; }
QLabel#bigNumber { color: #f4f2ff; font-size: 25px; font-weight: 800; }
QLabel#tag { color: #bdb4ff; background: #292449; border-radius: 8px; padding: 5px 8px; font-size: 10px; font-weight: 700; }
QLabel#gameGenshin { color: #e6d8b0; font-size: 21px; font-weight: 800; }
QLabel#gameStarRail { color: #c8d9ff; font-size: 21px; font-weight: 800; }
QScrollArea { border: 0; background: transparent; }
QScrollBar:vertical { background: #0b0e16; width: 8px; margin: 2px; }
QScrollBar::handle:vertical { background: #303951; border-radius: 4px; min-height: 30px; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
"""


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("GameMate")
        self.resize(1360, 860)
        self.setMinimumSize(1050, 700)

        root = QWidget()
        root_layout = QHBoxLayout(root)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)
        self.setCentralWidget(root)

        root_layout.addWidget(self.build_sidebar())

        self.pages = QStackedWidget()
        self.pages.addWidget(self.build_dashboard())
        self.genshin_characters = self.load_genshin_characters()
        self.pages.addWidget(self.build_genshin_page())
        self.pages.addWidget(self.build_simple_page("붕괴: 스타레일", "캐릭터와 광추, 유물 정보를 정리하세요.", "캐릭터 도감과 유물 정보는 다음 업데이트에서 연결할 예정입니다."))
        self.pages.addWidget(self.build_simple_page("내 계정", "게임별 계정 데이터와 가져오기 상태를 확인하세요.", "공식적으로 허용되는 데이터 가져오기 방식을 우선 지원할 예정입니다."))
        self.pages.addWidget(self.build_simple_page("캐릭터 추천", "보유 캐릭터와 장비를 바탕으로 파티와 육성 방향을 추천합니다.", "계정 데이터와 캐릭터 데이터베이스가 준비되면 추천 기능을 활성화합니다."))
        self.pages.addWidget(self.build_settings_page())
        root_layout.addWidget(self.pages, 1)

        self.nav.currentRowChanged.connect(self.pages.setCurrentIndex)
        self.setStyleSheet(APP_STYLE)

    def build_sidebar(self):
        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(238)
        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(17, 24, 17, 18)
        layout.setSpacing(5)

        brand_row = QHBoxLayout()
        brand = QLabel("GAME")
        brand.setObjectName("brand")
        accent = QLabel("MATE")
        accent.setObjectName("brandAccent")
        brand_row.addWidget(brand)
        brand_row.addWidget(accent)
        brand_row.addStretch()
        layout.addLayout(brand_row)

        version = QLabel("GAME COMPANION  •  DESKTOP")
        version.setStyleSheet("color:#68748d; font-size:9px; font-weight:700; padding-left:4px;")
        layout.addWidget(version)
        layout.addSpacing(22)

        caption = QLabel("WORKSPACE")
        caption.setObjectName("sideCaption")
        layout.addWidget(caption)

        self.nav = QListWidget()
        self.nav.addItems([
            "⌂   대시보드",
            "✦   원신",
            "✧   붕괴: 스타레일",
            "▣   내 계정",
            "◇   캐릭터 추천",
            "⚙   설정",
        ])
        self.nav.setCurrentRow(0)
        layout.addWidget(self.nav, 1)

        tip = QFrame()
        tip.setObjectName("panel")
        tip_layout = QVBoxLayout(tip)
        tip_layout.setContentsMargins(13, 13, 13, 13)
        tip_title = QLabel("작은 팁")
        tip_title.setStyleSheet("font-weight:800; color:#c9c1ff;")
        tip_text = QLabel("계정 비밀번호나 인증 토큰을 GameMate에 저장하지 마세요.")
        tip_text.setWordWrap(True)
        tip_text.setStyleSheet("color:#8793aa; font-size:11px; line-height:1.4;")
        tip_layout.addWidget(tip_title)
        tip_layout.addWidget(tip_text)
        layout.addWidget(tip)

        footer = QLabel("EARLY ACCESS  •  v0.6")
        footer.setStyleSheet("color:#56627a; font-size:9px; padding:14px 4px 0;")
        layout.addWidget(footer)
        return sidebar

    def build_dashboard(self):
        page = QWidget()
        page_layout = QVBoxLayout(page)
        page_layout.setContentsMargins(34, 25, 34, 26)
        page_layout.setSpacing(18)

        header = QHBoxLayout()
        header_left = QVBoxLayout()
        eyebrow = QLabel("YOUR GAME HUB")
        eyebrow.setObjectName("eyebrow")
        title = QLabel("대시보드")
        title.setObjectName("pageTitle")
        subtitle = QLabel("오늘의 게임 생활을 한눈에 관리해 보세요.")
        subtitle.setObjectName("muted")
        header_left.addWidget(eyebrow)
        header_left.addWidget(title)
        header_left.addWidget(subtitle)
        header.addLayout(header_left)
        header.addStretch()

        search = QLineEdit()
        search.setObjectName("search")
        search.setPlaceholderText("⌕   캐릭터, 무기, 메뉴 검색")
        search.setClearButtonEnabled(True)
        header.addWidget(search)
        page_layout.addLayout(header)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        body = QWidget()
        body_layout = QVBoxLayout(body)
        body_layout.setContentsMargins(0, 2, 8, 8)
        body_layout.setSpacing(18)

        hero = QFrame()
        hero.setObjectName("hero")
        hero_layout = QHBoxLayout(hero)
        hero_layout.setContentsMargins(25, 23, 25, 23)
        hero_text = QVBoxLayout()
        hero_kicker = QLabel("WELCOME TO GAMEMATE")
        hero_kicker.setStyleSheet("color:#bcb3ff; font-size:10px; font-weight:800; letter-spacing:1px;")
        hero_title = QLabel("나의 게임 데이터를\n더 스마트하게.")
        hero_title.setStyleSheet("font-size:25px; font-weight:800; color:#ffffff;")
        hero_desc = QLabel("원신과 붕괴: 스타레일의 캐릭터, 장비, 파티 정보를\n한곳에서 정리하는 나만의 게임 허브입니다.")
        hero_desc.setStyleSheet("color:#b5bfd4; font-size:12px;")
        hero_desc.setWordWrap(True)
        hero_text.addWidget(hero_kicker)
        hero_text.addSpacing(4)
        hero_text.addWidget(hero_title)
        hero_text.addSpacing(5)
        hero_text.addWidget(hero_desc)
        hero_text.addSpacing(8)
        start_button = QPushButton("게임 둘러보기  →")
        start_button.setObjectName("primary")
        start_button.setFixedWidth(150)
        start_button.clicked.connect(lambda: self.nav.setCurrentRow(1))
        hero_text.addWidget(start_button, alignment=Qt.AlignLeft)
        hero_layout.addLayout(hero_text, 1)

        orb = QLabel("✦")
        orb.setAlignment(Qt.AlignCenter)
        orb.setStyleSheet("color:#c5bdff; font-size:100px; background:rgba(255,255,255,0.04); border:1px solid rgba(210,205,255,0.15); border-radius:65px; min-width:130px; min-height:130px; max-width:130px; max-height:130px;")
        hero_layout.addWidget(orb, alignment=Qt.AlignCenter)
        body_layout.addWidget(hero)

        section_title = self.section_heading("내 게임", "등록된 게임 공간으로 바로 이동하세요.")
        body_layout.addLayout(section_title)

        games = QHBoxLayout()
        games.setSpacing(14)
        games.addWidget(self.game_card(
            "GENSHIN IMPACT", "원신", "캐릭터 · 무기 · 성유물 · 파티",
            "TEYVAT ADVENTURE", "#d9c89c", 1
        ), 1)
        games.addWidget(self.game_card(
            "HONKAI: STAR RAIL", "붕괴: 스타레일", "캐릭터 · 광추 · 유물 · 파티",
            "TRAILBLAZE JOURNEY", "#a9c5ff", 2
        ), 1)
        body_layout.addLayout(games)

        stats = QHBoxLayout()
        stats.setSpacing(14)
        stats.addWidget(self.stat_card("등록된 게임", "02", "지원 게임"), 1)
        stats.addWidget(self.stat_card("계정 연결", "준비 중", "안전한 가져오기 방식 검토"), 1)
        stats.addWidget(self.stat_card("추천 시스템", "준비 중", "캐릭터 데이터 구축 예정"), 1)
        body_layout.addLayout(stats)

        lower = QHBoxLayout()
        lower.setSpacing(14)
        activity = QFrame()
        activity.setObjectName("panel")
        activity_layout = QVBoxLayout(activity)
        activity_layout.setContentsMargins(17, 15, 17, 15)
        activity_title = QLabel("최근 업데이트")
        activity_title.setStyleSheet("font-size:15px; font-weight:800;")
        activity_layout.addWidget(activity_title)
        activity_layout.addWidget(self.activity_line("01", "GameMate 기본 화면 구성", "완료  ·  현재 버전"))
        activity_layout.addWidget(self.activity_line("02", "게임별 캐릭터 도감", "다음 개발 단계"))
        activity_layout.addWidget(self.activity_line("03", "계정 데이터 가져오기", "데이터 제공 경로 검토 예정"))
        lower.addWidget(activity, 3)

        quick = QFrame()
        quick.setObjectName("panel")
        quick_layout = QVBoxLayout(quick)
        quick_layout.setContentsMargins(17, 15, 17, 15)
        quick_title = QLabel("빠른 메뉴")
        quick_title.setStyleSheet("font-size:15px; font-weight:800;")
        quick_layout.addWidget(quick_title)
        for label, row in [("내 계정 확인  →", 3), ("캐릭터 추천  →", 4), ("환경 설정  →", 5)]:
            button = QPushButton(label)
            button.setObjectName("quiet")
            button.clicked.connect(lambda checked=False, target=row: self.nav.setCurrentRow(target))
            quick_layout.addWidget(button)
        lower.addWidget(quick, 2)
        body_layout.addLayout(lower)

        note = QLabel("안내  ·  현재 버전은 화면 구성과 기본 데이터 구조를 제공하며, 실제 계정 연동 및 추천 기능은 순차적으로 추가됩니다.")
        note.setWordWrap(True)
        note.setStyleSheet("color:#68748d; font-size:10px; padding:2px 3px;")
        body_layout.addWidget(note)
        body_layout.addStretch()

        scroll.setWidget(body)
        page_layout.addWidget(scroll, 1)
        return page

    def section_heading(self, title_text, description):
        layout = QVBoxLayout()
        title = QLabel(title_text)
        title.setStyleSheet("font-size:17px; font-weight:800; color:#f1f2fb;")
        desc = QLabel(description)
        desc.setStyleSheet("font-size:11px; color:#8793aa;")
        layout.addWidget(title)
        layout.addWidget(desc)
        return layout

    def game_card(self, kicker, title_text, description, tag_text, accent, nav_row):
        card = QFrame()
        card.setObjectName("gameCard")
        card.setMinimumHeight(172)
        layout = QVBoxLayout(card)
        layout.setContentsMargins(18, 16, 18, 16)
        top = QHBoxLayout()
        label = QLabel(kicker)
        label.setStyleSheet(f"color:{accent}; font-size:9px; font-weight:800; letter-spacing:1px;")
        tag = QLabel(tag_text)
        tag.setObjectName("tag")
        top.addWidget(label)
        top.addStretch()
        top.addWidget(tag)
        layout.addLayout(top)
        name = QLabel(title_text)
        name.setStyleSheet("font-size:20px; font-weight:800; color:#f4f5ff;")
        layout.addWidget(name)
        desc = QLabel(description)
        desc.setStyleSheet("color:#8f9bb2; font-size:11px;")
        layout.addWidget(desc)
        layout.addStretch()
        button = QPushButton("공간 열기  →")
        button.setObjectName("quiet")
        button.clicked.connect(lambda: self.nav.setCurrentRow(nav_row))
        layout.addWidget(button, alignment=Qt.AlignLeft)
        return card

    def stat_card(self, title_text, value, caption):
        card = QFrame()
        card.setObjectName("statCard")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(16, 13, 16, 13)
        label = QLabel(title_text)
        label.setStyleSheet("color:#8793aa; font-size:11px; font-weight:700;")
        number = QLabel(value)
        number.setObjectName("bigNumber")
        if value == "준비 중":
            number.setStyleSheet("color:#c4bbff; font-size:19px; font-weight:800;")
        sub = QLabel(caption)
        sub.setStyleSheet("color:#69758c; font-size:10px;")
        layout.addWidget(label)
        layout.addWidget(number)
        layout.addWidget(sub)
        return card

    def activity_line(self, number, title_text, subtitle):
        row = QFrame()
        row_layout = QHBoxLayout(row)
        row_layout.setContentsMargins(0, 7, 0, 7)
        badge = QLabel(number)
        badge.setAlignment(Qt.AlignCenter)
        badge.setStyleSheet("background:#24213f; color:#bdb4ff; border-radius:8px; padding:7px; font-size:10px; font-weight:800; min-width:25px;")
        text_col = QVBoxLayout()
        title = QLabel(title_text)
        title.setStyleSheet("font-size:11px; font-weight:700; color:#e4e7f2;")
        detail = QLabel(subtitle)
        detail.setStyleSheet("font-size:10px; color:#7e8aa2;")
        text_col.addWidget(title)
        text_col.addWidget(detail)
        row_layout.addWidget(badge)
        row_layout.addLayout(text_col, 1)
        return row


    def genshin_data_paths(self):
        data_dir = Path(__file__).resolve().parent.parent / "data"
        return (
            data_dir / "genshin_characters.json",
            data_dir / "user_genshin_customizations.json",
        )

    def load_genshin_characters(self):
        base_path, user_path = self.genshin_data_paths()
        try:
            with base_path.open("r", encoding="utf-8") as f:
                payload = json.load(f)
            characters = payload.get("characters", [])
        except (OSError, json.JSONDecodeError):
            characters = []

        self.genshin_user_data = {
            "overrides": {},
            "custom_characters": [],
            "deleted_ids": [],
        }
        try:
            with user_path.open("r", encoding="utf-8") as f:
                loaded = json.load(f)
            if isinstance(loaded, dict):
                self.genshin_user_data.update(loaded)
        except (OSError, json.JSONDecodeError):
            pass

        deleted = set(self.genshin_user_data.get("deleted_ids", []))
        overrides = self.genshin_user_data.get("overrides", {})
        merged = []
        for original in characters:
            character = dict(original)
            if character.get("id") in deleted:
                continue
            character.update(overrides.get(character.get("id"), {}))
            character.setdefault("recommended_weapons", "")
            character.setdefault("recommended_artifacts", "")
            character.setdefault("artifact_main_stats", "")
            character.setdefault("artifact_sub_stats", "")
            character.setdefault("talent_priority", "")
            character.setdefault("recommended_team", "")
            character.setdefault("memo", "")
            merged.append(character)

        for character in self.genshin_user_data.get("custom_characters", []):
            character = dict(character)
            character.setdefault("recommended_weapons", "")
            character.setdefault("recommended_artifacts", "")
            character.setdefault("artifact_main_stats", "")
            character.setdefault("artifact_sub_stats", "")
            character.setdefault("talent_priority", "")
            character.setdefault("recommended_team", "")
            character.setdefault("memo", "")
            merged.append(character)
        return merged

    def save_genshin_user_data(self):
        _, user_path = self.genshin_data_paths()
        user_path.parent.mkdir(parents=True, exist_ok=True)
        temp_path = user_path.with_suffix(".tmp")
        with temp_path.open("w", encoding="utf-8") as f:
            json.dump(self.genshin_user_data, f, ensure_ascii=False, indent=2)
        temp_path.replace(user_path)

    def reload_genshin_characters(self, selected_id=None):
        self.genshin_characters = self.load_genshin_characters()
        self.refresh_genshin_catalog()
        self.genshin_count_label.setText(f"도감 {len(self.genshin_characters)}명")
        if selected_id:
            selected = next((c for c in self.genshin_characters if c.get("id") == selected_id), None)
            if selected:
                self.show_genshin_detail(selected)
                return
        if self.genshin_characters:
            self.show_genshin_detail(self.genshin_characters[0])
        else:
            self.genshin_detail_symbol.setText("✦")
            self.genshin_detail_name.setText("캐릭터가 없습니다")
            self.genshin_detail_meta.setText("새 캐릭터를 추가해 보세요.")
            self.genshin_detail_role.setText("전투 역할")
            self.genshin_detail_summary.setText("")
            self.genshin_detail_build.setText("")
            self.genshin_detail_stats.setText("")
            self.genshin_detail_talents.setText("")
            self.genshin_detail_team.setText("")
            self.genshin_detail_memo.setText("")

    def build_genshin_page(self):
        page = QWidget()
        page_layout = QVBoxLayout(page)
        page_layout.setContentsMargins(34, 25, 30, 26)
        page_layout.setSpacing(15)

        header = QHBoxLayout()
        titles = QVBoxLayout()
        eyebrow = QLabel("TEYVAT CHARACTER ARCHIVE")
        eyebrow.setObjectName("eyebrow")
        title = QLabel("원신 캐릭터 도감")
        title.setObjectName("pageTitle")
        subtitle = QLabel("캐릭터를 검색하고 원소, 무기, 역할 정보를 확인하세요.")
        subtitle.setObjectName("muted")
        titles.addWidget(eyebrow)
        titles.addWidget(title)
        titles.addWidget(subtitle)
        header.addLayout(titles)
        header.addStretch()
        self.genshin_count_label = QLabel(f"도감 {len(self.genshin_characters)}명")
        self.genshin_count_label.setObjectName("tag")
        header.addWidget(self.genshin_count_label, alignment=Qt.AlignVCenter)
        page_layout.addLayout(header)

        filters = QHBoxLayout()
        self.genshin_search = QLineEdit()
        self.genshin_search.setObjectName("search")
        self.genshin_search.setPlaceholderText("⌕   캐릭터 이름 검색")
        self.genshin_search.setClearButtonEnabled(True)
        self.genshin_element_filter = QComboBox()
        self.genshin_element_filter.addItems(["모든 원소", "불", "물", "얼음", "번개", "바람", "바위", "풀"])
        self.genshin_element_filter.setMinimumWidth(125)
        self.genshin_rarity_filter = QComboBox()
        self.genshin_rarity_filter.addItems(["모든 등급", "5성", "4성"])
        self.genshin_rarity_filter.setMinimumWidth(115)
        filters.addWidget(self.genshin_search, 1)
        filters.addWidget(self.genshin_element_filter)
        filters.addWidget(self.genshin_rarity_filter)
        page_layout.addLayout(filters)

        content = QHBoxLayout()
        content.setSpacing(15)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setMinimumWidth(500)
        scroll.setObjectName("catalogScroll")
        self.genshin_grid_host = QWidget()
        self.genshin_grid = QGridLayout(self.genshin_grid_host)
        self.genshin_grid.setContentsMargins(2, 2, 8, 8)
        self.genshin_grid.setSpacing(10)
        scroll.setWidget(self.genshin_grid_host)
        content.addWidget(scroll, 3)

        detail = QFrame()
        detail.setObjectName("panel")
        detail.setMinimumWidth(245)
        detail.setMaximumWidth(310)
        detail_layout = QVBoxLayout(detail)
        detail_layout.setContentsMargins(19, 19, 19, 19)
        detail_layout.setSpacing(11)
        self.genshin_detail_symbol = QLabel("✦")
        self.genshin_detail_symbol.setAlignment(Qt.AlignCenter)
        self.genshin_detail_symbol.setStyleSheet("font-size:48px; color:#bdb4ff; background:#24213f; border:1px solid #3b3564; border-radius:16px; min-height:112px;")
        self.genshin_detail_name = QLabel("캐릭터를 선택하세요")
        self.genshin_detail_name.setStyleSheet("font-size:20px; font-weight:800; color:#f5f4ff;")
        self.genshin_detail_meta = QLabel("도감에서 캐릭터 카드를 누르면\n상세 정보가 표시됩니다.")
        self.genshin_detail_meta.setStyleSheet("font-size:11px; color:#a5afc4; line-height:1.5;")
        self.genshin_detail_meta.setWordWrap(True)
        divider = QFrame()
        divider.setFrameShape(QFrame.HLine)
        divider.setStyleSheet("color:#293349;")
        self.genshin_detail_role = QLabel("역할")
        self.genshin_detail_role.setStyleSheet("font-size:10px; color:#8f9bb2; font-weight:700;")
        self.genshin_detail_summary = QLabel("캐릭터 설명")
        self.genshin_detail_summary.setStyleSheet("font-size:12px; color:#d3d9e8;")
        self.genshin_detail_summary.setWordWrap(True)
        self.genshin_detail_build = QLabel("추천 무기 · 성유물")
        self.genshin_detail_build.setStyleSheet("font-size:11px; color:#c7cde0; background:#171e2d; border-radius:9px; padding:10px;")
        self.genshin_detail_build.setWordWrap(True)
        self.genshin_detail_stats = QLabel("성유물 주옵션 · 부옵션")
        self.genshin_detail_stats.setStyleSheet("font-size:11px; color:#c7cde0; background:#171e2d; border-radius:9px; padding:10px;")
        self.genshin_detail_stats.setWordWrap(True)
        self.genshin_detail_talents = QLabel("특성 우선순위")
        self.genshin_detail_talents.setStyleSheet("font-size:11px; color:#c7cde0; background:#171e2d; border-radius:9px; padding:10px;")
        self.genshin_detail_talents.setWordWrap(True)
        self.genshin_detail_team = QLabel("추천 파티")
        self.genshin_detail_team.setStyleSheet("font-size:11px; color:#c7cde0; background:#171e2d; border-radius:9px; padding:10px;")
        self.genshin_detail_team.setWordWrap(True)
        self.genshin_detail_memo = QLabel("내 메모")
        self.genshin_detail_memo.setStyleSheet("font-size:11px; color:#bdb4ff; background:#171e2d; border-radius:9px; padding:10px;")
        self.genshin_detail_memo.setWordWrap(True)
        self.genshin_detail_note = QLabel("내가 수정한 정보는 기본 도감과 분리되어 자동 저장됩니다.")
        self.genshin_detail_note.setStyleSheet("font-size:10px; color:#748199; background:#171e2d; border-radius:9px; padding:10px;")
        self.genshin_detail_note.setWordWrap(True)
        self.genshin_selected_character = None

        manage_buttons = QHBoxLayout()
        self.genshin_add_button = QPushButton("＋ 추가")
        self.genshin_add_button.setObjectName("primary")
        self.genshin_add_button.clicked.connect(self.add_genshin_character)
        self.genshin_edit_button = QPushButton("수정")
        self.genshin_edit_button.setObjectName("quiet")
        self.genshin_edit_button.clicked.connect(self.edit_genshin_character)
        self.genshin_delete_button = QPushButton("삭제")
        self.genshin_delete_button.setObjectName("quiet")
        self.genshin_delete_button.clicked.connect(self.delete_genshin_character)
        manage_buttons.addWidget(self.genshin_add_button)
        manage_buttons.addWidget(self.genshin_edit_button)
        manage_buttons.addWidget(self.genshin_delete_button)
        detail_layout.addWidget(self.genshin_detail_symbol)
        detail_layout.addWidget(self.genshin_detail_name)
        detail_layout.addWidget(self.genshin_detail_meta)
        detail_layout.addWidget(divider)
        detail_layout.addWidget(self.genshin_detail_role)
        detail_layout.addWidget(self.genshin_detail_summary)
        detail_layout.addWidget(self.genshin_detail_build)
        detail_layout.addWidget(self.genshin_detail_stats)
        detail_layout.addWidget(self.genshin_detail_talents)
        detail_layout.addWidget(self.genshin_detail_team)
        detail_layout.addWidget(self.genshin_detail_memo)
        detail_layout.addStretch()
        detail_layout.addWidget(self.genshin_detail_note)
        detail_layout.addLayout(manage_buttons)
        detail_scroll = QScrollArea()
        detail_scroll.setWidgetResizable(True)
        detail_scroll.setFrameShape(QFrame.NoFrame)
        detail_scroll.setMinimumWidth(245)
        detail_scroll.setMaximumWidth(330)
        detail_scroll.setWidget(detail)
        content.addWidget(detail_scroll, 2)
        page_layout.addLayout(content, 1)

        self.genshin_search.textChanged.connect(self.refresh_genshin_catalog)
        self.genshin_element_filter.currentTextChanged.connect(self.refresh_genshin_catalog)
        self.genshin_rarity_filter.currentTextChanged.connect(self.refresh_genshin_catalog)
        self.refresh_genshin_catalog()
        if self.genshin_characters:
            self.show_genshin_detail(self.genshin_characters[0])
        return page

    def refresh_genshin_catalog(self):
        while self.genshin_grid.count():
            item = self.genshin_grid.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

        query = self.genshin_search.text().strip().lower()
        element = self.genshin_element_filter.currentText()
        rarity = self.genshin_rarity_filter.currentText()
        filtered = []
        for character in self.genshin_characters:
            if query and query not in character["name"].lower() and query not in character.get("english", "").lower():
                continue
            if element != "모든 원소" and character["element"] != element:
                continue
            if rarity != "모든 등급" and f'{character["rarity"]}성' != rarity:
                continue
            filtered.append(character)

        self.genshin_count_label.setText(f"검색 결과 {len(filtered)}명 / 전체 {len(self.genshin_characters)}명")
        for index, character in enumerate(filtered):
            card = QPushButton(
                f'{character["symbol"]}   {character["rarity"]}성\n'
                f'{character["name"]}\n'
                f'{character["element"]} · {character["weapon"]}\n'
                f'{character["role"]}'
            )
            card.setObjectName("characterCard")
            card.setMinimumHeight(112)
            card.setCursor(Qt.PointingHandCursor)
            card.clicked.connect(lambda checked=False, item=character: self.show_genshin_detail(item))
            self.genshin_grid.addWidget(card, index // 3, index % 3)

        if not filtered:
            empty = QLabel("검색 조건에 맞는 캐릭터가 없습니다.")
            empty.setStyleSheet("color:#8793aa; padding:20px;")
            self.genshin_grid.addWidget(empty, 0, 0)

    def show_genshin_detail(self, character):
        self.genshin_selected_character = character
        self.genshin_detail_symbol.setText(character.get("symbol", "✦"))
        self.genshin_detail_symbol.setStyleSheet(
            f'font-size:48px; color:{character.get("accent", "#bdb4ff")}; background:#1a2233; '
            'border:1px solid #35415a; border-radius:16px; min-height:112px;'
        )
        self.genshin_detail_name.setText(character.get("name", "이름 없음"))
        self.genshin_detail_meta.setText(
            f'{character.get("english", "")}\n'
            f'{character.get("rarity", 4)}성  ·  {character.get("element", "")} 원소\n'
            f'{character.get("weapon", "")}  ·  {character.get("region", "")}'
        )
        self.genshin_detail_role.setText(f'전투 역할  ·  {character.get("role", "미입력")}')
        self.genshin_detail_summary.setText(character.get("summary", "설명이 없습니다."))
        weapons = character.get("recommended_weapons", "").strip() or "미등록"
        artifacts = character.get("recommended_artifacts", "").strip() or "미등록"
        self.genshin_detail_build.setText(f"추천 무기\n{weapons}\n\n추천 성유물\n{artifacts}")
        main_stats = character.get("artifact_main_stats", "").strip() or "미등록"
        sub_stats = character.get("artifact_sub_stats", "").strip() or "미등록"
        self.genshin_detail_stats.setText(
            f"성유물 주옵션\n{main_stats}\n\n성유물 부옵션\n{sub_stats}"
        )
        self.genshin_detail_talents.setText(
            f"특성 우선순위\n{character.get('talent_priority', '').strip() or '미등록'}"
        )
        self.genshin_detail_team.setText(
            f"추천 파티\n{character.get('recommended_team', '').strip() or '미등록'}"
        )
        self.genshin_detail_memo.setText(f"내 메모\n{character.get('memo', '').strip() or '작성된 메모가 없습니다.'}")

    def open_character_editor(self, character=None):
        dialog = QDialog(self)
        dialog.setWindowTitle("캐릭터 추가" if character is None else f'{character.get("name", "캐릭터")} 정보 수정')
        dialog.setMinimumWidth(440)
        dialog.setStyleSheet(APP_STYLE)
        form = QFormLayout(dialog)
        form.setContentsMargins(22, 22, 22, 16)
        form.setSpacing(10)

        def line(value=""):
            widget = QLineEdit()
            widget.setText(str(value or ""))
            return widget

        name = line((character or {}).get("name"))
        english = line((character or {}).get("english"))
        rarity = QComboBox()
        rarity.addItems(["4", "5"])
        rarity.setCurrentText(str((character or {}).get("rarity", 4)))
        element = QComboBox()
        element.addItems(["불", "물", "얼음", "번개", "바람", "바위", "풀"])
        element.setCurrentText((character or {}).get("element", "불"))
        weapon = QComboBox()
        weapon.addItems(["한손검", "양손검", "장병기", "법구", "활"])
        weapon.setCurrentText((character or {}).get("weapon", "한손검"))
        region = line((character or {}).get("region"))
        role = line((character or {}).get("role"))
        symbol = line((character or {}).get("symbol", "✦"))
        accent = line((character or {}).get("accent", "#bdb4ff"))
        summary = QTextEdit()
        summary.setPlainText((character or {}).get("summary", ""))
        summary.setMaximumHeight(80)
        weapons = QTextEdit()
        weapons.setPlainText((character or {}).get("recommended_weapons", ""))
        weapons.setMaximumHeight(65)
        artifacts = QTextEdit()
        artifacts.setPlainText((character or {}).get("recommended_artifacts", ""))
        artifacts.setMaximumHeight(65)
        artifact_main_stats = QTextEdit()
        artifact_main_stats.setPlainText((character or {}).get("artifact_main_stats", ""))
        artifact_main_stats.setMaximumHeight(60)
        artifact_sub_stats = QTextEdit()
        artifact_sub_stats.setPlainText((character or {}).get("artifact_sub_stats", ""))
        artifact_sub_stats.setMaximumHeight(60)
        talent_priority = QTextEdit()
        talent_priority.setPlainText((character or {}).get("talent_priority", ""))
        talent_priority.setMaximumHeight(60)
        recommended_team = QTextEdit()
        recommended_team.setPlainText((character or {}).get("recommended_team", ""))
        recommended_team.setMaximumHeight(65)
        memo = QTextEdit()
        memo.setPlainText((character or {}).get("memo", ""))
        memo.setMaximumHeight(75)

        form.addRow("캐릭터 이름 *", name)
        form.addRow("영문 이름", english)
        form.addRow("등급", rarity)
        form.addRow("원소", element)
        form.addRow("무기", weapon)
        form.addRow("지역", region)
        form.addRow("전투 역할", role)
        form.addRow("카드 기호", symbol)
        form.addRow("강조 색상", accent)
        form.addRow("캐릭터 설명", summary)
        form.addRow("추천 무기", weapons)
        form.addRow("추천 성유물", artifacts)
        form.addRow("성유물 주옵션", artifact_main_stats)
        form.addRow("성유물 부옵션", artifact_sub_stats)
        form.addRow("특성 우선순위", talent_priority)
        form.addRow("추천 파티 (최대 4명)", recommended_team)
        form.addRow("내 메모", memo)

        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        form.addRow(buttons)

        if dialog.exec() != QDialog.Accepted:
            return None
        if not name.text().strip():
            QMessageBox.warning(self, "입력 확인", "캐릭터 이름은 꼭 입력해 주세요.")
            return None
        color = accent.text().strip() or "#bdb4ff"
        if not re.fullmatch(r"#[0-9a-fA-F]{6}", color):
            QMessageBox.warning(self, "색상 확인", "강조 색상은 #RRGGBB 형식으로 입력해 주세요.")
            return None

        return {
            "name": name.text().strip(),
            "english": english.text().strip(),
            "rarity": int(rarity.currentText()),
            "element": element.currentText(),
            "weapon": weapon.currentText(),
            "region": region.text().strip(),
            "role": role.text().strip(),
            "symbol": symbol.text().strip() or "✦",
            "accent": color,
            "summary": summary.toPlainText().strip(),
            "recommended_weapons": weapons.toPlainText().strip(),
            "recommended_artifacts": artifacts.toPlainText().strip(),
            "artifact_main_stats": artifact_main_stats.toPlainText().strip(),
            "artifact_sub_stats": artifact_sub_stats.toPlainText().strip(),
            "talent_priority": talent_priority.toPlainText().strip(),
            "recommended_team": recommended_team.toPlainText().strip(),
            "memo": memo.toPlainText().strip(),
        }

    def add_genshin_character(self):
        values = self.open_character_editor()
        if values is None:
            return
        values["id"] = "custom_" + uuid.uuid4().hex[:12]
        self.genshin_user_data.setdefault("custom_characters", []).append(values)
        self.save_genshin_user_data()
        self.reload_genshin_characters(values["id"])

    def edit_genshin_character(self):
        current = self.genshin_selected_character
        if not current:
            QMessageBox.information(self, "캐릭터 선택", "먼저 수정할 캐릭터를 선택해 주세요.")
            return
        values = self.open_character_editor(current)
        if values is None:
            return
        character_id = current["id"]
        custom = self.genshin_user_data.setdefault("custom_characters", [])
        custom_item = next((c for c in custom if c.get("id") == character_id), None)
        if custom_item is not None:
            custom_item.update(values)
        else:
            self.genshin_user_data.setdefault("overrides", {})[character_id] = values
        self.save_genshin_user_data()
        self.reload_genshin_characters(character_id)

    def delete_genshin_character(self):
        current = self.genshin_selected_character
        if not current:
            QMessageBox.information(self, "캐릭터 선택", "먼저 삭제할 캐릭터를 선택해 주세요.")
            return
        answer = QMessageBox.question(
            self, "캐릭터 삭제",
            f'{current.get("name", "이 캐릭터")}을(를) 도감에서 삭제할까요?\n기본 데이터 자체는 변경되지 않습니다.',
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if answer != QMessageBox.Yes:
            return
        character_id = current["id"]
        custom = self.genshin_user_data.setdefault("custom_characters", [])
        if any(c.get("id") == character_id for c in custom):
            self.genshin_user_data["custom_characters"] = [
                c for c in custom if c.get("id") != character_id
            ]
        else:
            deleted = set(self.genshin_user_data.setdefault("deleted_ids", []))
            deleted.add(character_id)
            self.genshin_user_data["deleted_ids"] = sorted(deleted)
            self.genshin_user_data.setdefault("overrides", {}).pop(character_id, None)
        self.save_genshin_user_data()
        self.reload_genshin_characters()


    def build_settings_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(38, 34, 38, 34)
        layout.setSpacing(16)

        eyebrow = QLabel("GAMEMATE SETTINGS")
        eyebrow.setObjectName("eyebrow")
        title = QLabel("설정 및 데이터 관리")
        title.setObjectName("pageTitle")
        desc = QLabel("직접 수정한 원신 도감 데이터를 안전하게 백업하고 복원할 수 있습니다.")
        desc.setObjectName("muted")
        desc.setWordWrap(True)
        layout.addWidget(eyebrow)
        layout.addWidget(title)
        layout.addWidget(desc)

        panel = QFrame()
        panel.setObjectName("panel")
        panel_layout = QVBoxLayout(panel)
        panel_layout.setContentsMargins(22, 22, 22, 22)
        panel_layout.setSpacing(12)

        panel_title = QLabel("원신 사용자 데이터")
        panel_title.setStyleSheet("font-size:17px; font-weight:800; color:#f1f2fb;")
        explanation = QLabel(
            "캐릭터 추가·수정·삭제 내용, 추천 무기와 성유물, 육성 정보 및 메모가 포함됩니다.\n"
            "백업 파일은 JSON 형식이며 다른 PC의 GameMate에서도 복원할 수 있습니다."
        )
        explanation.setStyleSheet("color:#929db4; font-size:12px;")
        explanation.setWordWrap(True)

        export_button = QPushButton("사용자 데이터 백업 내보내기")
        export_button.setObjectName("primary")
        export_button.clicked.connect(self.export_genshin_user_data)

        import_button = QPushButton("백업 파일에서 데이터 복원")
        import_button.setObjectName("quiet")
        import_button.clicked.connect(self.import_genshin_user_data)

        warning = QLabel(
            "주의: 복원하면 현재 사용자 데이터가 선택한 백업 파일의 내용으로 교체됩니다. "
            "복원 전 현재 데이터는 자동으로 별도 백업됩니다."
        )
        warning.setStyleSheet("color:#c9b98d; font-size:11px;")
        warning.setWordWrap(True)

        panel_layout.addWidget(panel_title)
        panel_layout.addWidget(explanation)
        panel_layout.addSpacing(5)
        panel_layout.addWidget(export_button, alignment=Qt.AlignLeft)
        panel_layout.addWidget(import_button, alignment=Qt.AlignLeft)
        panel_layout.addWidget(warning)
        layout.addWidget(panel)
        layout.addStretch()
        return page

    def export_genshin_user_data(self):
        default_name = "GameMate_원신_사용자데이터_백업.json"
        file_path, _ = QFileDialog.getSaveFileName(
            self, "사용자 데이터 백업", default_name, "JSON 파일 (*.json)"
        )
        if not file_path:
            return
        destination = Path(file_path)
        if destination.suffix.lower() != ".json":
            destination = destination.with_suffix(".json")
        try:
            with destination.open("w", encoding="utf-8") as f:
                json.dump(self.genshin_user_data, f, ensure_ascii=False, indent=2)
        except OSError as exc:
            QMessageBox.critical(self, "백업 실패", f"파일을 저장하지 못했습니다.\n{exc}")
            return
        QMessageBox.information(
            self, "백업 완료", f"사용자 데이터를 백업했습니다.\n{destination}"
        )

    def import_genshin_user_data(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "사용자 데이터 복원", "", "JSON 파일 (*.json)"
        )
        if not file_path:
            return
        try:
            with Path(file_path).open("r", encoding="utf-8") as f:
                imported = json.load(f)
        except (OSError, json.JSONDecodeError) as exc:
            QMessageBox.critical(self, "복원 실패", f"백업 파일을 읽을 수 없습니다.\n{exc}")
            return

        valid = (
            isinstance(imported, dict)
            and isinstance(imported.get("overrides", {}), dict)
            and isinstance(imported.get("custom_characters", []), list)
            and isinstance(imported.get("deleted_ids", []), list)
            and all(isinstance(item, dict) for item in imported.get("custom_characters", []))
            and all(isinstance(item, str) for item in imported.get("deleted_ids", []))
        )
        if not valid:
            QMessageBox.warning(
                self, "복원 실패",
                "GameMate 사용자 데이터 형식이 아닙니다. 올바른 백업 JSON 파일을 선택해 주세요."
            )
            return

        answer = QMessageBox.question(
            self,
            "데이터 복원 확인",
            "선택한 백업 파일로 현재 사용자 데이터를 교체할까요?\n"
            "현재 데이터는 복원 전에 자동 백업됩니다.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        if answer != QMessageBox.Yes:
            return

        _, user_path = self.genshin_data_paths()
        try:
            if user_path.exists():
                from datetime import datetime
                backup_stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_path = user_path.with_name(
                    f"user_genshin_customizations.backup_{backup_stamp}.json"
                )
                backup_path.write_bytes(user_path.read_bytes())

            self.genshin_user_data = imported
            self.save_genshin_user_data()
            self.reload_genshin_characters()
        except (OSError, TypeError, ValueError) as exc:
            QMessageBox.critical(self, "복원 실패", f"데이터를 저장하지 못했습니다.\n{exc}")
            return

        QMessageBox.information(
            self, "복원 완료", "백업 데이터가 복원되었습니다. 원신 도감을 확인해 주세요."
        )

    def build_simple_page(self, title_text, description, detail):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(38, 34, 38, 34)
        eyebrow = QLabel("GAMEMATE WORKSPACE")
        eyebrow.setObjectName("eyebrow")
        title = QLabel(title_text)
        title.setObjectName("pageTitle")
        desc = QLabel(description)
        desc.setObjectName("muted")
        desc.setWordWrap(True)
        panel = QFrame()
        panel.setObjectName("panel")
        panel_layout = QVBoxLayout(panel)
        panel_layout.setContentsMargins(24, 24, 24, 24)
        panel_title = QLabel("이 공간은 준비 중입니다")
        panel_title.setStyleSheet("font-size:18px; font-weight:800; color:#e8e6ff;")
        panel_detail = QLabel(detail)
        panel_detail.setStyleSheet("color:#929db4; font-size:12px;")
        panel_detail.setWordWrap(True)
        panel_layout.addWidget(panel_title)
        panel_layout.addWidget(panel_detail)
        panel_layout.addSpacing(12)
        layout.addWidget(eyebrow)
        layout.addWidget(title)
        layout.addWidget(desc)
        layout.addSpacing(22)
        layout.addWidget(panel)
        layout.addStretch()
        return page


def main():
    init_db()
    load_sample_recommendations()
    app = QApplication(sys.argv)
    app.setApplicationName("GameMate")
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()