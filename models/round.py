from dataclasses import dataclass


@dataclass
class Round:
    """
    Round model for quiz game.
    Модель раунда для викторины.
    """

    id: int
    name: str