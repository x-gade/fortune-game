import math
import random

from PySide6.QtCore import QElapsedTimer, QPointF, QRectF, Qt, QTimer, Signal
from PySide6.QtGui import QColor, QFont, QPainter, QPen, QPolygonF
from PySide6.QtWidgets import QWidget


class WheelWidget(QWidget):
    """
    Visual wheel widget with smooth continuous spin curve.
    Визуальный виджет колеса с плавной непрерывной кривой вращения.
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

        self.total_duration_ms = 44000
        self.frame_interval_ms = 16

        self.spin_timer = QTimer(self)
        self.spin_timer.setTimerType(Qt.PreciseTimer)
        self.spin_timer.setInterval(self.frame_interval_ms)
        self.spin_timer.timeout.connect(self._on_spin_tick)

        self.elapsed_timer = QElapsedTimer()

        self._spin_active = False
        self._start_rotation = 0.0
        self._final_rotation = 0.0
        self._total_delta = 0.0

        self._curve_samples: list[float] = []
        self._curve_resolution = 4000

        self.setMinimumSize(420, 420)

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

        full_turns = random.randint(54, 72)

        self._start_rotation = self._rotation
        self._final_rotation = self._rotation + full_turns * 360.0 + needed_delta
        self._total_delta = self._final_rotation - self._start_rotation

        self._build_motion_curve()

        self._spin_active = True
        self.spin_timer.stop()
        self.elapsed_timer.restart()
        self.spin_timer.start()
        self.update()

    def _build_motion_curve(self) -> None:
        """
        Build normalized cumulative motion curve.
        Построить нормализованную накопленную кривую движения.
        """
        resolution = self._curve_resolution
        cumulative = [0.0]
        total_area = 0.0

        for index in range(1, resolution + 1):
            progress = index / resolution
            speed = self._speed_profile(progress)
            total_area += speed
            cumulative.append(total_area)

        if total_area <= 0:
            self._curve_samples = [i / resolution for i in range(resolution + 1)]
            return

        self._curve_samples = [value / total_area for value in cumulative]

    @staticmethod
    def _speed_profile(progress: float) -> float:
        """
        Continuous speed profile:
        quick spin-up at start, then long smooth decay.
        Непрерывный профиль скорости:
        быстрый разгон в начале, затем длительное плавное затухание.
        """
        progress = max(0.0, min(1.0, progress))

        # Быстрый старт из почти нулевой скорости.
        ramp_up = 1.0 - math.exp(-18.0 * progress)

        # Плавное постепенное затухание на всей длине анимации.
        decay = pow(1.0 - progress, 1.35)

        speed = ramp_up * decay

        # Под конец прижимаем скорость сильнее, чтобы остановка была мягкой.
        final_soft_stop = pow(1.0 - progress, 0.9)

        return max(speed * final_soft_stop, 0.0)

    def _normalized_motion(self, progress: float) -> float:
        """
        Return normalized cumulative displacement for progress.
        Вернуть нормализованное накопленное смещение для прогресса.
        """
        progress = max(0.0, min(1.0, progress))

        if not self._curve_samples:
            return progress

        scaled_index = progress * self._curve_resolution
        left_index = int(math.floor(scaled_index))
        right_index = min(left_index + 1, self._curve_resolution)

        if left_index >= self._curve_resolution:
            return 1.0

        local_t = scaled_index - left_index
        left_value = self._curve_samples[left_index]
        right_value = self._curve_samples[right_index]

        return left_value + (right_value - left_value) * local_t

    def _on_spin_tick(self) -> None:
        """
        Update wheel rotation frame by frame.
        Обновить вращение колеса покадрово.
        """
        if not self._spin_active:
            return

        elapsed_ms = self.elapsed_timer.elapsed()

        if elapsed_ms >= self.total_duration_ms:
            self._rotation = self._final_rotation
            self._spin_active = False
            self.spin_timer.stop()
            self.update()
            self.spin_finished.emit()
            return

        progress = elapsed_ms / self.total_duration_ms
        normalized_displacement = self._normalized_motion(progress)

        self._rotation = self._start_rotation + self._total_delta * normalized_displacement
        self.update()

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