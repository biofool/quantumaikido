"""
Video Post Helper - Drag videos to Instagram/Facebook/Buffer
Run: python video_poster.py
"""

import os
import json
import subprocess
import sys

from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QHBoxLayout, QLabel, QPushButton, QScrollArea,
                             QFrame, QFileDialog, QMessageBox)
from PyQt5.QtCore import Qt, QMimeData, QUrl, QPoint
from PyQt5.QtGui import QDrag, QFont, QColor, QPalette, QCursor

# Default folder
DEFAULT_FOLDER = r"C:\Users\sensie-ok\Downloads\quantuamaikido.com\instagram"


class DraggableLabel(QLabel):
    """Label that can be dragged to external applications"""

    def __init__(self, text, file_path, parent=None):
        super().__init__(text, parent)
        self.file_path = file_path
        self.setStyleSheet("""
            QLabel {
                background-color: #8b5cf6;
                color: white;
                font-weight: bold;
                padding: 8px;
                border-radius: 4px;
            }
            QLabel:hover {
                background-color: #a78bfa;
            }
        """)
        self.setCursor(QCursor(Qt.OpenHandCursor))
        self.setAlignment(Qt.AlignCenter)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.setCursor(QCursor(Qt.ClosedHandCursor))

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton:
            drag = QDrag(self)
            mime_data = QMimeData()

            # Set file URL for drag
            url = QUrl.fromLocalFile(self.file_path)
            mime_data.setUrls([url])

            drag.setMimeData(mime_data)
            drag.exec_(Qt.CopyAction)
            self.setCursor(QCursor(Qt.OpenHandCursor))

    def mouseReleaseEvent(self, event):
        self.setCursor(QCursor(Qt.OpenHandCursor))


