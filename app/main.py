import json
import sys
import uuid
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QListWidget, QStackedWidget, QLabel, QPushButton, QLineEdit,
    QGridLayout, QFrame, QMessageBox, QDialog, QFormLayout, QComboBox
)

ROOT = Path(__file__).resolve().parent.parent
CHARACTER_FILE = ROOT / "data" / "genshin_characters.json"
USER_FILE = ROOT / "data" / "user_genshin_customizations.json"

STYLE = """
QMainWindow, QWidget { background:#0b0e16; color:#edf0fa; font-family:'Malgun Gothic'; }
QListWidget { background:#101522; border:0; padding:12px; }
QListWidget::item { padding:13px; color:#aab4ca; }
QListWidget::item:selected { background:#292449; color:#d5ceff; }
QLabel#title { font-size:26px; font-weight:800; }
QFrame#card { background:#141b2a; border:1px solid #293349; border-radius:12px; }
QPushButton { background:#282344; color:#e5e0ff; border:1px solid #40366e; border-radius:8px; padding:9px 14px; }
QLineEdit, QComboBox { background:#151b29; color:#edf0fa; border:1px solid #303951; border-radius:8px; padding:9px; }
"""

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("GameMate")
        self.resize(1180, 760)
        self.characters = self.load_characters()
        root = QWidget()
        layout = QHBoxLayout(root)
        self.setCentralWidget(root)
        self.nav = QListWidget()
        self.nav.addItems(["대시보드", "원신 캐릭터 도감", "붕괴: 스타레일", "캐릭터 추천"])
        self.pages = QStackedWidget()
        layout.addWidget(self.nav, 1)
        layout.addWidget(self.pages, 4)
        self.pages.addWidget(self.dashboard())
        self.pages.addWidget(self.catalog())
        self.pages.addWidget(self.placeholder("붕괴: 스타레일", "캐릭터 도감은 다음 업데이트에서 추가할 예정입니다."))
        self.pages.addWidget(self.placeholder("캐릭터 추천", "보유 캐릭터와 추천 데이터를 연결할 예정입니다."))
        self.nav.currentRowChanged.connect(self.pages.setCurrentIndex)
        self.nav.setCurrentRow(0)
        self.setStyleSheet(STYLE)

    def load_characters(self):
        try:
            base = json.loads(CHARACTER_FILE.read_text(encoding="utf-8")).get("characters", [])
        except (OSError, json.JSONDecodeError):
            base = []
        try:
            user = json.loads(USER_FILE.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            user = {"overrides": {}, "custom_characters": [], "deleted_ids": []}
        deleted = set(user.get("deleted_ids", []))
        overrides = user.get("overrides", {})
        result = []
        for item in base:
            item = dict(item)
            if item.get("id") not in deleted:
                item.update(overrides.get(item.get("id"), {}))
                result.append(item)
        result.extend(user.get("custom_characters", []))
        self.user_data = user
        return result

    def save_user_data(self):
        USER_FILE.parent.mkdir(parents=True, exist_ok=True)
        USER_FILE.write_text(json.dumps(self.user_data, ensure_ascii=False, indent=2), encoding="utf-8")

    def dashboard(self):
        page = QWidget()
        box = QVBoxLayout(page)
        title = QLabel("GAME MATE")
        title.setObjectName("title")
        box.addWidget(title)
        box.addWidget(QLabel("나만의 게임 캐릭터와 정보를 한곳에서 관리하세요."))
        box.addWidget(QLabel("현재 원신 캐릭터 16명이 등록되어 있습니다."))
        box.addStretch()
        return page

    def catalog(self):
        page = QWidget()
        outer = QVBoxLayout(page)
        title = QLabel("원신 캐릭터 도감")
        title.setObjectName("title")
        outer.addWidget(title)
        self.search = QLineEdit()
        self.search.setPlaceholderText("캐릭터 이름 검색")
        self.search.textChanged.connect(self.refresh_cards)
        outer.addWidget(self.search)
        self.grid_host = QWidget()
        self.grid = QGridLayout(self.grid_host)
        outer.addWidget(self.grid_host)
        self.refresh_cards()
        return page

    def refresh_cards(self):
        while self.grid.count():
            item = self.grid.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        query = self.search.text().strip().lower()
        filtered = [c for c in self.characters if query in c.get("name", "").lower() or query in c.get("english", "").lower()]
        for i, character in enumerate(filtered):
            card = QPushButton(f'{character.get("name")}\n{character.get("rarity", 4)}성 · {character.get("element", "")} 원소')
            card.setMinimumHeight(80)
            card.clicked.connect(lambda checked=False, c=character: self.show_character(c))
            self.grid.addWidget(card, i // 3, i % 3)

    def show_character(self, character):
        details = "\n".join([
            character.get("name", ""),
            f'{character.get("english", "")} · {character.get("rarity", "")}성',
            f'{character.get("element", "")} 원소 · {character.get("weapon", "")}',
            character.get("summary", "")
        ])
        QMessageBox.information(self, "캐릭터 정보", details)

    def placeholder(self, title_text, description):
        page = QWidget()
        box = QVBoxLayout(page)
        title = QLabel(title_text)
        title.setObjectName("title")
        box.addWidget(title)
        box.addWidget(QLabel(description))
        box.addStretch()
        return page

def main():
    app = QApplication(sys.argv)
    app.setApplicationName("GameMate")
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
