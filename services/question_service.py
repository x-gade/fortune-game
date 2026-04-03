import random
from typing import Optional

from models.question import Question


class QuestionService:
    """
    Service for selecting and updating questions.
    Сервис выбора и обновления вопросов.
    """

    def __init__(self, questions: list[Question], default_timer_seconds: int = 30) -> None:
        """
        Initialize question service.
        Инициализация сервиса вопросов.
        """
        self.questions = questions
        self.default_timer_seconds = default_timer_seconds

    def get_available_questions(
        self,
        round_id: int,
        team_id: Optional[int] = None,
    ) -> list[Question]:
        """
        Return available questions for round and optional team.
        Вернуть доступные вопросы для раунда и, при необходимости, команды.
        """
        result: list[Question] = []

        for question in self.questions:
            if question.used:
                continue

            if question.round_id != round_id:
                continue

            if question.team_id is None:
                result.append(question)
                continue

            if team_id is not None and question.team_id == team_id:
                result.append(question)

        return result

    def pick_random_question(
        self,
        round_id: int,
        team_id: Optional[int] = None,
    ) -> Optional[Question]:
        """
        Pick random available question.
        Выбрать случайный доступный вопрос.
        """
        available = self.get_available_questions(round_id=round_id, team_id=team_id)
        if not available:
            return None
        return random.choice(available)

    def mark_used(self, question_id: int) -> None:
        """
        Mark question as used.
        Пометить вопрос как использованный.
        """
        for question in self.questions:
            if question.id == question_id:
                question.used = True
                return

        raise ValueError(f"Вопрос с id={question_id} не найден")

    def get_question_timer(self, question: Question) -> int:
        """
        Return effective timer value for question.
        Вернуть итоговое значение таймера для вопроса.
        """
        if question.timer_seconds > 0:
            return question.timer_seconds
        return self.default_timer_seconds