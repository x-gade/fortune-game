from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QCloseEvent, QHideEvent, QShowEvent
from PySide6.QtWidgets import QHBoxLayout, QLabel, QSizePolicy, QVBoxLayout, QWidget

from models.question import Question
from models.team import Team
from ui.scoreboard_widget import ScoreboardWidget
from ui.timer_widget import TimerWidget
from ui.video_widget import VideoWidget
from ui.wheel_widget import WheelWidget


class DisplayWindow(QWidget):
    """
    Public display window for players and audience.
    Публичное окно отображения для игроков и зрителей.
    """

    public_wheel_finished = Signal()
    video_finished = Signal()
    visibility_changed = Signal(bool)

    def __init__(self, parent=None) -> None:
        """
        Initialize public display window.
        Инициализация публичного окна.
        """
        super().__init__(parent)

        self.setWindowTitle("Fortune Game - Display")
        self.resize(1280, 800)

        self.round_label = QLabel("Раунд не выбран")
        self.round_label.setAlignment(Qt.AlignCenter)
        self.round_label.setStyleSheet("font-size: 28px; font-weight: bold;")

        self.status_label = QLabel("Ожидание запуска")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet("font-size: 20px;")

        self.wheel = WheelWidget()
        self.wheel.spin_finished.connect(self.public_wheel_finished.emit)

        self.question_label = QLabel("Вопрос пока не выбран")
        self.question_label.setWordWrap(True)
        self.question_label.setAlignment(Qt.AlignCenter)
        self.question_label.setStyleSheet("font-size: 26px; padding: 16px;")

        self.answer_label = QLabel("")
        self.answer_label.setWordWrap(True)
        self.answer_label.setAlignment(Qt.AlignCenter)
        self.answer_label.setStyleSheet("font-size: 22px; color: #FFD166; padding: 12px;")

        self.timer_widget = TimerWidget()
        self.timer_widget.setMinimumWidth(460)
        self.timer_widget.setMaximumWidth(520)
        self.timer_widget.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

        self.scoreboard = ScoreboardWidget()
        self.scoreboard.setMinimumWidth(220)
        self.scoreboard.setMaximumWidth(240)
        self.scoreboard.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Preferred)

        self.video_widget = VideoWidget()
        self.video_widget.playback_finished.connect(self.video_finished.emit)
        self.video_widget.hide()

        left_layout = QVBoxLayout()
        left_layout.setSpacing(10)
        left_layout.addWidget(self.round_label)
        left_layout.addWidget(self.status_label)
        left_layout.addWidget(self.wheel, 4)
        left_layout.addWidget(self.video_widget, 4)
        left_layout.addWidget(self.question_label)
        left_layout.addWidget(self.answer_label)

        right_layout = QVBoxLayout()
        right_layout.setSpacing(18)
        right_layout.addWidget(self.timer_widget, 0, Qt.AlignHCenter | Qt.AlignTop)
        right_layout.addWidget(self.scoreboard, 0, Qt.AlignHCenter | Qt.AlignTop)
        right_layout.addStretch()

        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(20)
        main_layout.addLayout(left_layout, 5)
        main_layout.addLayout(right_layout, 2)

        self.setLayout(main_layout)

    def set_round_title(self, title: str) -> None:
        """
        Update round title.
        Обновить заголовок раунда.
        """
        self.round_label.setText(title)

    def set_status(self, text: str) -> None:
        """
        Update status line.
        Обновить строку статуса.
        """
        self.status_label.setText(text)

    def start_wheel_animation(self, payload: dict) -> None:
        """
        Start public wheel animation.
        Запустить анимацию публичного колеса.
        """
        labels = payload.get("labels", [])
        target_index = payload.get("target_index", 0)

        self.video_widget.stop()
        self.video_widget.hide()
        self.wheel.show()

        self.question_label.clear()
        self.answer_label.clear()

        self.wheel.start_spin(labels, target_index)

    def show_question(self, question: Question) -> None:
        """
        Show current question.
        Показать текущий вопрос.
        """
        self.video_widget.stop()
        self.video_widget.hide()
        self.wheel.show()
        self.question_label.setText(question.text)
        self.answer_label.clear()

    def show_answer(self, answer: str) -> None:
        """
        Show current answer as text.
        Показать текущий ответ текстом.
        """
        self.video_widget.stop()
        self.video_widget.hide()
        self.wheel.show()
        self.answer_label.setText(f"Ответ: {answer}")

    def update_scores(self, teams: list[Team]) -> None:
        """
        Update scoreboard.
        Обновить табло счета.
        """
        self.scoreboard.update_scores(teams)

    def play_video(self, payload: dict) -> None:
        """
        Play question or answer video on public screen.
        Проиграть видео вопроса или видео ответа на публичном экране.
        """
        file_path = payload.get("path")
        mode = payload.get("mode", "question")

        if not file_path:
            self.status_label.setText("Путь к видео не указан.")
            return

        self.video_widget.stop()

        if mode == "answer":
            self.answer_label.clear()

        self.wheel.hide()
        self.video_widget.show()
        self.video_widget.play_file(file_path)

    def pause_video(self) -> None:
        """
        Pause current public video.
        Поставить текущее публичное видео на паузу.
        """
        self.video_widget.pause()

    def resume_video(self) -> None:
        """
        Resume current public video.
        Продолжить текущее публичное видео.
        """
        self.video_widget.resume()

    def stop_video(self) -> None:
        """
        Stop current public video.
        Остановить текущее публичное видео.
        """
        self.video_widget.stop()
        self.video_widget.hide()
        self.wheel.show()

    def showEvent(self, event: QShowEvent) -> None:
        """
        Emit visibility state on show.
        Отправить состояние видимости при показе окна.
        """
        super().showEvent(event)
        self.visibility_changed.emit(True)

    def hideEvent(self, event: QHideEvent) -> None:
        """
        Emit visibility state on hide.
        Отправить состояние видимости при скрытии окна.
        """
        super().hideEvent(event)
        self.visibility_changed.emit(False)

    def closeEvent(self, event: QCloseEvent) -> None:
        """
        Stop playback before window closes.
        Остановить воспроизведение перед закрытием окна.
        """
        self.stop_video()
        super().closeEvent(event)