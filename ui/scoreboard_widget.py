from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QLabel, QVBoxLayout, QWidget

from models.team import Team


class ScoreboardWidget(QWidget):
    """
    Scoreboard widget for teams.
    Виджет табло счета команд.
    """

    def __init__(self, parent=None) -> None:
        """
        Initialize scoreboard widget.
        Инициализация виджета табло.
        """
        super().__init__(parent)

        self.layout_main = QVBoxLayout()
        self.layout_main.setContentsMargins(0, 0, 0, 0)
        self.layout_main.setSpacing(8)
        self.setLayout(self.layout_main)

        self.title_label = QLabel("Счет команд")
        self.title_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.title_label.setStyleSheet(
            """
            font-size: 20px;
            font-weight: bold;
            color: #f0f0f0;
            padding-bottom: 4px;
            """
        )
        self.layout_main.addWidget(self.title_label)

        self.cards_container = QWidget()
        self.cards_layout = QVBoxLayout()
        self.cards_layout.setContentsMargins(0, 0, 0, 0)
        self.cards_layout.setSpacing(8)
        self.cards_container.setLayout(self.cards_layout)

        self.layout_main.addWidget(self.cards_container)
        self.layout_main.addStretch(1)

        self.update_scores([])

    def _clear_cards(self) -> None:
        """
        Remove all dynamic score cards from cards layout.
        Удалить все динамические карточки счета из layout карточек.
        """
        while self.cards_layout.count():
            item = self.cards_layout.takeAt(0)

            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

            child_layout = item.layout()
            if child_layout is not None:
                while child_layout.count():
                    child_item = child_layout.takeAt(0)
                    child_widget = child_item.widget()
                    if child_widget is not None:
                        child_widget.deleteLater()

    def update_scores(self, teams: list[Team]) -> None:
        """
        Update team score cards.
        Обновить карточки счета команд.
        """
        self._clear_cards()

        if not teams:
            empty_label = QLabel("Команды отсутствуют")
            empty_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            empty_label.setStyleSheet("color: #d0d0d0; font-size: 14px;")
            self.cards_layout.addWidget(empty_label)
            return

        sorted_teams = sorted(
            teams,
            key=lambda team: (-team.score, team.name.casefold()),
        )

        total_count = len(sorted_teams)

        for index, team in enumerate(sorted_teams):
            tier_style = self._get_score_tier_style(index=index, total_count=total_count)

            card = QFrame()
            card.setStyleSheet(
                """
                QFrame {
                    background-color: #3f3f3f;
                    border: 1px solid #666666;
                    border-radius: 8px;
                }
                """
            )

            card_layout = QVBoxLayout()
            card_layout.setContentsMargins(10, 8, 10, 8)
            card_layout.setSpacing(4)

            name_label = QLabel(team.name)
            name_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            name_label.setStyleSheet(
                """
                color: #f5f5f5;
                font-size: 16px;
                font-weight: 600;
                """
            )

            score_label = QLabel(str(team.score))
            score_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            score_label.setStyleSheet(
                f"""
                color: #f5f5f5;
                font-size: 24px;
                font-weight: bold;
                padding: 2px 8px;
                border: 2px solid {tier_style};
                border-radius: 8px;
                background-color: #484848;
                """
            )

            card_layout.addWidget(name_label)
            card_layout.addWidget(score_label)
            card.setLayout(card_layout)

            self.cards_layout.addWidget(card)

    @staticmethod
    def _get_score_tier_style(index: int, total_count: int) -> str:
        """
        Return border color for score tier.
        Вернуть цвет рамки для уровня позиции в табло.
        """
        if total_count <= 1:
            return "#4f7a67"

        if total_count == 2:
            return "#4f7a67" if index == 0 else "#8a4f56"

        top_count = 1
        bottom_count = 1
        middle_start = top_count
        middle_end = total_count - bottom_count - 1

        if index < top_count:
            return "#4f7a67"

        if middle_start <= index <= middle_end:
            return "#9a7448"

        return "#8a4f56"