class VideoCard(QFrame):
    """Card widget for each video"""

    def __init__(self, video_data, main_window, parent=None):
        super().__init__(parent)
        self.video_data = video_data
        self.main_window = main_window

        self.setStyleSheet("""
            QFrame {
                background-color: #1e293b;
                border-radius: 8px;
                padding: 10px;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setSpacing(8)

        # Title
        title = QLabel(video_data['title'][:60] + ('...' if len(video_data['title']) > 60 else ''))
        title.setStyleSheet("color: #f1f5f9; font-weight: bold; font-size: 11px;")
        title.setWordWrap(True)
        layout.addWidget(title)

        # Badge
        badge = QLabel("READY" if video_data['has_caption'] else "NO CAPTION")
        badge_color = "#22c55e" if video_data['has_caption'] else "#f59e0b"
        text_color = "white" if video_data['has_caption'] else "black"
        badge.setStyleSheet(f"""
            background-color: {badge_color};
            color: {text_color};
            font-size: 9px;
            font-weight: bold;
            padding: 2px 6px;
            border-radius: 3px;
        """)
        badge.setFixedWidth(80)
        layout.addWidget(badge)

        # Buttons row
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(5)

        # Copy Caption button
        copy_btn = QPushButton("Copy Caption")
        copy_btn.setStyleSheet("""
            QPushButton {
                background-color: #22c55e;
                color: white;
                border: none;
                padding: 6px 12px;
                border-radius: 4px;
                font-size: 10px;
            }
            QPushButton:hover {
                background-color: #16a34a;
            }
        """)
        copy_btn.setCursor(QCursor(Qt.PointingHandCursor))
        copy_btn.clicked.connect(self.copy_caption)
        btn_layout.addWidget(copy_btn)

        # Show in Folder button
        folder_btn = QPushButton("Show in Folder")
        folder_btn.setStyleSheet("""
            QPushButton {
                background-color: #334155;
                color: white;
                border: none;
                padding: 6px 12px;
                border-radius: 4px;
                font-size: 10px;
            }
            QPushButton:hover {
                background-color: #475569;
            }
        """)
        folder_btn.setCursor(QCursor(Qt.PointingHandCursor))
        folder_btn.clicked.connect(self.open_folder)
        btn_layout.addWidget(folder_btn)

        # Draggable zone - same row as buttons
        drag_label = DraggableLabel("DRAG", video_data['path'])
        btn_layout.addWidget(drag_label)

        btn_layout.addStretch()
        layout.addLayout(btn_layout)

    def copy_caption(self):
        text = self.video_data['title']
        if self.video_data['caption']:
            text += '\n\n' + self.video_data['caption']

        clipboard = QApplication.clipboard()
        clipboard.setText(text)
        self.main_window.show_toast("Caption copied!")

    def open_folder(self):
        subprocess.run(['explorer', '/select,', self.video_data['path']])


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.folder_path = DEFAULT_FOLDER
        self.videos = []
        self.filter_has_caption = False  # Filter state

        self.setWindowTitle("Video Post Helper")
        self.setGeometry(100, 100, 450, 750)
        self.setStyleSheet("background-color: #0f172a;")

        self.setup_ui()
        self.load_videos()

    def setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Header
        header = QFrame()
        header.setStyleSheet("background-color: #1e293b; padding: 10px;")
        header_layout = QHBoxLayout(header)

        title = QLabel("Video Post Helper")
        title.setStyleSheet("color: #a78bfa; font-size: 16px; font-weight: bold;")
        header_layout.addWidget(title)

        header_layout.addStretch()

        # Help button
        help_btn = QPushButton("?")
        help_btn.setFixedWidth(30)
        help_btn.setStyleSheet("""
            QPushButton {
                background-color: #334155;
                color: white;
                border: none;
                padding: 5px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #475569; }
        """)
        help_btn.setCursor(QCursor(Qt.PointingHandCursor))
        help_btn.clicked.connect(self.show_help)
        header_layout.addWidget(help_btn)

        # Filter button
        self.filter_btn = QPushButton("Ready Only")
        self.filter_btn.setCheckable(True)
        self.filter_btn.setStyleSheet("""
            QPushButton {
                background-color: #334155;
                color: white;
                border: none;
                padding: 5px 10px;
                border-radius: 4px;
            }
            QPushButton:hover { background-color: #475569; }
            QPushButton:checked {
                background-color: #22c55e;
            }
        """)
        self.filter_btn.setCursor(QCursor(Qt.PointingHandCursor))
        self.filter_btn.clicked.connect(self.toggle_filter)
        header_layout.addWidget(self.filter_btn)

        # Folder button
        folder_btn = QPushButton("Folder")
        folder_btn.setStyleSheet("""
            QPushButton {
                background-color: #334155;
                color: white;
                border: none;
                padding: 5px 10px;
                border-radius: 4px;
            }
            QPushButton:hover { background-color: #475569; }
        """)
        folder_btn.setCursor(QCursor(Qt.PointingHandCursor))
        folder_btn.clicked.connect(self.change_folder)
        header_layout.addWidget(folder_btn)

        # Refresh button
        refresh_btn = QPushButton("Refresh")
        refresh_btn.setStyleSheet("""
            QPushButton {
                background-color: #8b5cf6;
                color: white;
                border: none;
                padding: 5px 10px;
                border-radius: 4px;
            }
            QPushButton:hover { background-color: #a78bfa; }
        """)
        refresh_btn.setCursor(QCursor(Qt.PointingHandCursor))
        refresh_btn.clicked.connect(self.load_videos)
        header_layout.addWidget(refresh_btn)

        main_layout.addWidget(header)

        # Path label
        self.path_label = QLabel(self.folder_path)
        self.path_label.setStyleSheet("color: #64748b; font-size: 9px; padding: 5px 15px;")
        self.path_label.setWordWrap(True)
        main_layout.addWidget(self.path_label)

        # Stats
        self.stats_label = QLabel("")
        self.stats_label.setStyleSheet("color: #cbd5e1; font-size: 10px; padding: 0 15px;")
        main_layout.addWidget(self.stats_label)

        # Scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: #0f172a;
            }
            QScrollBar:vertical {
                background-color: #1e293b;
                width: 10px;
            }
            QScrollBar::handle:vertical {
                background-color: #475569;
                border-radius: 5px;
            }
        """)

        self.scroll_content = QWidget()
        self.scroll_layout = QVBoxLayout(self.scroll_content)
        self.scroll_layout.setSpacing(10)
        self.scroll_layout.setContentsMargins(15, 10, 15, 10)

        scroll.setWidget(self.scroll_content)
        main_layout.addWidget(scroll)

        # Toast (hidden by default)
        self.toast = QLabel("")
        self.toast.setStyleSheet("""
            background-color: #22c55e;
            color: white;
            font-weight: bold;
            padding: 10px 20px;
            border-radius: 5px;
        """)
        self.toast.setAlignment(Qt.AlignCenter)
        self.toast.hide()

    def load_videos(self):
        # Clear existing
        while self.scroll_layout.count():
            child = self.scroll_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        self.videos = []

        if not os.path.exists(self.folder_path):
            self.stats_label.setText("Folder not found")
            return

        # Find files
        files = {}
        for filename in os.listdir(self.folder_path):
            filepath = os.path.join(self.folder_path, filename)
            if not os.path.isfile(filepath):
                continue

            if '.' in filename:
                base_name = filename.rsplit('.', 1)[0]
                ext = filename.rsplit('.', 1)[1].lower()
            else:
                continue

            if base_name not in files:
                files[base_name] = {}

            if ext == 'mp4':
                files[base_name]['video'] = filepath
                files[base_name]['video_name'] = filename
            elif ext == 'json':
                files[base_name]['json'] = filepath

        # Process pairs
        for base_name, file_set in files.items():
            if 'video' not in file_set:
                continue

            metadata = {'title_text': '', 'caption_text': ''}
            if 'json' in file_set:
                try:
                    with open(file_set['json'], 'r', encoding='utf-8') as f:
                        metadata = json.load(f)
                except:
                    pass

            self.videos.append({
                'path': file_set['video'],
                'filename': file_set.get('video_name', ''),
                'title': metadata.get('title_text') or base_name[:50],
                'caption': metadata.get('caption_text', ''),
                'has_caption': bool(metadata.get('caption_text'))
            })

        self.videos.sort(key=lambda v: v['title'].lower())

        # Stats
        total = len(self.videos)
        ready = sum(1 for v in self.videos if v['has_caption'])
        self.stats_label.setText(f"Videos: {total} | Ready: {ready} | Need caption: {total - ready}")

        self.render_cards()

    def render_cards(self):
        """Render video cards with current filter"""
        # Clear existing
        while self.scroll_layout.count():
            child = self.scroll_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        # Filter videos
        if self.filter_has_caption:
            filtered = [v for v in self.videos if v['has_caption']]
        else:
            filtered = self.videos

        # Create cards
        for video in filtered:
            card = VideoCard(video, self)
            self.scroll_layout.addWidget(card)

        self.scroll_layout.addStretch()

    def toggle_filter(self):
        self.filter_has_caption = self.filter_btn.isChecked()
        self.render_cards()

    def change_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Folder", self.folder_path)
        if folder:
            self.folder_path = folder
            self.path_label.setText(folder)
            self.load_videos()

    def show_toast(self, message):
        self.toast.setText(message)
        self.toast.adjustSize()

        # Position at bottom center
        x = (self.width() - self.toast.width()) // 2
        y = self.height() - self.toast.height() - 30
        self.toast.move(x, y)
        self.toast.show()

        # Hide after 1.5 seconds
        from PyQt5.QtCore import QTimer
        QTimer.singleShot(1500, self.toast.hide)

    def show_help(self):
        help_text = """HOW TO POST VIDEOS

1. DRAG the purple "DRAG VIDEO TO BROWSER" bar
   directly to Facebook/Instagram upload area

2. Click "Copy Caption" to copy text to clipboard

3. Paste caption with Ctrl+V

FACEBOOK REELS:
https://www.facebook.com/reels/create

INSTAGRAM:
Go to instagram.com, click + (Create)

HASHTAGS:
#aikido #quantumaikido #martialarts
#harmony #mindfulness #budo"""

        QMessageBox.information(self, "How to Post", help_text)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
