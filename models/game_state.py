from dataclasses import dataclass, field
from typing import Optional


@dataclass
class GameState:
    """
    Runtime state of current game session.
    Текущее состояние игровой сессии.
    """

    current_round_id: Optional[int] = None
    current_team_id: Optional[int] = None
    current_question_id: Optional[int] = None
    current_wheel_label: Optional[str] = None
    last_result_correct: Optional[bool] = None
    history: list[str] = field(default_factory=list)