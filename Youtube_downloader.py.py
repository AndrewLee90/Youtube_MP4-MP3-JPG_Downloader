import os
import subprocess
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QLabel, QLineEdit, QPushButton,
    QRadioButton, QButtonGroup, QFileDialog, QProgressBar, QWidget, QMessageBox
)
from yt_dlp import YoutubeDL


class DownloadThread(QThread):
    progress_signal = Signal(int)
    status_signal = Signal(str)
    error_signal = Signal(str)

    def __init__(self, url, output_path, selected_format, parent=None):
        super().__init__(parent)
        self.url = url
        self.output_path = output_path
        self.selected_format = selected_format

    def run(self):
        try:
            ffmpeg_path = r"C:\Users\Andrew_Lee\Desktop\MachineLearning\ffmpeg\ffmpeg-7.1.1-essentials_build\bin\ffmpeg.exe"
            ydl_opts = {
                'outtmpl': os.path.join(self.output_path, '%(title)s.%(ext)s'),
                'ffmpeg_location': ffmpeg_path,
            }

            if self.selected_format == "mp4":
                ydl_opts['format'] = 'bestvideo+bestaudio/best'
                ydl_opts['merge_output_format'] = 'mp4'
            elif self.selected_format == "mp3":
                ydl_opts['format'] = 'bestaudio/best'
                ydl_opts['postprocessors'] = [
                    {'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3', 'preferredquality': '192'},
                ]
            elif self.selected_format == "jpg":
                ydl_opts['format'] = 'bestvideo/best'

            with YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(self.url, download=True)

            if self.selected_format == "jpg":
                video_path = os.path.join(self.output_path, f"{info['title']}.mp4")
                output_dir = os.path.join(self.output_path, "frames")
                os.makedirs(output_dir, exist_ok=True)

                self.status_signal.emit("모든 프레임 저장 중...")
                subprocess.run([
                    ffmpeg_path, "-i", video_path,
                    os.path.join(output_dir, "frame%03d.jpg")
                ], check=True)

            self.progress_signal.emit(100)
            self.status_signal.emit(f"{self.selected_format.upper()} 다운로드 완료!")

        except Exception as e:
            self.error_signal.emit(str(e))


class YouTubeDownloaderApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("YouTube Downloader with Qt")
        self.setGeometry(100, 100, 500, 400)

        # 중앙 위젯 및 레이아웃 설정
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)

        # URL 입력 필드
        self.url_label = QLabel("유튜브 URL을 입력하세요:")
        self.layout.addWidget(self.url_label)
        self.url_input = QLineEdit()
        self.layout.addWidget(self.url_input)

        # 저장 경로 설정
        self.path_button = QPushButton("저장 경로 선택")
        self.path_button.clicked.connect(self.select_path)
        self.layout.addWidget(self.path_button)
        self.path_label = QLabel("저장경로 : downloads(기본값)")
        self.layout.addWidget(self.path_label)
        self.output_path = "downloads"

        # 파일 형식 선택 버튼 (아이콘 포함)
        self.format_label = QLabel("다운로드 형식을 선택하세요:")
        self.layout.addWidget(self.format_label)
        self.format_group = QButtonGroup(self)

        self.mp4_button = QRadioButton("MP4  (영상)")
        self.mp4_button.setIcon(QIcon("icons/video_icon.png"))  # 영상 아이콘 추가
        self.mp4_button.setChecked(True)
        self.format_group.addButton(self.mp4_button)
        self.layout.addWidget(self.mp4_button)

        self.mp3_button = QRadioButton("MP3  (음원)")
        self.mp3_button.setIcon(QIcon("icons/audio_icon.png"))  # 음원 아이콘 추가
        self.format_group.addButton(self.mp3_button)
        self.layout.addWidget(self.mp3_button)

        self.jpg_button = QRadioButton("JPG  (사진)")
        self.jpg_button.setIcon(QIcon("icons/image_icon.png"))  # 사진 아이콘 추가
        self.format_group.addButton(self.jpg_button)
        self.layout.addWidget(self.jpg_button)

        # 다운로드 버튼
        self.download_button = QPushButton("다운로드")
        self.download_button.clicked.connect(self.start_download)
        self.layout.addWidget(self.download_button)

        # 진행 바
        self.progress_bar = QProgressBar()
        self.progress_bar.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(self.progress_bar)

        # 상태 표시 레이블
        self.status_label = QLabel("")
        self.layout.addWidget(self.status_label)

    def select_path(self):
        """저장 경로 선택."""
        path = QFileDialog.getExistingDirectory(self, "저장 경로 선택")
        if path:  # 사용자가 경로를 선택한 경우
            self.output_path = path
            self.path_label.setText(f"저장경로 : {path}")  # QLabel 업데이트

    def start_download(self):
        """다운로드 작업 시작."""
        url = self.url_input.text()
        if not url:
            QMessageBox.critical(self, "오류", "URL을 입력해주세요!")
            self.status_label.setText("작업 대기 중...")
            return

        selected_format = "mp4" if self.mp4_button.isChecked() else "mp3" if self.mp3_button.isChecked() else "jpg"

        # QThread로 다운로드 작업 실행
        self.download_thread = DownloadThread(url, self.output_path, selected_format)
        self.download_thread.progress_signal.connect(self.update_progress)
        self.download_thread.status_signal.connect(self.update_status)
        self.download_thread.error_signal.connect(self.show_error)
        self.download_thread.start()

    def update_progress(self, value):
        """진행 바 업데이트."""
        self.progress_bar.setValue(value)

    def update_status(self, message):
        """상태 표시 업데이트."""
        self.status_label.setText(message)

    def show_error(self, message):
        """오류 메시지 처리."""
        QMessageBox.critical(self, "오류", f"다운로드 실패: {message}")
        self.status_label.setText("다운로드 실패...")


if __name__ == "__main__":
    app = QApplication([])
    window = YouTubeDownloaderApp()
    window.show()
    app.exec()
