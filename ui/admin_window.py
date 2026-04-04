from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from models.question import Question
from models.team import Team
from ui.question_editor_dialog import QuestionEditorDialog
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

        self.setWindowTitle("Fortune Game - Admin")
        self.resize(1320, 900)

        self.round_combo = QComboBox()
        for round_item in self.controller.game.rounds:
            self.round_combo.addItem(round_item.name, round_item.id)

        self.select_round_button = QPushButton("Применить раунд")
        self.spin_button = QPushButton("Крутить колесо")
        self.repeat_button = QPushButton("Повторить вопрос")
        self.show_answer_button = QPushButton("Показать ответ")
        self.correct_button = QPushButton("Верный ответ")
        self.wrong_button = QPushButton("Неверный ответ")
        self.timer_start_button = QPushButton("Старт таймера")
        self.timer_pause_button = QPushButton("Пауза таймера")
        self.timer_stop_button = QPushButton("Стоп таймера")

        self.current_team_value = QLabel("Нет активной команды")
        self.next_team_value = QLabel("Нет следующей команды")
        self.round_progress_value = QLabel("Раунд не выбран")

        self.question_filter_round_combo = QComboBox()
        self.question_filter_round_combo.addItem("Все раунды", None)
        for round_item in self.controller.game.rounds:
            self.question_filter_round_combo.addItem(round_item.name, round_item.id)

        self.question_select_combo = QComboBox()
        self.question_used_checkbox = QCheckBox("Вопрос закрыт (used=True)")

        self.refresh_questions_button = QPushButton("Обновить список")
        self.save_question_state_button = QPushButton("Сохранить статус")
        self.reset_current_question_button = QPushButton("Сбросить текущий")
        self.reset_round_button = QPushButton("Сбросить раунд")
        self.reset_all_button = QPushButton("Сбросить все")
        self.add_question_button = QPushButton("Добавить вопрос")

        self.wheel = WheelWidget()
        self.timer_widget = TimerWidget()
        self.scoreboard = ScoreboardWidget()

        self.question_text = QTextEdit()
        self.question_text.setReadOnly(True)

        self.answer_text = QTextEdit()
        self.answer_text.setReadOnly(True)

        self.status_label = QLabel("Готово")
        self.status_label.setAlignment(Qt.AlignCenter)

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
        self.controller.timer_paused.connect(self.timer_widget.set_paused)
        self.controller.timer_started.connect(self.timer_widget.set_running)
        self.controller.timer_stopped.connect(self.timer_widget.set_stopped)
        self.controller.questions_changed.connect(self.refresh_question_list)
        self.controller.active_team_changed.connect(self.current_team_value.setText)
        self.controller.next_team_changed.connect(self.next_team_value.setText)
        self.controller.round_progress_changed.connect(self.round_progress_value.setText)

        self.scoreboard.update_scores(self.controller.game.teams)
        self.refresh_question_list()
        self.current_team_value.setText(self.controller.get_active_team_name())
        self.next_team_value.setText(self.controller.get_next_team_name())

    def _build_layout(self) -> None:
        """
        Build widget layout.
        Построить компоновку виджетов.
        """
        top_controls = QGridLayout()
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

        button_row = QHBoxLayout()
        button_row.addWidget(self.repeat_button)
        button_row.addWidget(self.show_answer_button)
        button_row.addWidget(self.correct_button)
        button_row.addWidget(self.wrong_button)

        timer_row = QHBoxLayout()
        timer_row.addWidget(self.timer_start_button)
        timer_row.addWidget(self.timer_pause_button)
        timer_row.addWidget(self.timer_stop_button)

        questions_manage_grid = QGridLayout()
        questions_manage_grid.addWidget(QLabel("Фильтр по раунду:"), 0, 0)
        questions_manage_grid.addWidget(self.question_filter_round_combo, 0, 1)
        questions_manage_grid.addWidget(self.refresh_questions_button, 0, 2)

        questions_manage_grid.addWidget(QLabel("Вопрос:"), 1, 0)
        questions_manage_grid.addWidget(self.question_select_combo, 1, 1, 1, 2)

        questions_manage_grid.addWidget(self.question_used_checkbox, 2, 0, 1, 3)

        questions_manage_grid.addWidget(self.save_question_state_button, 3, 0)
        questions_manage_grid.addWidget(self.reset_current_question_button, 3, 1)
        questions_manage_grid.addWidget(self.reset_round_button, 3, 2)

        questions_manage_grid.addWidget(self.reset_all_button, 4, 0)
        questions_manage_grid.addWidget(self.add_question_button, 4, 1, 1, 2)

        left_layout = QVBoxLayout()
        left_layout.addLayout(top_controls)
        left_layout.addWidget(self.wheel, 4)
        left_layout.addLayout(button_row)
        left_layout.addLayout(timer_row)
        left_layout.addWidget(self.timer_widget)
        left_layout.addWidget(QLabel("Управление вопросами:"))
        left_layout.addLayout(questions_manage_grid)
        left_layout.addWidget(QLabel("Текущий вопрос:"))
        left_layout.addWidget(self.question_text, 2)
        left_layout.addWidget(QLabel("Ответ:"))
        left_layout.addWidget(self.answer_text, 1)
        left_layout.addWidget(self.status_label)

        main_layout = QHBoxLayout()
        main_layout.addLayout(left_layout, 4)
        main_layout.addWidget(self.scoreboard, 1)

        self.setLayout(main_layout)

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
        self.timer_start_button.clicked.connect(self.controller.start_timer)
        self.timer_pause_button.clicked.connect(self.controller.pause_timer)
        self.timer_stop_button.clicked.connect(self.controller.stop_timer)

        self.refresh_questions_button.clicked.connect(self.refresh_question_list)
        self.question_filter_round_combo.currentIndexChanged.connect(self.refresh_question_list)
        self.question_select_combo.currentIndexChanged.connect(self._sync_selected_question_state)
        self.save_question_state_button.clicked.connect(self._save_question_used_state)
        self.reset_current_question_button.clicked.connect(self._reset_current_question)
        self.reset_round_button.clicked.connect(self._reset_round_questions)
        self.reset_all_button.clicked.connect(self.controller.reset_all_questions)
        self.add_question_button.clicked.connect(self._open_add_question_dialog)

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

    def refresh_question_list(self) -> None:
        """
        Rebuild question selection list.
        Пересобрать список выбора вопросов.
        """
        current_id = self.question_select_combo.currentData()
        round_id = self.question_filter_round_combo.currentData()

        self.question_select_combo.blockSignals(True)
        self.question_select_combo.clear()

        questions = self.controller.get_questions_for_round(round_id)

        for question in questions:
            used_mark = "закрыт" if question.used else "открыт"
            short_text = question.text[:60].replace("\n", " ")
            self.question_select_combo.addItem(
                f"#{question.id} [{used_mark}] {short_text}",
                question.id,
            )

        if questions:
            target_index = 0
            if current_id is not None:
                for index in range(self.question_select_combo.count()):
                    if self.question_select_combo.itemData(index) == current_id:
                        target_index = index
                        break
            self.question_select_combo.setCurrentIndex(target_index)
        else:
            self.question_text.clear()
            self.answer_text.clear()
            self.question_used_checkbox.setChecked(False)

        self.question_select_combo.blockSignals(False)
        self._sync_selected_question_state()

    def _sync_selected_question_state(self) -> None:
        """
        Sync checkbox state with selected question.
        Синхронизировать чекбокс со статусом выбранного вопроса.
        """
        question_id = self.question_select_combo.currentData()
        if question_id is None:
            self.question_used_checkbox.setChecked(False)
            return

        question = self.controller.game.question_service.get_question_by_id(question_id)
        if question is None:
            self.question_used_checkbox.setChecked(False)
            return

        self.question_used_checkbox.setChecked(question.used)

    def _save_question_used_state(self) -> None:
        """
        Save used state for selected question.
        Сохранить состояние used для выбранного вопроса.
        """
        question_id = self.question_select_combo.currentData()
        if question_id is None:
            self.status_label.setText("Вопрос не выбран.")
            return

        self.controller.set_question_used(
            question_id=question_id,
            used=self.question_used_checkbox.isChecked(),
        )

    def _reset_current_question(self) -> None:
        """
        Reset currently selected question.
        Сбросить текущий выбранный вопрос.
        """
        question_id = self.question_select_combo.currentData()
        if question_id is None:
            self.status_label.setText("Вопрос не выбран.")
            return

        self.controller.reset_current_question(question_id)

    def _reset_round_questions(self) -> None:
        """
        Reset all questions in selected filter round.
        Сбросить все вопросы выбранного в фильтре раунда.
        """
        round_id = self.question_filter_round_combo.currentData()
        if round_id is None:
            self.status_label.setText("Для сброса раунда выбери конкретный раунд в фильтре.")
            return

        self.controller.reset_round_questions(round_id)

    def _open_add_question_dialog(self) -> None:
        """
        Open dialog for adding a new question.
        Открыть диалог добавления нового вопроса.
        """
        dialog = QuestionEditorDialog(
            rounds=self.controller.game.rounds,
            parent=self,
        )

        if dialog.exec():
            payload = dialog.get_payload()
            self.controller.add_question(payload)