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

    def get_available_questions(self, round_id: int) -> list[Question]:
        """
        Return available questions for selected round.
        Вернуть доступные вопросы выбранного раунда.
        """
        return [
            question
            for question in self.questions
            if not question.used and question.round_id == round_id
        ]

    def get_questions_by_round(self, round_id: Optional[int] = None) -> list[Question]:
        """
        Return all questions or questions filtered by round.
        Вернуть все вопросы или вопросы по выбранному раунду.
        """
        if round_id is None:
            return list(self.questions)

        return [question for question in self.questions if question.round_id == round_id]

    def get_question_by_id(self, question_id: int) -> Optional[Question]:
        """
        Return question by identifier.
        Вернуть вопрос по идентификатору.
        """
        for question in self.questions:
            if question.id == question_id:
                return question
        return None

    def pick_random_question(self, round_id: int) -> Optional[Question]:
        """
        Pick random available question for round.
        Выбрать случайный доступный вопрос для раунда.
        """
        available = self.get_available_questions(round_id=round_id)
        if not available:
            return None
        return random.choice(available)

    def get_unused_count_by_round(self, round_id: int) -> int:
        """
        Return count of unused questions in round.
        Вернуть количество неиспользованных вопросов в раунде.
        """
        return len(self.get_available_questions(round_id))

    def mark_used(self, question_id: int) -> None:
        """
        Mark question as used.
        Пометить вопрос как использованный.
        """
        question = self.get_question_by_id(question_id)
        if question is None:
            raise ValueError(f"Вопрос с id={question_id} не найден")

        question.used = True

    def set_used(self, question_id: int, used: bool) -> None:
        """
        Set question used flag manually.
        Установить флаг used вручную.
        """
        question = self.get_question_by_id(question_id)
        if question is None:
            raise ValueError(f"Вопрос с id={question_id} не найден")

        question.used = used

    def reset_question(self, question_id: int) -> None:
        """
        Reset one question to unused state.
        Сбросить один вопрос в состояние неиспользованного.
        """
        self.set_used(question_id, False)

    def reset_round_questions(self, round_id: int) -> int:
        """
        Reset all questions in selected round.
        Сбросить все вопросы выбранного раунда.
        """
        count = 0
        for question in self.questions:
            if question.round_id == round_id:
                question.used = False
                count += 1
        return count

    def reset_all_questions(self) -> int:
        """
        Reset all questions in the game.
        Сбросить все вопросы игры.
        """
        count = 0
        for question in self.questions:
            question.used = False
            count += 1
        return count

    def add_question(self, question: Question) -> None:
        """
        Append new question to storage.
        Добавить новый вопрос в хранилище.
        """
        self.questions.append(question)

    def get_question_timer(self, question: Question) -> int:
        """
        Return effective timer value for question.
        Вернуть итоговое значение таймера для вопроса.
        """
        if question.timer_seconds > 0:
            return question.timer_seconds
        return self.default_timer_seconds