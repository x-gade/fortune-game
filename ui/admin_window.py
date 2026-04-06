from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QSpinBox,
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
        self.video_pause_resume_button = QPushButton("Пауза видео")
        self.video_pause_resume_button.hide()

        self.timer_start_button = QPushButton("Старт таймера")
        self.timer_pause_resume_button = QPushButton("Пауза таймера")
        self.timer_stop_button = QPushButton("Стоп таймера")

        self.current_team_value = QLabel("Нет активной команды")
        self.next_team_value = QLabel("Нет следующей команды")
        self.round_progress_value = QLabel("Раунд не выбран")

        self.manual_score_team_combo = QComboBox()
        for team in self.controller.game.teams:
            self.manual_score_team_combo.addItem(team.name, team.id)

        self.manual_score_spin = QSpinBox()
        self.manual_score_spin.setRange(1, 100000)
        self.manual_score_spin.setValue(100)

        self.manual_add_points_button = QPushButton("Начислить очки")
        self.manual_remove_points_button = QPushButton("Списать очки")

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
        self.edit_question_button = QPushButton("Изменить вопрос")
        self.delete_question_button = QPushButton("Удалить вопрос")

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
        self.controller.timer_paused.connect(self._on_timer_paused)
        self.controller.timer_started.connect(self._on_timer_started)
        self.controller.timer_stopped.connect(self._on_timer_stopped)
        self.controller.questions_changed.connect(self.refresh_question_list)
        self.controller.active_team_changed.connect(self.current_team_value.setText)
        self.controller.next_team_changed.connect(self.next_team_value.setText)
        self.controller.round_progress_changed.connect(self.round_progress_value.setText)
        self.controller.video_state_changed.connect(self._update_video_button_state)

        self.scoreboard.update_scores(self.controller.game.teams)
        self.refresh_question_list()
        self.current_team_value.setText(self.controller.get_active_team_name())
        self.next_team_value.setText(self.controller.get_next_team_name())
        self._update_video_button_state()
        self._on_timer_stopped()

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

        video_row = QHBoxLayout()
        video_row.addWidget(self.video_pause_resume_button, 1)

        timer_row = QHBoxLayout()
        timer_row.addWidget(self.timer_start_button)
        timer_row.addWidget(self.timer_pause_resume_button)
        timer_row.addWidget(self.timer_stop_button)

        manual_score_grid = QGridLayout()
        manual_score_grid.addWidget(QLabel("Ручная корректировка счета:"), 0, 0, 1, 3)
        manual_score_grid.addWidget(QLabel("Команда:"), 1, 0)
        manual_score_grid.addWidget(self.manual_score_team_combo, 1, 1, 1, 2)

        manual_score_grid.addWidget(QLabel("Очки:"), 2, 0)
        manual_score_grid.addWidget(self.manual_score_spin, 2, 1, 1, 2)

        manual_score_grid.addWidget(self.manual_add_points_button, 3, 1)
        manual_score_grid.addWidget(self.manual_remove_points_button, 3, 2)

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

        questions_manage_grid.addWidget(self.edit_question_button, 4, 0)
        questions_manage_grid.addWidget(self.delete_question_button, 4, 1)
        questions_manage_grid.addWidget(self.add_question_button, 4, 2)

        questions_manage_grid.addWidget(self.reset_all_button, 5, 0, 1, 3)

        left_layout = QVBoxLayout()
        left_layout.addLayout(top_controls)
        left_layout.addWidget(self.wheel, 4)
        left_layout.addLayout(button_row)
        left_layout.addLayout(video_row)
        left_layout.addLayout(timer_row)
        left_layout.addWidget(self.timer_widget)
        left_layout.addLayout(manual_score_grid)
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
        self.video_pause_resume_button.clicked.connect(self.controller.toggle_video_pause_resume)

        self.timer_start_button.clicked.connect(self.controller.start_timer)
        self.timer_pause_resume_button.clicked.connect(self._toggle_timer_pause_resume)
        self.timer_stop_button.clicked.connect(self.controller.stop_timer)

        self.manual_add_points_button.clicked.connect(self._add_manual_points)
        self.manual_remove_points_button.clicked.connect(self._remove_manual_points)

        self.refresh_questions_button.clicked.connect(self.refresh_question_list)
        self.question_filter_round_combo.currentIndexChanged.connect(self.refresh_question_list)
        self.question_select_combo.currentIndexChanged.connect(self._on_selected_question_changed)
        self.save_question_state_button.clicked.connect(self._save_question_used_state)
        self.reset_current_question_button.clicked.connect(self._reset_current_question)
        self.reset_round_button.clicked.connect(self._reset_round_questions)
        self.reset_all_button.clicked.connect(self.controller.reset_all_questions)
        self.add_question_button.clicked.connect(self._open_add_question_dialog)
        self.edit_question_button.clicked.connect(self._open_edit_question_dialog)
        self.delete_question_button.clicked.connect(self._delete_selected_question)

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
            media_mark = " [VIDEO]" if question.media_type == "video" else ""
            short_text = question.text[:60].replace("\n", " ")
            self.question_select_combo.addItem(
                f"#{question.id} [{used_mark}] {short_text}{media_mark}",
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
        self._sync_selected_question_preview()

    def _on_selected_question_changed(self) -> None:
        """
        Handle question selection change.
        Обработать смену выбранного вопроса.
        """
        self._sync_selected_question_state()
        self._sync_selected_question_preview()

    def _sync_selected_question_state(self) -> None:
        """
        Sync checkbox state with selected question.
        Синхронизировать чекбокс со статусом выбранного вопроса.
        """
        question_id = self.question_select_combo.currentData()
        if question_id is None:
            self.question_used_checkbox.setChecked(False)
            return

        question = self.controller.get_question_by_id(question_id)
        if question is None:
            self.question_used_checkbox.setChecked(False)
            return

        self.question_used_checkbox.setChecked(question.used)

    def _sync_selected_question_preview(self) -> None:
        """
        Sync question and answer preview with selected question.
        Синхронизировать предпросмотр вопроса и ответа с выбранным вопросом.
        """
        question_id = self.question_select_combo.currentData()
        if question_id is None:
            self.question_text.clear()
            self.answer_text.clear()
            return

        question = self.controller.get_question_by_id(question_id)
        if question is None:
            self.question_text.clear()
            self.answer_text.clear()
            return

        self.question_text.setPlainText(question.text)
        self.answer_text.setPlainText(question.answer or "")

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

    def _open_edit_question_dialog(self) -> None:
        """
        Open dialog for editing selected question.
        Открыть диалог редактирования выбранного вопроса.
        """
        question_id = self.question_select_combo.currentData()
        if question_id is None:
            self.status_label.setText("Вопрос не выбран.")
            return

        question = self.controller.get_question_by_id(question_id)
        if question is None:
            self.status_label.setText("Выбранный вопрос не найден.")
            return

        dialog = QuestionEditorDialog(
            rounds=self.controller.game.rounds,
            question=question,
            parent=self,
        )

        if dialog.exec():
            payload = dialog.get_payload()
            self.controller.update_question(question_id, payload)

    def _delete_selected_question(self) -> None:
        """
        Delete selected question after confirmation.
        Удалить выбранный вопрос после подтверждения.
        """
        question_id = self.question_select_combo.currentData()
        if question_id is None:
            self.status_label.setText("Вопрос не выбран.")
            return

        question = self.controller.get_question_by_id(question_id)
        if question is None:
            self.status_label.setText("Выбранный вопрос не найден.")
            return

        short_text = question.text[:120].replace("\n", " ")
        reply = QMessageBox.question(
            self,
            "Подтверждение удаления",
            (
                f"Удалить вопрос #{question.id}?\n\n"
                f"{short_text}\n\n"
                "Это действие нельзя отменить."
            ),
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )

        if reply != QMessageBox.Yes:
            return

        self.controller.delete_question(question_id)