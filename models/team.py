from dataclasses import dataclass


@dataclass
class Team:
    """
    Team model for quiz game.
    Модель команды для викторины.
    """

    id: int
    name: str
    score: int = 0