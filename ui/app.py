from PySide6.QtCore import QObject, QTimer, Signal
from PySide6.QtWidgets import QApplication

from models.question import Question
from services.game_service import GameService
from ui.admin_window import AdminWindow
from ui.display_window import DisplayWindow
from utils.helpers import get_next_id


APP_STYLESHEET = """
QWidget {
    background-color: #3a3a3a;
    color: #f0f0f0;
    font-size: 13px;
}

QLabel {
    color: #f0f0f0;
}

QPushButton {
    background-color: #505050;
    color: #ffffff;
    border: 1px solid #707070;
    border-radius: 6px;
    padding: 6px 10px;
}

QPushButton:hover {
    background-color: #5e5e5e;
}

QPushButton:pressed {
    background-color: #444444;
}

QComboBox {
    background-color: #505050;
    color: #ffffff;
    border: 1px solid #707070;
    border-radius: 4px;
    padding: 4px 8px;
}

QComboBox QAbstractItemView {
    background-color: #454545;
    color: #ffffff;
    selection-background-color: #606060;
}

QTextEdit {
    background-color: #2f2f2f;
    color: #f5f5f5;
    border: 1px solid #666666;
}

QScrollBar:vertical,
QScrollBar:horizontal {
    background: #3a3a3a;
}

QToolTip {
    background-color: #505050;
    color: #ffffff;
    border: 1px solid #707070;
}
"""


