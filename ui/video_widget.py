from pathlib import Path

from PySide6.QtCore import QUrl, Signal
from PySide6.QtMultimedia import QAudioOutput, QMediaPlayer
from PySide6.QtMultimediaWidgets import QVideoWidget
from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget


class VideoWidget(QWidget):
    """
    Video playback widget.
    Виджет воспроизведения видео.
    """

    playback_finished = Signal()

    def __init__(self, parent=None) -> None:
        """
        Initialize video widget.
        Инициализация видео-виджета.
        """
        super().__init__(parent)

        self.info_label = QLabel("Видео не запущено")
        self.video_widget = QVideoWidget()

        self.audio_output = QAudioOutput(self)
        self.player = QMediaPlayer(self)
        self.player.setAudioOutput(self.audio_output)
        self.player.setVideoOutput(self.video_widget)
        self.player.mediaStatusChanged.connect(self._on_media_status_changed)

        layout = QVBoxLayout()
        layout.addWidget(self.info_label)
        layout.addWidget(self.video_widget)
        self.setLayout(layout)

    def play_file(self, file_path: str) -> None:
        """
        Play video file from local path.
        Проиграть видеофайл по локальному пути.
        """
        path = Path(file_path)
        self.info_label.setText(f"Видео: {path.name}")

        if not path.exists():
            self.info_label.setText(f"Видео не найдено: {file_path}")
            self.playback_finished.emit()
            return

        self.player.setSource(QUrl.fromLocalFile(str(path.resolve())))
        self.player.play()

    def stop(self) -> None:
        """
        Stop current playback.
        Остановить текущее воспроизведение.
        """
        self.player.stop()

    def _on_media_status_changed(self, status) -> None:
        """
        Handle media status updates.
        Обработать изменение статуса медиа.
        """
        if status == QMediaPlayer.EndOfMedia:
            self.playback_finished.emit()