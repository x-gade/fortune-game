from models.question import Question
from models.team import Team


def format_scoreboard(teams: list[Team]) -> str:
    """
    Build text scoreboard for console output.
    Сформировать текстовое табло счета для консольного вывода.
    """
    lines = ["Текущий счет:"]
    for team in teams:
        lines.append(f"- {team.name}: {team.score}")
    return "\n".join(lines)


def format_question_card(question: Question) -> str:
    """
    Build formatted text block for question output.
    Сформировать форматированный текстовый блок для вывода вопроса.
    """
    lines = [
        "=== ВОПРОС ===",
        f"ID: {question.id}",
        f"Текст: {question.text}",
        f"Очки: {question.points}",
        f"Таймер: {question.timer_seconds} сек.",
    ]

    if question.team_id is not None:
        lines.append(f"Привязанная команда: {question.team_id}")

    if question.category:
        lines.append(f"Категория: {question.category}")

    if question.difficulty:
        lines.append(f"Сложность: {question.difficulty}")

    if question.media_type:
        lines.append(f"Медиа: {question.media_type}")

    if question.media_path:
        lines.append(f"Путь к медиа: {question.media_path}")

    return "\n".join(lines)