from dataclasses import dataclass
from typing import Optional


@dataclass
class Question:
    """
    Quiz question entity.
    Сущность вопроса викторины.
    """

    id: int
    round_id: int
    text: str
    answer: str
    timer_seconds: int
    points: int
    used: bool = False
    team_id: Optional[int] = None
    category: Optional[str] = None
    difficulty: Optional[str] = None
    media_type: Optional[str] = None
    media_path: Optional[str] = None