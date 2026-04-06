from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QSpinBox,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from models.question import Question
from models.team import Team
from ui.game_settings_window import GameSettingsWindow
from ui.scoreboard_widget import ScoreboardWidget
from ui.timer_widget import TimerWidget
from ui.wheel_widget import WheelWidget


class AdminWindow(QWidget):
    """
    Admin control window.
    Админское окно управления.
    """

    def __init__(self, controller, parent=None) -> None:
        """
        Initialize admin window.
        Инициализация админского окна.
        """
        super().__init__(parent)
        self.controller = controller
        self.settings_window: GameSettingsWindow | None = None

        self.setWindowTitle("Fortune Game - Admin")
        self.resize(1320, 900)

        self.round_combo = QComboBox()
        self._refresh_round_combo_items()

        self.select_round_button = QPushButton("Применить раунд")
        self.spin_button = QPushButton("Крутить колесо")
        self.repeat_button = QPushButton("Повторить вопрос")
        self.show_answer_button = QPushButton("Показать ответ")
        self.correct_button = QPushButton("Верный ответ")
        self.wrong_button = QPushButton("Неверный ответ")
        self.video_pause_resume_button = QPushButton("Пауза видео")
        self.video_pause_resume_button.hide()

        self.timer_start_button = QPushButton("Старт таймера")
        self.timer_pause_resume_button = QPushButton("Пауза таймера")
        self.timer_stop_button = QPushButton("Стоп таймера")

        self.current_team_value = QLabel("Нет активной команды")
        self.next_team_value = QLabel("Нет следующей команды")
        self.round_progress_value = QLabel("Раунд не выбран")

        self.manual_score_team_combo = QComboBox()
        self._refresh_team_combo_items()

        self.manual_score_spin = QSpinBox()
        self.manual_score_spin.setRange(1, 100000)
        self.manual_score_spin.setValue(100)

        self.manual_add_points_button = QPushButton("Начислить очки")
        self.manual_remove_points_button = QPushButton("Списать очки")

        self.settings_button = QPushButton("Настройки игры")
        self.display_window_button = QPushButton("Показать игровое окно")

        self.wheel = WheelWidget()
        self.timer_widget = TimerWidget()
        self.scoreboard = ScoreboardWidget()
        self.scoreboard.setMinimumWidth(220)

        self.question_text = QTextEdit()
        self.question_text.setReadOnly(True)

        self.answer_text = QTextEdit()
        self.answer_text.setReadOnly(True)

        self.status_label = QLabel("Готово")
        self.status_label.setAlignment(Qt.AlignCenter)

        self._apply_local_styles()
        self._apply_size_policies()
        self._build_layout()
        self._connect_events()

        self.controller.scoreboard_changed.connect(self.scoreboard.update_scores)
        self.controller.scoreboard_changed.connect(self._update_admin_scoreboard)
        self.controller.status_changed.connect(self.status_label.setText)
        self.controller.round_title_changed.connect(self._set_round_title)
        self.controller.question_selected.connect(self._show_question)
        self.controller.answer_requested.connect(self._show_answer)
        self.controller.wheel_spin_requested.connect(self.wheel.start_spin)
        self.controller.timer_updated.connect(self.timer_widget.set_seconds)
        self.controller.timer_paused.connect(self._on_timer_paused)
        self.controller.timer_started.connect(self._on_timer_started)
        self.controller.timer_stopped.connect(self._on_timer_stopped)
        self.controller.active_team_changed.connect(self.current_team_value.setText)
        self.controller.next_team_changed.connect(self.next_team_value.setText)
        self.controller.round_progress_changed.connect(self.round_progress_value.setText)
        self.controller.video_state_changed.connect(self._update_video_button_state)
        self.controller.teams_changed.connect(self._refresh_team_combo_items)
        self.controller.rounds_changed.connect(self._refresh_round_combo_items)

        self.scoreboard.update_scores(self.controller.game.teams)
        self.current_team_value.setText(self.controller.get_active_team_name())
        self.next_team_value.setText(self.controller.get_next_team_name())
        self._update_video_button_state()
        self._on_timer_stopped()
        self._update_display_button_state(
            self.controller.display_window is not None and self.controller.display_window.isVisible()
        )

    def _apply_local_styles(self) -> None:
        """
        Apply local styles for action buttons in admin window.
        Применить локальные стили для action-кнопок в окне администратора.
        """
        self.setStyleSheet(
            """
            QPushButton#spinButton,
            QPushButton#timerStartButton,
            QPushButton#correctButton,
            QPushButton#manualAddPointsButton {
                border: 2px solid #4f7a67;
                color: #ffffff;
                background-color: #505050;
            }

            QPushButton#spinButton:hover,
            QPushButton#timerStartButton:hover,
            QPushButton#correctButton:hover,
            QPushButton#manualAddPointsButton:hover {
                border: 2px solid #6a9a84;
                background-color: #5a5a5a;
            }

            QPushButton#spinButton:pressed,
            QPushButton#timerStartButton:pressed,
            QPushButton#correctButton:pressed,
            QPushButton#manualAddPointsButton:pressed {
                border: 2px solid #3f6555;
                background-color: #454545;
            }

            QPushButton#timerPauseButton {
                border: 2px solid #9a7448;
                color: #ffffff;
                background-color: #505050;
            }

            QPushButton#timerPauseButton:hover {
                border: 2px solid #b38857;
                background-color: #5a5a5a;
            }

            QPushButton#timerPauseButton:pressed {
                border: 2px solid #7f5f3d;
                background-color: #454545;
            }

            QPushButton#wrongButton,
            QPushButton#timerStopButton,
            QPushButton#manualRemovePointsButton {
                border: 2px solid #8a4f56;
                color: #ffffff;
                background-color: #505050;
            }

            QPushButton#wrongButton:hover,
            QPushButton#timerStopButton:hover,
            QPushButton#manualRemovePointsButton:hover {
                border: 2px solid #a8656d;
                background-color: #5a5a5a;
            }

            QPushButton#wrongButton:pressed,
            QPushButton#timerStopButton:pressed,
            QPushButton#manualRemovePointsButton:pressed {
                border: 2px solid #6f4046;
                background-color: #454545;
            }

            QPushButton#settingsButton,
            QPushButton#displayWindowButton {
                border: 2px solid #4d6481;
                color: #ffffff;
                background-color: #505050;
            }

            QPushButton#settingsButton:hover,
            QPushButton#displayWindowButton:hover {
                border: 2px solid #637d9c;
                background-color: #5a5a5a;
            }

            QPushButton#settingsButton:pressed,
            QPushButton#displayWindowButton:pressed {
                border: 2px solid #3f526a;
                background-color: #454545;
            }
            """
        )

        self.spin_button.setObjectName("spinButton")
        self.correct_button.setObjectName("correctButton")
        self.wrong_button.setObjectName("wrongButton")

        self.timer_start_button.setObjectName("timerStartButton")
        self.timer_pause_resume_button.setObjectName("timerPauseButton")
        self.timer_stop_button.setObjectName("timerStopButton")

        self.manual_add_points_button.setObjectName("manualAddPointsButton")
        self.manual_remove_points_button.setObjectName("manualRemovePointsButton")

        self.settings_button.setObjectName("settingsButton")
        self.display_window_button.setObjectName("displayWindowButton")

    def _apply_size_policies(self) -> None:
        """
        Apply size policies and unified heights for key buttons.
        Применить size policy и единую высоту для ключевых кнопок.
        """
        uniform_height = 34

        buttons_to_normalize = [
            self.manual_add_points_button,
            self.manual_remove_points_button,
            self.settings_button,
            self.display_window_button,
        ]

        for button in buttons_to_normalize:
            button.setMinimumHeight(uniform_height)
            button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

    def _build_layout(self) -> None:
        """
        Build widget layout.
        Построить компоновку виджетов.
        """
        top_controls = QGridLayout()
        top_controls.setHorizontalSpacing(8)
        top_controls.setVerticalSpacing(8)

        top_controls.addWidget(QLabel("Раунд:"), 0, 0)
        top_controls.addWidget(self.round_combo, 0, 1)
        top_controls.addWidget(self.select_round_button, 0, 2)
        top_controls.addWidget(self.spin_button, 0, 3)

        top_controls.addWidget(QLabel("Сейчас отвечает:"), 1, 0)
        top_controls.addWidget(self.current_team_value, 1, 1)
        top_controls.addWidget(QLabel("Следующая команда:"), 1, 2)
        top_controls.addWidget(self.next_team_value, 1, 3)

        top_controls.addWidget(QLabel("Прогресс раунда:"), 2, 0)
        top_controls.addWidget(self.round_progress_value, 2, 1, 1, 3)

        top_section = QHBoxLayout()
        top_section.setSpacing(14)
        top_section.addLayout(top_controls, 5)
        top_section.addWidget(self.scoreboard, 1, Qt.AlignTop)

        button_row = QHBoxLayout()
        button_row.setSpacing(8)
        button_row.addWidget(self.repeat_button)
        button_row.addWidget(self.show_answer_button)
        button_row.addWidget(self.correct_button)
        button_row.addWidget(self.wrong_button)

        video_row = QHBoxLayout()
        video_row.addWidget(self.video_pause_resume_button, 1)

        timer_row = QHBoxLayout()
        timer_row.setSpacing(8)
        timer_row.addWidget(self.timer_start_button)
        timer_row.addWidget(self.timer_pause_resume_button)
        timer_row.addWidget(self.timer_stop_button)

        manual_score_grid = QGridLayout()
        manual_score_grid.setHorizontalSpacing(10)
        manual_score_grid.setVerticalSpacing(8)

        manual_score_grid.addWidget(QLabel("Ручная корректировка счета:"), 0, 0, 1, 3)
        manual_score_grid.addWidget(QLabel("Команда:"), 1, 0)
        manual_score_grid.addWidget(self.manual_score_team_combo, 1, 1, 1, 2)

        manual_score_grid.addWidget(QLabel("Очки:"), 2, 0)
        manual_score_grid.addWidget(self.manual_score_spin, 2, 1, 1, 2)

        manual_buttons_row = QHBoxLayout()
        manual_buttons_row.setSpacing(8)
        manual_buttons_row.addWidget(self.manual_add_points_button, 1)
        manual_buttons_row.addWidget(self.manual_remove_points_button, 1)
        manual_score_grid.addLayout(manual_buttons_row, 3, 0, 1, 3)

        windows_row = QHBoxLayout()
        windows_row.setSpacing(8)
        windows_row.addWidget(self.settings_button, 1)
        windows_row.addWidget(self.display_window_button, 1)

        left_layout = QVBoxLayout()
        left_layout.setSpacing(10)
        left_layout.addLayout(top_section)
        left_layout.addWidget(self.wheel, 4)
        left_layout.addLayout(button_row)
        left_layout.addLayout(video_row)
        left_layout.addLayout(timer_row)
        left_layout.addWidget(self.timer_widget)
        left_layout.addLayout(manual_score_grid)
        left_layout.addLayout(windows_row)
        left_layout.addWidget(QLabel("Текущий вопрос:"))
        left_layout.addWidget(self.question_text, 2)
        left_layout.addWidget(QLabel("Ответ:"))
        left_layout.addWidget(self.answer_text, 1)
        left_layout.addWidget(self.status_label)

        self.setLayout(left_layout)

    def _connect_events(self) -> None:
        """
        Connect button actions.
        Подключить действия кнопок.
        """
        self.select_round_button.clicked.connect(self._select_round)
        self.spin_button.clicked.connect(self._spin)
        self.repeat_button.clicked.connect(self.controller.repeat_question)
        self.show_answer_button.clicked.connect(self.controller.show_answer)
        self.correct_button.clicked.connect(self.controller.mark_correct)
        self.wrong_button.clicked.connect(self.controller.mark_wrong)
        self.video_pause_resume_button.clicked.connect(self.controller.toggle_video_pause_resume)

        self.timer_start_button.clicked.connect(self.controller.start_timer)
        self.timer_pause_resume_button.clicked.connect(self._toggle_timer_pause_resume)
        self.timer_stop_button.clicked.connect(self.controller.stop_timer)

        self.manual_add_points_button.clicked.connect(self._add_manual_points)
        self.manual_remove_points_button.clicked.connect(self._remove_manual_points)

        self.settings_button.clicked.connect(self._toggle_settings_window)
        self.display_window_button.clicked.connect(self._toggle_display_window)

    def _select_round(self) -> None:
        """
        Apply selected round.
        Применить выбранный раунд.
        """
        round_id = self.round_combo.currentData()
        self.controller.select_round(round_id)

    def _spin(self) -> None:
        """
        Start wheel for current round and current queue team.
        Запустить колесо для текущего раунда и текущей команды по очереди.
        """
        if self.controller.game.state.current_round_id is None:
            round_id = self.round_combo.currentData()
            self.controller.select_round(round_id)

        self.controller.spin_next_question()

    def _show_question(self, question: Question) -> None:
        """
        Show selected question in admin panel.
        Показать выбранный вопрос в панели администратора.
        """
        self.question_text.setPlainText(question.text)
        self.answer_text.clear()

    def _show_answer(self, answer: str) -> None:
        """
        Show answer in admin panel.
        Показать ответ в панели администратора.
        """
        self.answer_text.setPlainText(answer)

    def _set_round_title(self, title: str) -> None:
        """
        Reflect round change in admin status.
        Отразить смену раунда в статусе админа.
        """
        self.status_label.setText(f"Активный раунд: {title}")

    def _update_admin_scoreboard(self, teams: list[Team]) -> None:
        """
        Update local scoreboard widget.
        Обновить локальный виджет счета.
        """
        self.scoreboard.update_scores(teams)

    def _update_video_button_state(self) -> None:
        """
        Update video pause/resume button visibility and text.
        Обновить видимость и текст кнопки паузы/продолжения видео.
        """
        if not self.controller.is_video_question_context():
            self.video_pause_resume_button.hide()
            return

        if not self.controller.is_video_visible_now():
            self.video_pause_resume_button.hide()
            return

        self.video_pause_resume_button.show()

        if self.controller.is_video_paused():
            self.video_pause_resume_button.setText("Продолжить видео")
        else:
            self.video_pause_resume_button.setText("Пауза видео")

    def _toggle_timer_pause_resume(self) -> None:
        """
        Toggle timer pause or resume from one button.
        Переключить паузу или продолжение таймера одной кнопкой.
        """
        if self.timer_pause_resume_button.text() == "Продолжить таймер":
            self.controller.start_timer()
        else:
            self.controller.pause_timer()

    def _on_timer_started(self) -> None:
        """
        Update timer buttons when timer starts or resumes.
        Обновить кнопки таймера при запуске или продолжении.
        """
        self.timer_widget.set_running()
        self.timer_pause_resume_button.setText("Пауза таймера")

    def _on_timer_paused(self) -> None:
        """
        Update timer buttons when timer is paused.
        Обновить кнопки таймера при паузе.
        """
        self.timer_widget.set_paused()
        self.timer_pause_resume_button.setText("Продолжить таймер")

    def _on_timer_stopped(self) -> None:
        """
        Update timer buttons when timer is stopped.
        Обновить кнопки таймера при остановке.
        """
        self.timer_widget.set_stopped()
        self.timer_pause_resume_button.setText("Пауза таймера")

    def _add_manual_points(self) -> None:
        """
        Add manual points to selected team.
        Начислить вручную очки выбранной команде.
        """
        team_id = self.manual_score_team_combo.currentData()
        points = self.manual_score_spin.value()
        self.controller.add_manual_points(team_id=team_id, points=points)

    def _remove_manual_points(self) -> None:
        """
        Remove manual points from selected team.
        Списать вручную очки у выбранной команды.
        """
        team_id = self.manual_score_team_combo.currentData()
        points = self.manual_score_spin.value()
        self.controller.remove_manual_points(team_id=team_id, points=points)

    def _toggle_settings_window(self) -> None:
        """
        Open or close settings window in a single instance.
        Открыть или закрыть окно настроек в единственном экземпляре.
        """
        if self.settings_window is None:
            self.settings_window = GameSettingsWindow(controller=self.controller)
            self.settings_window.visibility_changed.connect(self._update_settings_button_state)

        if self.settings_window.isVisible():
            self.settings_window.close()
        else:
            self.settings_window.refresh_all()
            self.settings_window.show()
            self.settings_window.raise_()
            self.settings_window.activateWindow()

    def _toggle_display_window(self) -> None:
        """
        Show or hide bound display window.
        Показать или скрыть привязанное игровое окно.
        """
        display_window = self.controller.display_window
        if display_window is None:
            self.status_label.setText("Игровое окно не привязано к контроллеру.")
            return

        if not hasattr(display_window, "_admin_visibility_connected"):
            display_window.visibility_changed.connect(self._update_display_button_state)
            display_window._admin_visibility_connected = True

        if display_window.isVisible():
            display_window.close()
        else:
            display_window.show()
            display_window.raise_()
            display_window.activateWindow()

    def _update_settings_button_state(self, is_visible: bool) -> None:
        """
        Reflect settings window visibility on button text.
        Отразить видимость окна настроек в тексте кнопки.
        """
        if is_visible:
            self.settings_button.setText("Закрыть настройки")
        else:
            self.settings_button.setText("Настройки игры")

    def _update_display_button_state(self, is_visible: bool) -> None:
        """
        Reflect display window visibility on button text.
        Отразить видимость игрового окна в тексте кнопки.
        """
        if is_visible:
            self.display_window_button.setText("Скрыть игровое окно")
        else:
            self.display_window_button.setText("Показать игровое окно")

    def _refresh_team_combo_items(self) -> None:
        """
        Refresh manual score teams combo preserving selection.
        Обновить комбобокс команд для ручного счета с сохранением выбора.
        """
        current_team_id = self.manual_score_team_combo.currentData()

        self.manual_score_team_combo.blockSignals(True)
        self.manual_score_team_combo.clear()
        for team in self.controller.get_all_teams():
            self.manual_score_team_combo.addItem(team.name, team.id)

        self._restore_combo_selection(self.manual_score_team_combo, current_team_id)
        self.manual_score_team_combo.blockSignals(False)

    def _refresh_round_combo_items(self) -> None:
        """
        Refresh rounds combo preserving selection.
        Обновить комбобокс раундов с сохранением выбора.
        """
        current_round_id = self.round_combo.currentData()

        self.round_combo.blockSignals(True)
        self.round_combo.clear()
        for round_item in self.controller.get_all_rounds():
            self.round_combo.addItem(round_item.name, round_item.id)

        self._restore_combo_selection(self.round_combo, current_round_id)
        self.round_combo.blockSignals(False)

    @staticmethod
    def _restore_combo_selection(combo: QComboBox, target_data) -> None:
        """
        Restore combo selection by data value.
        Восстановить выбор комбобокса по data-значению.
        """
        if combo.count() <= 0:
            return

        if target_data is None:
            combo.setCurrentIndex(0)
            return

        for index in range(combo.count()):
            if combo.itemData(index) == target_data:
                combo.setCurrentIndex(index)
                return

        combo.setCurrentIndex(0)