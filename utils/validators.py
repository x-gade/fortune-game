from typing import Any


def validate_game_data(data: dict[str, Any]) -> None:
    """
    Validate root structure of game data JSON.
    Проверить корневую структуру игрового JSON файла.
    """
    required_root_keys = ["teams", "rounds", "questions"]

    for key in required_root_keys:
        if key not in data:
            raise ValueError(f"В JSON отсутствует обязательный ключ: {key}")

    if not isinstance(data["teams"], list):
        raise ValueError("Поле 'teams' должно быть списком")

    if not isinstance(data["rounds"], list):
        raise ValueError("Поле 'rounds' должно быть списком")

    if not isinstance(data["questions"], list):
        raise ValueError("Поле 'questions' должно быть списком")

    for team in data["teams"]:
        if "id" not in team or "name" not in team:
            raise ValueError("У команды должны быть поля 'id' и 'name'")

    for round_item in data["rounds"]:
        if "id" not in round_item or "name" not in round_item:
            raise ValueError("У раунда должны быть поля 'id' и 'name'")

    for question in data["questions"]:
        required_question_keys = [
            "id",
            "round_id",
            "text",
            "answer",
            "points",
        ]

        for key in required_question_keys:
            if key not in question:
                raise ValueError(f"У вопроса отсутствует обязательный ключ: {key}")

        if "timer_seconds" in question and int(question["timer_seconds"]) <= 0:
            raise ValueError("Поле 'timer_seconds' должно быть больше 0")

        media_type = question.get("media_type")
        media_path = question.get("media_path")

        allowed_media_types = {None, "video"}
        if media_type not in allowed_media_types:
            raise ValueError(
                f"Недопустимое значение media_type: {media_type}. "
                f"Разрешено только: {allowed_media_types}"
            )

        if media_type == "video" and not media_path:
            raise ValueError(
                "Если media_type == 'video', поле media_path обязательно"
            )