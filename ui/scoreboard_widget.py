from PySide6.QtGui import QFont
from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget

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

        self.title_label = QLabel("Счет команд")
        self.title_label.setFont(QFont("Arial", 18, QFont.Bold))
        self.layout_main.addWidget(self.title_label)

        self.team_labels: list[QLabel] = []

        self.setLayout(self.layout_main)

    def update_scores(self, teams: list[Team]) -> None:
        """
        Update team score labels.
        Обновить отображение счета команд.
        """
        for label in self.team_labels:
            self.layout_main.removeWidget(label)
            label.deleteLater()

        self.team_labels.clear()

        for team in teams:
            label = QLabel(f"{team.name}: {team.score}")
            label.setFont(QFont("Arial", 26, QFont.Bold))
            self.layout_main.addWidget(label)
            self.team_labels.append(label)