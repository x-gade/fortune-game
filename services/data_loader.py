import json
from pathlib import Path
from typing import Any

from models.question import Question
from models.round import Round
from models.team import Team
from utils.validators import validate_game_data


class DataLoader:
    """
    Service for loading and saving game data.
    Сервис загрузки и сохранения игровых данных.
    """

    def __init__(self, data_path: str) -> None:
        """
        Initialize loader with JSON file path.
        Инициализация загрузчика путем до JSON файла.
        """
        self.data_path = Path(data_path)

    def load_raw_data(self) -> dict[str, Any]:
        """
        Read raw JSON data from file.
        Прочитать сырые JSON данные из файла.
        """
        if not self.data_path.exists():
            raise FileNotFoundError(f"Файл данных не найден: {self.data_path}")

        with self.data_path.open("r", encoding="utf-8") as file:
            data = json.load(file)

        validate_game_data(data)
        return data

    def load_all(self) -> tuple[dict[str, Any], list[Team], list[Round], list[Question]]:
        """
        Load all root entities from JSON.
        Загрузить все корневые сущности из JSON.
        """
        data = self.load_raw_data()

        settings = data.get("settings", {})
        teams = [Team(**item) for item in data.get("teams", [])]
        rounds = [Round(**item) for item in data.get("rounds", [])]
        questions = [Question(**item) for item in data.get("questions", [])]

        return settings, teams, rounds, questions

    def save_all(
        self,
        settings: dict[str, Any],
        teams: list[Team],
        rounds: list[Round],
        questions: list[Question],
    ) -> None:
        """
        Save all entities back to JSON.
        Сохранить все сущности обратно в JSON.
        """
        data = {
            "settings": settings,
            "teams": [team.__dict__ for team in teams],
            "rounds": [round_item.__dict__ for round_item in rounds],
            "questions": [question.__dict__ for question in questions],
        }

        with self.data_path.open("w", encoding="utf-8") as file:
            json.dump(data, file, ensure_ascii=False, indent=2)