class GameController(QObject):
    """
    UI game controller for multi-window workflow.
    UI-контроллер игры для работы с несколькими окнами.
    """

    wheel_spin_requested = Signal(list, int)
    question_selected = Signal(object)
    answer_requested = Signal(str)
    scoreboard_changed = Signal(object)
    round_title_changed = Signal(str)
    status_changed = Signal(str)
    timer_updated = Signal(int)
    timer_started = Signal()
    timer_paused = Signal()
    timer_stopped = Signal()
    video_requested = Signal(str)
    questions_changed = Signal()

    def __init__(self, data_path: str) -> None:
        """
        Initialize UI controller and core game services.
        Инициализация UI-контроллера и базовых игровых сервисов.
        """
        super().__init__()

        self.game = GameService(data_path=data_path)

        self.current_question: Question | None = None
        self.current_question_resolved: bool = True
        self.current_team_id: int | None = None
        self.remaining_seconds: int = 0

        self.timer = QTimer(self)
        self.timer.setInterval(1000)
        self.timer.timeout.connect(self._on_timer_tick)

    def clear_active_question_state(self) -> None:
        """
        Clear active runtime state of current question.
        Очистить runtime-состояние активного текущего вопроса.
        """
        self.timer.stop()
        self.current_question = None
        self.current_question_resolved = True
        self.current_team_id = None
        self.remaining_seconds = 0
        self.timer_updated.emit(0)
        self.timer_stopped.emit()

    def select_round(self, round_id: int) -> None:
        """
        Set current round manually from admin window.
        Установить текущий раунд вручную из окна администратора.
        """
        if round_id is None:
            self.status_changed.emit("Раунд не выбран.")
            return

        self.game.state.current_round_id = round_id

        round_name = next(
            (round_item.name for round_item in self.game.rounds if round_item.id == round_id),
            f"Раунд {round_id}",
        )
        self.round_title_changed.emit(round_name)
        self.status_changed.emit(f"Выбран раунд: {round_name}")

    def spin_for_team(self, team_id: int) -> None:
        """
        Select question and start wheel animation for team.
        Выбрать вопрос и запустить анимацию колеса для команды.
        """
        if self.game.state.current_round_id is None:
            self.status_changed.emit("Сначала выбери раунд.")
            return

        if not self.current_question_resolved:
            self.status_changed.emit("Сначала заверши текущий вопрос.")
            return

        available_questions = self.game.question_service.get_available_questions(
            round_id=self.game.state.current_round_id,
            team_id=team_id,
        )

        if not available_questions:
            self.status_changed.emit("Для выбранного раунда нет доступных вопросов.")
            return

        selected_question = self.game.question_service.pick_random_question(
            round_id=self.game.state.current_round_id,
            team_id=team_id,
        )

        if selected_question is None:
            self.status_changed.emit("Не удалось выбрать вопрос.")
            return

        self.current_question = selected_question
        self.current_question_resolved = False
        self.current_team_id = team_id

        self.game.state.current_team_id = team_id
        self.game.state.current_question_id = selected_question.id

        labels = self.game.wheel_service.build_wheel_labels(available_questions)
        target_index = self.game.wheel_service.pick_target_index(
            questions=available_questions,
            target_question_id=selected_question.id,
        )

        self.wheel_spin_requested.emit(labels, target_index)
        self.status_changed.emit("Колесо вращается...")

    def on_public_wheel_finished(self) -> None:
        """
        Reveal selected question after public wheel animation.
        Показать выбранный вопрос после завершения публичной анимации колеса.
        """
        if self.current_question is None:
            return

        self.question_selected.emit(self.current_question)
        self.status_changed.emit("Вопрос показан.")

        if getattr(self.current_question, "media_type", None) == "video":
            media_path = getattr(self.current_question, "media_path", None)
            if media_path:
                self.video_requested.emit(media_path)
                self.status_changed.emit("Запущен видеовопрос.")
            else:
                self.status_changed.emit("У видеовопроса не указан путь к файлу.")

    def on_video_finished(self) -> None:
        """
        Start timer automatically after video playback.
        Автоматически запустить таймер после завершения видео.
        """
        self.status_changed.emit("Видео завершено. Таймер запускается автоматически.")
        self.start_timer()

    def repeat_question(self) -> None:
        """
        Repeat current question text.
        Повторно показать текущий вопрос.
        """
        if self.current_question is None:
            self.status_changed.emit("Нет активного вопроса для повтора.")
            return

        self.question_selected.emit(self.current_question)
        self.status_changed.emit("Вопрос повторен.")

    def show_answer(self) -> None:
        """
        Show answer for current question.
        Показать ответ на текущий вопрос.
        """
        if self.current_question is None:
            self.status_changed.emit("Нет активного вопроса.")
            return

        self.answer_requested.emit(self.current_question.answer)
        self.status_changed.emit("Ответ показан.")

    def start_timer(self) -> None:
        """
        Start or resume timer for current question.
        Запустить или продолжить таймер для текущего вопроса.
        """
        if self.current_question is None:
            self.status_changed.emit("Нет активного вопроса для запуска таймера.")
            return

        if self.remaining_seconds <= 0:
            self.remaining_seconds = self.game.question_service.get_question_timer(self.current_question)
            self.timer_updated.emit(self.remaining_seconds)

        self.timer.start()
        self.timer_started.emit()
        self.status_changed.emit("Таймер запущен.")

    def pause_timer(self) -> None:
        """
        Pause active timer.
        Поставить активный таймер на паузу.
        """
        if self.timer.isActive():
            self.timer.stop()
            self.timer_paused.emit()
            self.status_changed.emit("Таймер поставлен на паузу.")

    def stop_timer(self) -> None:
        """
        Stop timer and reset current countdown value.
        Остановить таймер и сбросить текущее значение отсчета.
        """
        self.timer.stop()

        if self.current_question is not None:
            self.remaining_seconds = self.game.question_service.get_question_timer(self.current_question)
        else:
            self.remaining_seconds = 0

        self.timer_updated.emit(self.remaining_seconds)
        self.timer_stopped.emit()
        self.status_changed.emit("Таймер остановлен.")

    def mark_correct(self) -> None:
        """
        Mark answer as correct and award points.
        Отметить ответ как верный и начислить очки.
        """
        if self.current_question is None or self.current_team_id is None:
            self.status_changed.emit("Нет активного вопроса или команды.")
            return

        if self.current_question_resolved:
            self.status_changed.emit("Этот вопрос уже завершен.")
            return

        self.timer.stop()
        self.game.score_service.add_points(self.current_team_id, self.current_question.points)
        self.game.state.last_result_correct = True
        self._finalize_current_question("Ответ засчитан.")

    def mark_wrong(self) -> None:
        """
        Mark answer as incorrect.
        Отметить ответ как неверный.
        """
        if self.current_question is None:
            self.status_changed.emit("Нет активного вопроса.")
            return

        if self.current_question_resolved:
            self.status_changed.emit("Этот вопрос уже завершен.")
            return

        self.timer.stop()
        self.game.state.last_result_correct = False
        self._finalize_current_question("Ответ не засчитан.")

    def _finalize_current_question(self, status_text: str) -> None:
        """
        Finalize current question and persist updated state.
        Завершить текущий вопрос и сохранить обновленное состояние.
        """
        if self.current_question is None:
            return

        self.game.question_service.mark_used(self.current_question.id)

        self.game.state.history.append(
            (
                f"round={self.game.state.current_round_id}; "
                f"team={self.current_team_id}; "
                f"question={self.current_question.id}; "
                f"media={getattr(self.current_question, 'media_type', None)}; "
                f"correct={self.game.state.last_result_correct}"
            )
        )

        self.game.data_loader.save_all(
            settings=self.game.settings,
            teams=self.game.teams,
            rounds=self.game.rounds,
            questions=self.game.questions,
        )

        self.scoreboard_changed.emit(self.game.teams)
        self.current_question_resolved = True
        self.remaining_seconds = 0
        self.timer_updated.emit(0)
        self.timer_stopped.emit()
        self.status_changed.emit(status_text)
        self.questions_changed.emit()

    def _on_timer_tick(self) -> None:
        """
        Tick timer down by one second.
        Уменьшить таймер на одну секунду.
        """
        self.remaining_seconds -= 1
        self.timer_updated.emit(max(self.remaining_seconds, 0))

        if self.remaining_seconds <= 0:
            self.timer.stop()
            self.timer_stopped.emit()
            self.status_changed.emit("Время вышло.")

    def get_questions_for_round(self, round_id: int | None = None) -> list[Question]:
        """
        Return questions for admin list.
        Вернуть вопросы для списка администратора.
        """
        return self.game.question_service.get_questions_by_round(round_id)

    def save_questions_state(self) -> None:
        """
        Persist current questions and related state.
        Сохранить текущее состояние вопросов и связанных данных.
        """
        self.game.data_loader.save_all(
            settings=self.game.settings,
            teams=self.game.teams,
            rounds=self.game.rounds,
            questions=self.game.questions,
        )
        self.questions_changed.emit()

    def reset_current_question(self, question_id: int) -> None:
        """
        Reset selected question to unused state.
        Сбросить выбранный вопрос в состояние неиспользованного.
        """
        self.game.question_service.reset_question(question_id)

        if self.current_question is not None and self.current_question.id == question_id:
            self.clear_active_question_state()

        self.save_questions_state()
        self.status_changed.emit(f"Вопрос #{question_id} сброшен.")

    def reset_round_questions(self, round_id: int) -> None:
        """
        Reset all questions in selected round.
        Сбросить все вопросы выбранного раунда.
        """
        count = self.game.question_service.reset_round_questions(round_id)

        if (
            self.current_question is not None
            and self.current_question.round_id == round_id
        ):
            self.clear_active_question_state()

        self.save_questions_state()
        self.status_changed.emit(f"Сброшено вопросов в раунде: {count}")

    def reset_all_questions(self) -> None:
        """
        Reset all questions in game.
        Сбросить все вопросы игры.
        """
        count = self.game.question_service.reset_all_questions()
        self.clear_active_question_state()
        self.save_questions_state()
        self.status_changed.emit(f"Сброшено всех вопросов: {count}")

    def set_question_used(self, question_id: int, used: bool) -> None:
        """
        Manually set used flag for selected question.
        Вручную установить флаг used для выбранного вопроса.
        """
        self.game.question_service.set_used(question_id, used)

        if self.current_question is not None and self.current_question.id == question_id and not used:
            self.clear_active_question_state()

        self.save_questions_state()
        state_text = "закрыт" if used else "открыт"
        self.status_changed.emit(f"Вопрос #{question_id} теперь {state_text}.")

    def add_question(self, payload: dict) -> None:
        """
        Create and store new question from dialog payload.
        Создать и сохранить новый вопрос из payload диалога.
        """
        question = Question(
            id=get_next_id(self.game.questions),
            round_id=payload["round_id"],
            team_id=payload["team_id"],
            text=payload["text"],
            answer=payload["answer"],
            timer_seconds=payload["timer_seconds"],
            points=payload["points"],
            used=payload["used"],
            category=payload["category"],
            difficulty=payload["difficulty"],
            media_type=payload["media_type"],
            media_path=payload["media_path"],
        )

        self.game.question_service.add_question(question)
        self.save_questions_state()
        self.status_changed.emit(f"Добавлен вопрос #{question.id}.")


