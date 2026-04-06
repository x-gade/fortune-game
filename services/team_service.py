from models.team import Team


class TeamService:
    """
    Service for team storage management.
    Сервис управления списком команд.
    """

    def __init__(self, teams: list[Team]) -> None:
        """
        Initialize service with teams storage.
        Инициализация сервиса с хранилищем команд.
        """
        self.teams = teams

    def get_all(self) -> list[Team]:
        """
        Return all teams.
        Вернуть все команды.
        """
        return list(self.teams)

    def get_by_id(self, team_id: int) -> Team | None:
        """
        Return team by identifier.
        Вернуть команду по идентификатору.
        """
        for team in self.teams:
            if team.id == team_id:
                return team
        return None

    def add_team(self, team: Team) -> None:
        """
        Append new team to storage.
        Добавить новую команду в хранилище.
        """
        self.teams.append(team)

    def update_team(self, team_id: int, name: str) -> Team:
        """
        Update existing team name.
        Обновить имя существующей команды.
        """
        team = self.get_by_id(team_id)
        if team is None:
            raise ValueError(f"Команда с id={team_id} не найдена")

        team.name = name
        return team

    def delete_team(self, team_id: int) -> Team:
        """
        Delete team from storage and return removed object.
        Удалить команду из хранилища и вернуть удаленный объект.
        """
        for index, team in enumerate(self.teams):
            if team.id == team_id:
                return self.teams.pop(index)

        raise ValueError(f"Команда с id={team_id} не найдена")