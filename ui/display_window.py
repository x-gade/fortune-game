from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QCloseEvent, QHideEvent, QShowEvent
from PySide6.QtWidgets import (
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

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

    SIDE_PANEL_WIDTH = 460

    def __init__(self, parent=None) -> None:
        """
        Initialize public display window.
        Инициализация публичного окна.
        """
        super().__init__(parent)

        self.setWindowTitle("Fortune Game - Display")
        self.resize(1380, 840)

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
        self.timer_widget.setMinimumWidth(self.SIDE_PANEL_WIDTH)
        self.timer_widget.setMaximumWidth(self.SIDE_PANEL_WIDTH)
        self.timer_widget.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

        self.scoreboard = ScoreboardWidget()
        self.scoreboard.setMinimumWidth(self.SIDE_PANEL_WIDTH)
        self.scoreboard.setMaximumWidth(self.SIDE_PANEL_WIDTH)
        self.scoreboard.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Preferred)

        self.extra_time_status_title = QLabel("Дополнительное время")
        self.extra_time_status_title.setStyleSheet("font-size: 16px; font-weight: 700;")

        self.extra_time_status_value = QLabel("Нет данных")
        self.extra_time_status_value.setWordWrap(True)
        self.extra_time_status_value.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        self.extra_time_status_value.setMinimumWidth(self.SIDE_PANEL_WIDTH)
        self.extra_time_status_value.setMaximumWidth(self.SIDE_PANEL_WIDTH)
        self.extra_time_status_value.setStyleSheet(
            """
            background-color: #2f2f2f;
            border: 1px solid #666666;
            border-radius: 8px;
            padding: 10px;
            font-size: 13px;
            """
        )

        self.current_award_title = QLabel("Текущая награда")
        self.current_award_title.setStyleSheet("font-size: 16px; font-weight: 700;")

        self.current_award_value = QLabel("Нет активного вопроса")
        self.current_award_value.setWordWrap(True)
        self.current_award_value.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        self.current_award_value.setMinimumWidth(self.SIDE_PANEL_WIDTH)
        self.current_award_value.setMaximumWidth(self.SIDE_PANEL_WIDTH)
        self.current_award_value.setStyleSheet(
            """
            background-color: #2f2f2f;
            border: 1px solid #666666;
            border-radius: 8px;
            padding: 10px;
            font-size: 13px;
            """
        )

        self.extra_time_indicator_title = QLabel("Индикаторы допвремени активной команды:")

        self.extra_time_plus_10_button = QPushButton("+10")
        self.extra_time_plus_15_button = QPushButton("+15")
        self.extra_time_plus_30_button = QPushButton("+30")
        self.extra_time_plus_60_button = QPushButton("+1м")

        self.extra_time_buttons_map = {
            10: self.extra_time_plus_10_button,
            15: self.extra_time_plus_15_button,
            30: self.extra_time_plus_30_button,
            60: self.extra_time_plus_60_button,
        }

        for button in self.extra_time_buttons_map.values():
            button.setEnabled(False)
            button.setMinimumHeight(34)
            button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

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

        extra_time_buttons_grid = QGridLayout()
        extra_time_buttons_grid.setContentsMargins(0, 0, 0, 0)
        extra_time_buttons_grid.setHorizontalSpacing(8)
        extra_time_buttons_grid.setVerticalSpacing(8)
        extra_time_buttons_grid.addWidget(self.extra_time_plus_10_button, 0, 0)
        extra_time_buttons_grid.addWidget(self.extra_time_plus_15_button, 0, 1)
        extra_time_buttons_grid.addWidget(self.extra_time_plus_30_button, 1, 0)
        extra_time_buttons_grid.addWidget(self.extra_time_plus_60_button, 1, 1)

        self.extra_time_buttons_widget = QWidget()
        self.extra_time_buttons_widget.setMinimumWidth(self.SIDE_PANEL_WIDTH)
        self.extra_time_buttons_widget.setMaximumWidth(self.SIDE_PANEL_WIDTH)
        self.extra_time_buttons_widget.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.extra_time_buttons_widget.setLayout(extra_time_buttons_grid)

        right_layout = QVBoxLayout()
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(14)
        right_layout.setAlignment(Qt.AlignTop)

        right_layout.addWidget(self.scoreboard)
        right_layout.addWidget(self.extra_time_status_title)
        right_layout.addWidget(self.extra_time_status_value)
        right_layout.addWidget(self.timer_widget)
        right_layout.addWidget(self.current_award_title)
        right_layout.addWidget(self.current_award_value)
        right_layout.addWidget(self.extra_time_indicator_title)
        right_layout.addWidget(self.extra_time_buttons_widget)
        right_layout.addStretch()

        self.right_panel = QWidget()
        self.right_panel.setMinimumWidth(self.SIDE_PANEL_WIDTH)
        self.right_panel.setMaximumWidth(self.SIDE_PANEL_WIDTH)
        self.right_panel.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)
        self.right_panel.setLayout(right_layout)

        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(20)
        main_layout.addLayout(left_layout, 1)
        main_layout.addWidget(self.right_panel, 0, Qt.AlignTop)

        self.setLayout(main_layout)
        self.update_extra_time_state({})

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

    def _set_extra_time_button_style(
        self,
        button: QPushButton,
        *,
        is_selected: bool,
        is_available: bool,
    ) -> None:
        """
        Apply visual style for extra-time indicator button.
        Применить визуальный стиль для индикаторной кнопки допвремени.
        """
        if is_selected:
            border_color = "#c74d5f"
            background_color = "#4f3035"
        elif is_available:
            border_color = "#4d7fd1"
            background_color = "#334154"
        else:
            border_color = "#7a7a7a"
            background_color = "#4a4a4a"

        button.setStyleSheet(
            f"""
            QPushButton {{
                border: 2px solid {border_color};
                background-color: {background_color};
                color: #ffffff;
                border-radius: 8px;
                padding: 6px 10px;
                font-weight: 700;
            }}
            """
        )

    def update_extra_time_state(self, payload: dict) -> None:
        """
        Update public extra-time indicators.
        Обновить публичные индикаторы допвремени.
        """
        if not payload:
            self.extra_time_status_value.setText("Раунд не выбран.\nДополнительное время недоступно.")
            self.current_award_value.setText("Нет активного вопроса")
            for button in self.extra_time_buttons_map.values():
                self._set_extra_time_button_style(button, is_selected=False, is_available=False)
            return

        active_team_id = payload.get("active_team_id")
        selected_bonus_seconds = payload.get("selected_bonus_seconds", 0)
        time_expired = payload.get("time_expired", False)
        base_points = payload.get("base_points", 0)
        award_points = payload.get("award_points", 0)
        award_percent = payload.get("award_percent", 0)

        active_team_usage = None
        lines = []

        for team_state in payload.get("team_states", []):
            team_name = team_state.get("team_name", "Команда")
            used = team_state.get("used", False)
            bonus_seconds = team_state.get("bonus_seconds", 0)
            penalty_percent = team_state.get("penalty_percent", 0)
            is_active = team_state.get("is_active", False)

            prefix = "•"
            if is_active:
                prefix = "▶"

            if used:
                line = (
                    f"{prefix} {team_name}: использовано +{bonus_seconds} сек, "
                    f"награда {100 - penalty_percent}%"
                )
            else:
                line = f"{prefix} {team_name}: не использовано"

            lines.append(line)

            if team_state.get("team_id") == active_team_id:
                active_team_usage = team_state

        self.extra_time_status_value.setText("\n".join(lines) if lines else "Нет команд.")

        if time_expired:
            self.current_award_value.setText(
                f"Базовая награда: {base_points}\n"
                f"Текущая награда: {award_points}\n"
                f"Время вышло, доступно только 5%."
            )
        elif base_points > 0:
            if selected_bonus_seconds > 0:
                self.current_award_value.setText(
                    f"Базовая награда: {base_points}\n"
                    f"Текущая награда: {award_points}\n"
                    f"Использовано +{selected_bonus_seconds} сек, награда {award_percent}%."
                )
            else:
                self.current_award_value.setText(
                    f"Базовая награда: {base_points}\n"
                    f"Текущая награда: {award_points}\n"
                    f"Без штрафа, награда 100%."
                )
        else:
            self.current_award_value.setText("Нет активного вопроса")

        team_already_used = bool(active_team_usage and active_team_usage.get("used", False))

        for seconds, button in self.extra_time_buttons_map.items():
            is_selected = selected_bonus_seconds == seconds
            is_available = (
                active_team_id is not None
                and not time_expired
                and base_points > 0
                and (not team_already_used or is_selected)
            )
            self._set_extra_time_button_style(
                button,
                is_selected=is_selected,
                is_available=is_available,
            )

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