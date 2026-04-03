from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
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
        self.resize(1100, 780)

        self.round_combo = QComboBox()
        self.team_combo = QComboBox()

        for round_item in self.controller.game.rounds:
            self.round_combo.addItem(round_item.name, round_item.id)

        for team in self.controller.game.teams:
            self.team_combo.addItem(team.name, team.id)

        self.select_round_button = QPushButton("Применить раунд")
        self.spin_button = QPushButton("Крутить колесо")
        self.repeat_button = QPushButton("Повторить вопрос")
        self.show_answer_button = QPushButton("Показать ответ")
        self.correct_button = QPushButton("Верный ответ")
        self.wrong_button = QPushButton("Неверный ответ")
        self.timer_start_button = QPushButton("Старт таймера")
        self.timer_pause_button = QPushButton("Пауза таймера")
        self.timer_stop_button = QPushButton("Стоп таймера")

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

        self.scoreboard.update_scores(self.controller.game.teams)

    def _build_layout(self) -> None:
        """
        Build widget layout.
        Построить компоновку виджетов.
        """
        top_controls = QGridLayout()
        top_controls.addWidget(QLabel("Раунд:"), 0, 0)
        top_controls.addWidget(self.round_combo, 0, 1)
        top_controls.addWidget(self.select_round_button, 0, 2)
        top_controls.addWidget(QLabel("Команда:"), 1, 0)
        top_controls.addWidget(self.team_combo, 1, 1)
        top_controls.addWidget(self.spin_button, 1, 2)

        button_row = QHBoxLayout()
        button_row.addWidget(self.repeat_button)
        button_row.addWidget(self.show_answer_button)
        button_row.addWidget(self.correct_button)
        button_row.addWidget(self.wrong_button)

        timer_row = QHBoxLayout()
        timer_row.addWidget(self.timer_start_button)
        timer_row.addWidget(self.timer_pause_button)
        timer_row.addWidget(self.timer_stop_button)

        left_layout = QVBoxLayout()
        left_layout.addLayout(top_controls)
        left_layout.addWidget(self.wheel, 4)
        left_layout.addLayout(button_row)
        left_layout.addLayout(timer_row)
        left_layout.addWidget(self.timer_widget)
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

    def _select_round(self) -> None:
        """
        Apply selected round.
        Применить выбранный раунд.
        """
        round_id = self.round_combo.currentData()
        self.controller.select_round(round_id)

    def _spin(self) -> None:
        """
        Start spin for selected team.
        Запустить вращение для выбранной команды.
        """
        round_id = self.round_combo.currentData()
        self.controller.select_round(round_id)

        team_id = self.team_combo.currentData()
        self.controller.spin_for_team(team_id)

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