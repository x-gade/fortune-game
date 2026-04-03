import random

from models.question import Question


class WheelService:
    """
    Logical wheel service based on available questions.
    Логический сервис колеса на основе доступных вопросов.
    """

    def build_wheel_labels(self, questions: list[Question]) -> list[str]:
        """
        Build wheel labels from available questions.
        Собрать подписи колеса из доступных вопросов.
        """
        labels: list[str] = []

        for question in questions:
            label = f"Вопрос #{question.id}"
            if question.media_type == "video":
                label += " [VIDEO]"
            labels.append(label)

        return labels

    def pick_target_index(self, questions: list[Question], target_question_id: int) -> int:
        """
        Find wheel index for selected target question.
        Найти индекс сектора колеса для выбранного вопроса.
        """
        for index, question in enumerate(questions):
            if question.id == target_question_id:
                return index

        raise ValueError(f"Вопрос с id={target_question_id} отсутствует в колесе")

    def simulate_spin_steps(self, item_count: int, target_index: int) -> list[int]:
        """
        Build pseudo-spin sequence ending on target index.
        Построить псевдо-анимационную последовательность с остановкой на нужном индексе.
        """
        if item_count <= 0:
            return []

        full_turns = random.randint(2, 4)
        total_steps = full_turns * item_count + target_index
        return [step % item_count for step in range(total_steps + 1)]