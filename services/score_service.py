from models.team import Team


class ScoreService:
    """
    Service for team score management.
    Сервис управления очками команд.
    """

    def __init__(self, teams: list[Team]) -> None:
        """
        Initialize score service.
        Инициализация сервиса счета.
        """
        self.teams = teams

    def get_team_by_id(self, team_id: int) -> Team:
        """
        Return team by identifier.
        Вернуть команду по идентификатору.
        """
        for team in self.teams:
            if team.id == team_id:
                return team
        raise ValueError(f"Команда с id={team_id} не найдена")

    def add_points(self, team_id: int, points: int) -> None:
        """
        Add points to team.
        Начислить очки команде.
        """
        team = self.get_team_by_id(team_id)
        team.score += points

    def remove_points(self, team_id: int, points: int) -> None:
        """
        Remove points from team.
        Списать очки у команды.
        """
        team = self.get_team_by_id(team_id)
        team.score -= points