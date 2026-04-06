from models.round import Round


class RoundService:
    """
    Service for round storage management.
    Сервис управления списком раундов.
    """

    def __init__(self, rounds: list[Round]) -> None:
        """
        Initialize service with rounds storage.
        Инициализация сервиса с хранилищем раундов.
        """
        self.rounds = rounds

    def get_all(self) -> list[Round]:
        """
        Return all rounds.
        Вернуть все раунды.
        """
        return list(self.rounds)

    def get_by_id(self, round_id: int) -> Round | None:
        """
        Return round by identifier.
        Вернуть раунд по идентификатору.
        """
        for round_item in self.rounds:
            if round_item.id == round_id:
                return round_item
        return None

    def add_round(self, round_item: Round) -> None:
        """
        Append new round to storage.
        Добавить новый раунд в хранилище.
        """
        self.rounds.append(round_item)

    def update_round(self, round_id: int, name: str) -> Round:
        """
        Update existing round name.
        Обновить имя существующего раунда.
        """
        round_item = self.get_by_id(round_id)
        if round_item is None:
            raise ValueError(f"Раунд с id={round_id} не найден")

        round_item.name = name
        return round_item

    def delete_round(self, round_id: int) -> Round:
        """
        Delete round from storage and return removed object.
        Удалить раунд из хранилища и вернуть удаленный объект.
        """
        for index, round_item in enumerate(self.rounds):
            if round_item.id == round_id:
                return self.rounds.pop(index)

        raise ValueError(f"Раунд с id={round_id} не найден")