def run_app() -> int:
    """
    Create application and show both windows.
    Создать приложение и показать оба окна.
    """
    app = QApplication([])
    app.setStyleSheet(APP_STYLESHEET)

    controller = GameController(data_path="data/game_data.json")
    admin_window = AdminWindow(controller=controller)
    display_window = DisplayWindow()

    controller.scoreboard_changed.connect(display_window.update_scores)
    controller.round_title_changed.connect(display_window.set_round_title)
    controller.status_changed.connect(display_window.set_status)
    controller.question_selected.connect(display_window.show_question)
    controller.answer_requested.connect(display_window.show_answer)
    controller.timer_updated.connect(display_window.timer_widget.set_seconds)
    controller.timer_started.connect(display_window.timer_widget.set_running)
    controller.timer_paused.connect(display_window.timer_widget.set_paused)
    controller.timer_stopped.connect(display_window.timer_widget.set_stopped)
    controller.video_requested.connect(display_window.play_video)

    controller.wheel_spin_requested.connect(admin_window.wheel.start_spin)
    controller.wheel_spin_requested.connect(
        lambda labels, index: display_window.start_wheel_animation(
            {"labels": labels, "target_index": index}
        )
    )

    display_window.public_wheel_finished.connect(controller.on_public_wheel_finished)
    display_window.video_finished.connect(controller.on_video_finished)

    controller.scoreboard_changed.emit(controller.game.teams)

    if controller.game.rounds:
        first_round_id = controller.game.rounds[0].id
        controller.select_round(first_round_id)
        admin_window.round_combo.setCurrentIndex(0)

    admin_window.show()
    display_window.show()

    return app.exec()