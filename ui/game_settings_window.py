from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QCloseEvent, QHideEvent, QShowEvent
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QGridLayout,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QListWidget,
    QMessageBox,
    QPushButton,
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from ui.question_editor_dialog import QuestionEditorDialog


class GameSettingsWindow(QWidget):
    """
    Window for editing game entities.
    Окно редактирования игровых сущностей.
    """

    visibility_changed = Signal(bool)

    def __init__(self, controller, parent=None) -> None:
        """
        Initialize settings window.
        Инициализация окна настроек.
        """
        super().__init__(parent)
        self.controller = controller

        self.setWindowTitle("Fortune Game - Настройки игры")
        self.resize(1100, 800)

        self.tabs = QTabWidget()

        self._build_questions_tab()
        self._build_teams_tab()
        self._build_rounds_tab()

        layout = QVBoxLayout()
        layout.addWidget(self.tabs)
        self.setLayout(layout)

        self._apply_local_styles()
        self._connect_events()
        self.refresh_all()

    def _apply_local_styles(self) -> None:
        """
        Apply local styles for settings window controls.
        Применить локальные стили для элементов окна настроек.
        """
        self.setStyleSheet(
            """
            QTabWidget::pane {
                border: 1px solid #7f7f7f;
                background-color: #3a3a3a;
                margin-top: 2px;
            }

            QTabBar::tab {
                background-color: #4a4a4a;
                color: #f0f0f0;
                border: 1px solid #7f7f7f;
                padding: 8px 18px;
                min-width: 120px;
                font-size: 13px;
            }

            QTabBar::tab:selected {
                background-color: #585858;
                color: #ffffff;
                font-weight: bold;
            }

            QTabBar::tab:hover {
                background-color: #626262;
                color: #ffffff;
            }

            QListWidget {
                background-color: #2f2f2f;
                color: #f5f5f5;
                border: 1px solid #666666;
            }

            QListWidget::item:selected {
                background-color: #3f566b;
                color: #ffffff;
            }

            QPushButton#addQuestionButton,
            QPushButton#addTeamButton,
            QPushButton#addRoundButton {
                border: 2px solid #4f7a67;
                color: #ffffff;
                background-color: #505050;
            }

            QPushButton#addQuestionButton:hover,
            QPushButton#addTeamButton:hover,
            QPushButton#addRoundButton:hover {
                border: 2px solid #6a9a84;
                background-color: #5a5a5a;
            }

            QPushButton#addQuestionButton:pressed,
            QPushButton#addTeamButton:pressed,
            QPushButton#addRoundButton:pressed {
                border: 2px solid #3f6555;
                background-color: #454545;
            }

            QPushButton#editQuestionButton,
            QPushButton#editTeamButton,
            QPushButton#editRoundButton {
                border: 2px solid #9a7448;
                color: #ffffff;
                background-color: #505050;
            }

            QPushButton#editQuestionButton:hover,
            QPushButton#editTeamButton:hover,
            QPushButton#editRoundButton:hover {
                border: 2px solid #b38857;
                background-color: #5a5a5a;
            }

            QPushButton#editQuestionButton:pressed,
            QPushButton#editTeamButton:pressed,
            QPushButton#editRoundButton:pressed {
                border: 2px solid #7f5f3d;
                background-color: #454545;
            }

            QPushButton#deleteQuestionButton,
            QPushButton#deleteTeamButton,
            QPushButton#deleteRoundButton {
                border: 2px solid #8a4f56;
                color: #ffffff;
                background-color: #505050;
            }

            QPushButton#deleteQuestionButton:hover,
            QPushButton#deleteTeamButton:hover,
            QPushButton#deleteRoundButton:hover {
                border: 2px solid #a8656d;
                background-color: #5a5a5a;
            }

            QPushButton#deleteQuestionButton:pressed,
            QPushButton#deleteTeamButton:pressed,
            QPushButton#deleteRoundButton:pressed {
                border: 2px solid #6f4046;
                background-color: #454545;
            }
            """
        )

    def _build_questions_tab(self) -> None:
        """
        Build questions tab.
        Построить вкладку вопросов.
        """
        self.questions_tab = QWidget()

        self.question_filter_round_combo = QComboBox()
        self.question_select_combo = QComboBox()
        self.question_used_checkbox = QCheckBox("Вопрос закрыт (used=True)")

        self.refresh_questions_button = QPushButton("Обновить список")
        self.save_question_state_button = QPushButton("Сохранить статус вопроса")
        self.reset_current_question_button = QPushButton("Сбросить текущий статус вопроса")
        self.reset_round_button = QPushButton("Сбросить раунд")
        self.reset_all_questions_button = QPushButton("Сбросить все вопросы")
        self.add_question_button = QPushButton("Добавить вопрос")
        self.edit_question_button = QPushButton("Изменить вопрос")
        self.delete_question_button = QPushButton("Удалить вопрос")

        self.add_question_button.setObjectName("addQuestionButton")
        self.edit_question_button.setObjectName("editQuestionButton")
        self.delete_question_button.setObjectName("deleteQuestionButton")

        self.question_text = QTextEdit()
        self.question_text.setReadOnly(True)
        self.answer_text = QTextEdit()
        self.answer_text.setReadOnly(True)

        questions_manage_grid = QGridLayout()
        questions_manage_grid.setHorizontalSpacing(10)
        questions_manage_grid.setVerticalSpacing(8)

        questions_manage_grid.addWidget(QLabel("Фильтр по раунду:"), 0, 0)
        questions_manage_grid.addWidget(self.question_filter_round_combo, 0, 1)
        questions_manage_grid.addWidget(self.refresh_questions_button, 0, 2)

        questions_manage_grid.addWidget(QLabel("Вопрос:"), 1, 0)
        questions_manage_grid.addWidget(self.question_select_combo, 1, 1, 1, 2)

        questions_manage_grid.addWidget(self.question_used_checkbox, 2, 0, 1, 3)

        questions_manage_grid.addWidget(self.save_question_state_button, 3, 0)
        questions_manage_grid.addWidget(self.reset_current_question_button, 3, 1)
        questions_manage_grid.addWidget(self.reset_round_button, 3, 2)

        questions_manage_grid.addWidget(self.add_question_button, 4, 0)
        questions_manage_grid.addWidget(self.edit_question_button, 4, 1)
        questions_manage_grid.addWidget(self.delete_question_button, 4, 2)

        questions_manage_grid.addWidget(self.reset_all_questions_button, 5, 0, 1, 3)

        layout = QVBoxLayout()
        layout.addLayout(questions_manage_grid)
        layout.addWidget(QLabel("Текущий вопрос:"))
        layout.addWidget(self.question_text, 3)
        layout.addWidget(QLabel("Ответ:"))
        layout.addWidget(self.answer_text, 2)

        self.questions_tab.setLayout(layout)
        self.tabs.addTab(self.questions_tab, "Вопросы")

    def _build_teams_tab(self) -> None:
        """
        Build teams tab.
        Построить вкладку команд.
        """
        self.teams_tab = QWidget()

        self.teams_list = QListWidget()
        self.add_team_button = QPushButton("Добавить команду")
        self.edit_team_button = QPushButton("Изменить команду")
        self.delete_team_button = QPushButton("Удалить команду")
        self.reset_all_scores_button = QPushButton("Сбросить все очки")

        self.add_team_button.setObjectName("addTeamButton")
        self.edit_team_button.setObjectName("editTeamButton")
        self.delete_team_button.setObjectName("deleteTeamButton")

        buttons_top = QHBoxLayout()
        buttons_top.addWidget(self.add_team_button)
        buttons_top.addWidget(self.edit_team_button)
        buttons_top.addWidget(self.delete_team_button)

        buttons_bottom = QHBoxLayout()
        buttons_bottom.addWidget(self.reset_all_scores_button)

        layout = QVBoxLayout()
        layout.addWidget(QLabel("Команды игры:"))
        layout.addWidget(self.teams_list, 1)
        layout.addLayout(buttons_top)
        layout.addLayout(buttons_bottom)

        self.teams_tab.setLayout(layout)
        self.tabs.addTab(self.teams_tab, "Команды")

    def _build_rounds_tab(self) -> None:
        """
        Build rounds tab.
        Построить вкладку раундов.
        """
        self.rounds_tab = QWidget()

        self.rounds_list = QListWidget()
        self.add_round_button = QPushButton("Добавить раунд")
        self.edit_round_button = QPushButton("Изменить раунд")
        self.delete_round_button = QPushButton("Удалить раунд")

        self.add_round_button.setObjectName("addRoundButton")
        self.edit_round_button.setObjectName("editRoundButton")
        self.delete_round_button.setObjectName("deleteRoundButton")

        buttons = QHBoxLayout()
        buttons.addWidget(self.add_round_button)
        buttons.addWidget(self.edit_round_button)
        buttons.addWidget(self.delete_round_button)

        layout = QVBoxLayout()
        layout.addWidget(QLabel("Раунды игры:"))
        layout.addWidget(self.rounds_list, 1)
        layout.addLayout(buttons)

        self.rounds_tab.setLayout(layout)
        self.tabs.addTab(self.rounds_tab, "Раунды")

    def _connect_events(self) -> None:
        """
        Connect widget actions and controller signals.
        Подключить действия виджетов и сигналы контроллера.
        """
        self.refresh_questions_button.clicked.connect(self.refresh_question_list)
        self.question_filter_round_combo.currentIndexChanged.connect(self.refresh_question_list)
        self.question_select_combo.currentIndexChanged.connect(self._on_selected_question_changed)
        self.save_question_state_button.clicked.connect(self._save_question_used_state)
        self.reset_current_question_button.clicked.connect(self._reset_current_question)
        self.reset_round_button.clicked.connect(self._reset_round_questions)
        self.reset_all_questions_button.clicked.connect(self._reset_all_questions)
        self.add_question_button.clicked.connect(self._open_add_question_dialog)
        self.edit_question_button.clicked.connect(self._open_edit_question_dialog)
        self.delete_question_button.clicked.connect(self._delete_selected_question)

        self.add_team_button.clicked.connect(self._add_team)
        self.edit_team_button.clicked.connect(self._edit_team)
        self.delete_team_button.clicked.connect(self._delete_team)
        self.reset_all_scores_button.clicked.connect(self._reset_all_scores)

        self.add_round_button.clicked.connect(self._add_round)
        self.edit_round_button.clicked.connect(self._edit_round)
        self.delete_round_button.clicked.connect(self._delete_round)

        self.controller.questions_changed.connect(self.refresh_question_list)
        self.controller.teams_changed.connect(self.refresh_team_list)
        self.controller.rounds_changed.connect(self.refresh_round_list)
        self.controller.rounds_changed.connect(self._refresh_question_filter_rounds)
        self.controller.scoreboard_changed.connect(lambda _: self.refresh_team_list())

    def refresh_all(self) -> None:
        """
        Refresh all tabs data.
        Обновить данные всех вкладок.
        """
        self.refresh_team_list()
        self.refresh_round_list()
        self._refresh_question_filter_rounds()
        self.refresh_question_list()

    def refresh_team_list(self) -> None:
        """
        Refresh teams list.
        Обновить список команд.
        """
        current_team_id = self._get_selected_team_id()

        self.teams_list.blockSignals(True)
        self.teams_list.clear()

        for team in self.controller.get_all_teams():
            self.teams_list.addItem(f"#{team.id} {team.name} | очки: {team.score}")
            self.teams_list.item(self.teams_list.count() - 1).setData(Qt.UserRole, team.id)

        self.teams_list.blockSignals(False)
        self._restore_list_selection(self.teams_list, current_team_id)

    def refresh_round_list(self) -> None:
        """
        Refresh rounds list.
        Обновить список раундов.
        """
        current_round_id = self._get_selected_round_id()

        self.rounds_list.blockSignals(True)
        self.rounds_list.clear()

        for round_item in self.controller.get_all_rounds():
            total_count = len(self.controller.get_questions_for_round(round_item.id))
            self.rounds_list.addItem(
                f"#{round_item.id} {round_item.name} | вопросов: {total_count}"
            )
            self.rounds_list.item(self.rounds_list.count() - 1).setData(Qt.UserRole, round_item.id)

        self.rounds_list.blockSignals(False)
        self._restore_list_selection(self.rounds_list, current_round_id)

    def _refresh_question_filter_rounds(self) -> None:
        """
        Refresh round filter combo for questions tab.
        Обновить комбобокс фильтра раундов для вкладки вопросов.
        """
        current_round_id = self.question_filter_round_combo.currentData()

        self.question_filter_round_combo.blockSignals(True)
        self.question_filter_round_combo.clear()
        self.question_filter_round_combo.addItem("Все раунды", None)

        for round_item in self.controller.get_all_rounds():
            self.question_filter_round_combo.addItem(round_item.name, round_item.id)

        self._set_combo_data(self.question_filter_round_combo, current_round_id)
        self.question_filter_round_combo.blockSignals(False)

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
            QMessageBox.warning(self, "Внимание", "Вопрос не выбран.")
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
            QMessageBox.warning(self, "Внимание", "Вопрос не выбран.")
            return

        self.controller.reset_current_question(question_id)

    def _reset_round_questions(self) -> None:
        """
        Reset all questions in selected filter round.
        Сбросить все вопросы выбранного в фильтре раунда.
        """
        round_id = self.question_filter_round_combo.currentData()
        if round_id is None:
            QMessageBox.warning(
                self,
                "Внимание",
                "Для сброса раунда выбери конкретный раунд в фильтре.",
            )
            return

        self.controller.reset_round_questions(round_id)

    def _reset_all_questions(self) -> None:
        """
        Reset all questions in project.
        Сбросить все вопросы проекта.
        """
        result = QMessageBox.question(
            self,
            "Подтверждение",
            "Сбросить все вопросы проекта в состояние открытых?",
        )
        if result == QMessageBox.StandardButton.Yes:
            self.controller.reset_all_questions()

    def _reset_all_scores(self) -> None:
        """
        Reset all teams scores after confirmation.
        Сбросить очки всех команд после подтверждения.
        """
        result = QMessageBox.question(
            self,
            "Подтверждение",
            "Сбросить все очки всех команд до нуля?",
        )
        if result == QMessageBox.StandardButton.Yes:
            self.controller.reset_all_scores()

    def _open_add_question_dialog(self) -> None:
        """
        Open dialog for adding a new question.
        Открыть диалог добавления нового вопроса.
        """
        dialog = QuestionEditorDialog(
            rounds=self.controller.get_all_rounds(),
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
            QMessageBox.warning(self, "Внимание", "Вопрос не выбран.")
            return

        question = self.controller.get_question_by_id(question_id)
        if question is None:
            QMessageBox.warning(self, "Внимание", "Выбранный вопрос не найден.")
            return

        dialog = QuestionEditorDialog(
            rounds=self.controller.get_all_rounds(),
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
            QMessageBox.warning(self, "Внимание", "Вопрос не выбран.")
            return

        result = QMessageBox.question(
            self,
            "Подтверждение",
            f"Удалить вопрос #{question_id}?",
        )
        if result != QMessageBox.StandardButton.Yes:
            return

        self.controller.delete_question(question_id)

    def _add_team(self) -> None:
        """
        Request and create new team.
        Запросить и создать новую команду.
        """
        name, accepted = QInputDialog.getText(self, "Новая команда", "Название команды:")
        if not accepted:
            return

        self.controller.add_team(name)

    def _edit_team(self) -> None:
        """
        Request and update selected team.
        Запросить и обновить выбранную команду.
        """
        team_id = self._get_selected_team_id()
        if team_id is None:
            QMessageBox.warning(self, "Внимание", "Команда не выбрана.")
            return

        team = self.controller.get_team_by_id(team_id)
        if team is None:
            QMessageBox.warning(self, "Внимание", "Команда не найдена.")
            return

        name, accepted = QInputDialog.getText(
            self,
            "Изменить команду",
            "Название команды:",
            text=team.name,
        )
        if not accepted:
            return

        self.controller.update_team(team_id, name)

    def _delete_team(self) -> None:
        """
        Delete selected team after confirmation.
        Удалить выбранную команду после подтверждения.
        """
        team_id = self._get_selected_team_id()
        if team_id is None:
            QMessageBox.warning(self, "Внимание", "Команда не выбрана.")
            return

        team = self.controller.get_team_by_id(team_id)
        if team is None:
            QMessageBox.warning(self, "Внимание", "Команда не найдена.")
            return

        result = QMessageBox.question(
            self,
            "Подтверждение",
            f"Удалить команду '{team.name}'?",
        )
        if result != QMessageBox.StandardButton.Yes:
            return

        self.controller.delete_team(team_id)

    def _add_round(self) -> None:
        """
        Request and create new round.
        Запросить и создать новый раунд.
        """
        name, accepted = QInputDialog.getText(self, "Новый раунд", "Название раунда:")
        if not accepted:
            return

        self.controller.add_round(name)

    def _edit_round(self) -> None:
        """
        Request and update selected round.
        Запросить и обновить выбранный раунд.
        """
        round_id = self._get_selected_round_id()
        if round_id is None:
            QMessageBox.warning(self, "Внимание", "Раунд не выбран.")
            return

        round_item = self.controller.get_round_by_id(round_id)
        if round_item is None:
            QMessageBox.warning(self, "Внимание", "Раунд не найден.")
            return

        name, accepted = QInputDialog.getText(
            self,
            "Изменить раунд",
            "Название раунда:",
            text=round_item.name,
        )
        if not accepted:
            return

        self.controller.update_round(round_id, name)

    def _delete_round(self) -> None:
        """
        Delete selected round after confirmation.
        Удалить выбранный раунд после подтверждения.
        """
        round_id = self._get_selected_round_id()
        if round_id is None:
            QMessageBox.warning(self, "Внимание", "Раунд не выбран.")
            return

        round_item = self.controller.get_round_by_id(round_id)
        if round_item is None:
            QMessageBox.warning(self, "Внимание", "Раунд не найден.")
            return

        result = QMessageBox.question(
            self,
            "Подтверждение",
            f"Удалить раунд '{round_item.name}'?",
        )
        if result != QMessageBox.StandardButton.Yes:
            return

        self.controller.delete_round(round_id)

    def _get_selected_team_id(self) -> int | None:
        """
        Return selected team identifier.
        Вернуть идентификатор выбранной команды.
        """
        item = self.teams_list.currentItem()
        if item is None:
            return None
        return item.data(Qt.UserRole)

    def _get_selected_round_id(self) -> int | None:
        """
        Return selected round identifier.
        Вернуть идентификатор выбранного раунда.
        """
        item = self.rounds_list.currentItem()
        if item is None:
            return None
        return item.data(Qt.UserRole)

    @staticmethod
    def _restore_list_selection(list_widget, target_id: int | None) -> None:
        """
        Restore list selection by stored identifier.
        Восстановить выбор в списке по сохраненному идентификатору.
        """
        if list_widget.count() <= 0:
            return

        if target_id is None:
            list_widget.setCurrentRow(0)
            return

        for index in range(list_widget.count()):
            item = list_widget.item(index)
            if item.data(Qt.UserRole) == target_id:
                list_widget.setCurrentRow(index)
                return

        list_widget.setCurrentRow(0)

    @staticmethod
    def _set_combo_data(combo: QComboBox, target_data) -> None:
        """
        Set combo current item by data value.
        Установить текущий элемент комбобокса по data-значению.
        """
        for index in range(combo.count()):
            if combo.itemData(index) == target_data:
                combo.setCurrentIndex(index)
                return

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
        Handle closing of settings window.
        Обработать закрытие окна настроек.
        """
        super().closeEvent(event)