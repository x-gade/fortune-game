import math
import random

from PySide6.QtCore import QEasingCurve, Property, QPropertyAnimation, QPointF, QRectF, Qt, Signal
from PySide6.QtGui import QColor, QFont, QPainter, QPen, QPolygonF
from PySide6.QtWidgets import QWidget


class WheelWidget(QWidget):
    """
    Visual wheel widget with simple spin animation.
    Визуальный виджет колеса с простой анимацией вращения.
    """

    spin_finished = Signal()

    def __init__(self, parent=None) -> None:
        """
        Initialize wheel widget.
        Инициализация виджета колеса.
        """
        super().__init__(parent)

        self._rotation = 0.0
        self.labels: list[str] = []
        self.target_index: int | None = None

        self.animation = QPropertyAnimation(self, b"rotation")
        self.animation.setDuration(4200)
        self.animation.setEasingCurve(QEasingCurve.OutCubic)
        self.animation.finished.connect(self.spin_finished.emit)

        self.setMinimumSize(420, 420)

    def get_rotation(self) -> float:
        """
        Return current rotation angle.
        Вернуть текущий угол вращения.
        """
        return self._rotation

    def set_rotation(self, value: float) -> None:
        """
        Set current rotation angle.
        Установить текущий угол вращения.
        """
        self._rotation = value
        self.update()

    rotation = Property(float, get_rotation, set_rotation)

    def start_spin(self, labels: list[str], target_index: int) -> None:
        """
        Start wheel spin toward selected target sector.
        Запустить вращение колеса к выбранному сектору.
        """
        self.labels = labels[:]
        self.target_index = target_index

        if not self.labels:
            self.update()
            self.spin_finished.emit()
            return

        sector_angle = 360.0 / len(self.labels)

        target_center_angle = target_index * sector_angle + sector_angle / 2
        pointer_angle = 90.0
        needed_delta = pointer_angle - target_center_angle

        while needed_delta < 0:
            needed_delta += 360.0

        full_turns = random.randint(4, 7)

        start_value = self._rotation % 360.0
        end_value = self._rotation + full_turns * 360.0 + needed_delta

        self.animation.stop()
        self.animation.setStartValue(start_value)
        self.animation.setEndValue(end_value)
        self.animation.start()

    def paintEvent(self, event) -> None:
        """
        Paint wheel and pointer.
        Отрисовать колесо и указатель.
        """
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        rect_size = min(self.width(), self.height()) - 40
        rect = QRectF(
            (self.width() - rect_size) / 2,
            (self.height() - rect_size) / 2,
            rect_size,
            rect_size,
        )
        center_x = rect.center().x()
        center_y = rect.center().y()

        painter.fillRect(self.rect(), QColor("#3a3a3a"))

        if not self.labels:
            painter.setPen(QColor("#f0f0f0"))
            painter.setFont(QFont("Arial", 16, QFont.Bold))
            painter.drawText(self.rect(), Qt.AlignCenter, "Нет доступных вопросов")
            return

        sector_angle = 360.0 / len(self.labels)
        colors = [
            QColor("#4E79A7"),
            QColor("#F28E2B"),
            QColor("#E15759"),
            QColor("#76B7B2"),
            QColor("#59A14F"),
            QColor("#EDC948"),
            QColor("#B07AA1"),
            QColor("#FF9DA7"),
            QColor("#9C755F"),
            QColor("#BAB0AC"),
        ]

        painter.save()
        painter.translate(center_x, center_y)
        painter.rotate(self._rotation)
        painter.translate(-center_x, -center_y)

        for index, label in enumerate(self.labels):
            start_deg = 90 - index * sector_angle
            painter.setBrush(colors[index % len(colors)])
            painter.setPen(QPen(Qt.black, 2))
            painter.drawPie(rect, int(start_deg * 16), int(-sector_angle * 16))

            text_angle = start_deg - sector_angle / 2
            radius = rect.width() / 2 * 0.62
            text_x = center_x + radius * math.cos(math.radians(text_angle))
            text_y = center_y - radius * math.sin(math.radians(text_angle))

            text_rect = QRectF(text_x - 55, text_y - 16, 110, 32)
            painter.save()
            painter.setPen(Qt.white)
            painter.setFont(QFont("Arial", 9, QFont.Bold))
            painter.drawText(text_rect, Qt.AlignCenter, label)
            painter.restore()

        painter.restore()

        painter.setBrush(QColor("#ffffff"))
        painter.setPen(QPen(Qt.black, 2))

        top_center = QPointF(rect.center().x(), rect.top() - 8)
        left_point = QPointF(rect.center().x() - 14, rect.top() - 34)
        right_point = QPointF(rect.center().x() + 14, rect.top() - 34)
        pointer = QPolygonF([top_center, left_point, right_point])
        painter.drawPolygon(pointer)

        painter.setBrush(QColor("#202020"))
        painter.drawEllipse(rect.center(), 18, 18)