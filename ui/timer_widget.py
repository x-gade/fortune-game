from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget


class TimerWidget(QWidget):
    """
    Visual timer widget.
    Визуальный виджет таймера.
    """

    def __init__(self, parent=None) -> None:
        """
        Initialize timer widget.
        Инициализация виджета таймера.
        """
        super().__init__(parent)

        self.title_label = QLabel("Таймер")
        self.title_label.setAlignment(Qt.AlignCenter)

        self.value_label = QLabel("00:00")
        self.value_label.setAlignment(Qt.AlignCenter)
        self.value_label.setFont(QFont("Arial", 28, QFont.Bold))

        layout = QVBoxLayout()
        layout.addWidget(self.title_label)
        layout.addWidget(self.value_label)
        self.setLayout(layout)

    def set_seconds(self, seconds: int) -> None:
        """
        Display remaining seconds.
        Отобразить оставшееся количество секунд.
        """
        minutes = seconds // 60
        secs = seconds % 60
        self.value_label.setText(f"{minutes:02d}:{secs:02d}")

    def set_paused(self) -> None:
        """
        Mark timer as paused.
        Отметить таймер как поставленный на паузу.
        """
        self.title_label.setText("Таймер [ПАУЗА]")

    def set_running(self) -> None:
        """
        Mark timer as running.
        Отметить таймер как запущенный.
        """
        self.title_label.setText("Таймер")

    def set_stopped(self) -> None:
        """
        Mark timer as stopped.
        Отметить таймер как остановленный.
        """
        self.title_label.setText("Таймер [СТОП]")