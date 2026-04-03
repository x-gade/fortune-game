import time
from pathlib import Path
from typing import Optional

from models.game_state import GameState
from models.question import Question
from services.data_loader import DataLoader
from services.question_service import QuestionService
from services.score_service import ScoreService
from services.timer_service import TimerService
from services.wheel_service import WheelService
from utils.formatters import format_scoreboard, format_question_card


class GameService:
    """
    Main game coordinator service.
    Главный координирующий сервис игры.
    """

    def __init__(self, data_path: str) -> None:
        """
        Initialize game services and load data.
        Инициализация игровых сервисов и загрузка данных.
        """
        self.data_loader = DataLoader(data_path)
        self.settings, self.teams, self.rounds, self.questions = self.data_loader.load_all()

        default_timer = int(self.settings.get("default_timer_seconds", 30))

        self.question_service = QuestionService(
            questions=self.questions,
            default_timer_seconds=default_timer,
        )
        self.score_service = ScoreService(self.teams)
        self.timer_service = TimerService()
        self.wheel_service = WheelService()
        self.state = GameState()

    def choose_round(self) -> Optional[int]:
        """
        Ask user to select a round.
        Запросить у пользователя выбор раунда.
        """
        print("\nДоступные раунды:")
        for round_item in self.rounds:
            print(f"{round_item.id}. {round_item.name}")

        raw_value = input("Введите id раунда или q для выхода: ").strip()
        if raw_value.lower() == "q":
            return None

        try:
            round_id = int(raw_value)
        except ValueError:
            print("Некорректный ввод раунда.")
            return None

        for round_item in self.rounds:
            if round_item.id == round_id:
                return round_id

        print("Раунд не найден.")
        return None

    def choose_team(self) -> Optional[int]:
        """
        Ask user to select a team.
        Запросить у пользователя выбор команды.
        """
        print("\nДоступные команды:")
        for team in self.teams:
            print(f"{team.id}. {team.name} | очки: {team.score}")

        raw_value = input("Введите id команды или q для выхода: ").strip()
        if raw_value.lower() == "q":
            return None

        try:
            team_id = int(raw_value)
        except ValueError:
            print("Некорректный ввод команды.")
            return None

        for team in self.teams:
            if team.id == team_id:
                return team_id

        print("Команда не найдена.")
        return None

    def play_media_if_needed(self, question: Question) -> None:
        """
        Handle media before timer start.
        Обработать медиа перед запуском таймера.
        """
        if question.media_type != "video":
            return

        if not question.media_path:
            print("У вопроса указан тип video, но не задан media_path.")
            input("Нажмите Enter для продолжения...")
            return

        media_file = Path(question.media_path)
        print("\n=== ВИДЕОВОПРОС ===")
        print(f"Файл видео: {media_file}")

        if not media_file.exists():
            print("Видео-файл не найден. Таймер будет запущен без видео.")
            input("Нажмите Enter для продолжения...")
            return

        print("Здесь в будущем будет встроенный плеер GUI.")
        print("Пока ведущий может открыть файл вручную.")
        input("После завершения видео нажмите Enter для запуска таймера...")

    def run_wheel_for_question(self, available_questions: list[Question], selected_question: Question) -> None:
        """
        Simulate wheel spinning until selected question.
        Имитировать вращение колеса до выбранного вопроса.
        """
        labels = self.wheel_service.build_wheel_labels(available_questions)
        target_index = self.wheel_service.pick_target_index(
            questions=available_questions,
            target_question_id=selected_question.id,
        )
        steps = self.wheel_service.simulate_spin_steps(
            item_count=len(available_questions),
            target_index=target_index,
        )

        print("\n=== КОЛЕСО ФОРТУНЫ ===")
        for index in steps:
            print(f"\rКрутится: {labels[index]}", end="", flush=True)
            time.sleep(0.08)

        print("\nКолесо остановилось.")
        self.state.current_wheel_label = labels[target_index]

    def handle_question_result(self, team_id: int, question: Question) -> None:
        """
        Ask whether answer is correct and update score.
        Запросить результат ответа и обновить счет.
        """
        print("\n=== ОТВЕТ ===")
        print(question.answer)

        raw_result = input("Ответ правильный? [y/n]: ").strip().lower()
        if raw_result == "y":
            self.score_service.add_points(team_id, question.points)
            self.state.last_result_correct = True
            print(f"Команде начислено {question.points} очков.")
            return

        self.state.last_result_correct = False
        print("Очки не начислены.")

    def play_turn(self, round_id: int, team_id: int) -> None:
        """
        Play one full game turn.
        Сыграть один полный игровой ход.
        """
        available_questions = self.question_service.get_available_questions(
            round_id=round_id,
            team_id=team_id,
        )

        if not available_questions:
            print("Для выбранного раунда больше нет доступных вопросов.")
            return

        selected_question = self.question_service.pick_random_question(
            round_id=round_id,
            team_id=team_id,
        )
        if selected_question is None:
            print("Не удалось выбрать вопрос.")
            return

        self.state.current_round_id = round_id
        self.state.current_team_id = team_id
        self.state.current_question_id = selected_question.id

        self.run_wheel_for_question(
            available_questions=available_questions,
            selected_question=selected_question,
        )

        print("\n" + format_question_card(selected_question))
        self.play_media_if_needed(selected_question)

        timer_seconds = self.question_service.get_question_timer(selected_question)
        input("Нажмите Enter для запуска таймера...")
        self.timer_service.run_timer(timer_seconds)

        self.handle_question_result(team_id=team_id, question=selected_question)
        self.question_service.mark_used(selected_question.id)

        self.state.history.append(
            (
                f"round={round_id}; "
                f"team={team_id}; "
                f"question={selected_question.id}; "
                f"media={selected_question.media_type}; "
                f"correct={self.state.last_result_correct}"
            )
        )

        self.data_loader.save_all(
            settings=self.settings,
            teams=self.teams,
            rounds=self.rounds,
            questions=self.questions,
        )

    def run(self) -> None:
        """
        Start main console game loop.
        Запустить основной консольный игровой цикл.
        """
        print("Fortune Game MVP запущен.")

        while True:
            print("\n==============================")
            print(format_scoreboard(self.teams))
            print("==============================")

            round_id = self.choose_round()
            if round_id is None:
                print("Выход из игры.")
                break

            team_id = self.choose_team()
            if team_id is None:
                print("Выход из игры.")
                break

            input("\nНажмите Enter, чтобы крутить колесо...")
            self.play_turn(round_id=round_id, team_id=team_id)