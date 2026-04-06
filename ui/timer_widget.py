from __future__ import annotations

from PySide6.QtCore import QEasingCurve, Property, QPropertyAnimation, Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QFrame, QGraphicsDropShadowEffect, QLabel, QVBoxLayout, QWidget


class TimerWidget(QWidget):
    """
    Visual timer widget with dynamic color states and pulse animation.
    Визуальный виджет таймера с динамическими цветовыми состояниями и пульсацией.
    """

    def __init__(self, parent=None) -> None:
        """
        Initialize timer widget.
        Инициализация виджета таймера.
        """
        super().__init__(parent)

        self._base_font_px = 84
        self._pulse_font_px = 102
        self._current_font_px = self._base_font_px

        self._initial_total_seconds = 0
        self._current_seconds = 0

        self._default_border_color = "#d8d8d8"
        self._default_text_color = "#f5f5f5"

        self.outer_frame = QFrame()
        self.outer_frame.setObjectName("timerOuterFrame")

        self.title_label = QLabel("Таймер")
        self.title_label.setAlignment(Qt.AlignCenter)

        self.value_label = QLabel("00:00")
        self.value_label.setAlignment(Qt.AlignCenter)

        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(22)
        shadow.setOffset(0, 0)
        shadow.setColor(QColor(0, 0, 0, 150))
        self.value_label.setGraphicsEffect(shadow)

        frame_layout = QVBoxLayout()
        frame_layout.setContentsMargins(22, 16, 22, 16)
        frame_layout.setSpacing(8)
        frame_layout.addWidget(self.title_label)
        frame_layout.addWidget(self.value_label, 1)

        self.outer_frame.setLayout(frame_layout)

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.outer_frame)
        self.setLayout(layout)

        self.setMinimumWidth(760)
        self.setMaximumWidth(860)
        self.setMinimumHeight(210)
        self.setMaximumHeight(250)

        self._pulse_animation = QPropertyAnimation(self, b"pulseFontPx", self)
        self._pulse_animation.setDuration(280)
        self._pulse_animation.setStartValue(self._pulse_font_px)
        self._pulse_animation.setEndValue(self._base_font_px)
        self._pulse_animation.setEasingCurve(QEasingCurve.OutCubic)

        self._apply_visual_state(
            border_color=self._default_border_color,
            text_color=self._default_text_color,
        )
        self._apply_font_size()

    def _apply_visual_state(self, border_color: str, text_color: str) -> None:
        """
        Apply frame and text colors.
        Применить цвета рамки и текста.
        """
        self.outer_frame.setStyleSheet(
            f"""
            QFrame#timerOuterFrame {{
                background-color: #404040;
                border: 4px solid {border_color};
                border-radius: 18px;
            }}
            """
        )

        self.title_label.setStyleSheet(
            f"""
            color: {text_color};
            font-size: 24px;
            font-weight: 700;
            padding-top: 4px;
            """
        )

        self._apply_font_size(text_color=text_color)

    def _mix_colors(self, start: QColor, end: QColor, progress: float) -> QColor:
        """
        Mix two colors by progress from 0.0 to 1.0.
        Смешать два цвета по прогрессу от 0.0 до 1.0.
        """
        progress = max(0.0, min(1.0, progress))

        red = round(start.red() + (end.red() - start.red()) * progress)
        green = round(start.green() + (end.green() - start.green()) * progress)
        blue = round(start.blue() + (end.blue() - start.blue()) * progress)

        return QColor(red, green, blue)

    def _resolve_timer_color(self, seconds: int) -> QColor:
        """
        Resolve current timer color by remaining seconds.

        Rules:
        - from start down to 30 sec: white -> amber
        - from 30 to 10 sec: amber -> hot red
        - from 10 to 0 sec: keep peak hot color

        Определить текущий цвет таймера по оставшемуся времени.

        Правила:
        - от старта до 30 сек: белый -> янтарный
        - от 30 до 10 сек: янтарный -> раскаленно-красный
        - от 10 до 0 сек: удерживать пиковый горячий цвет
        """
        white = QColor("#F5F5F5")
        amber = QColor("#FFB000")
        hot_red = QColor("#C62828")

        if seconds <= 10:
            return hot_red

        if 11 <= seconds <= 30:
            progress = (30 - seconds) / 20.0
            return self._mix_colors(amber, hot_red, progress)

        if self._initial_total_seconds <= 30:
            return amber

        start_seconds = self._initial_total_seconds
        end_seconds = 30
        interval = max(start_seconds - end_seconds, 1)

        passed = start_seconds - seconds
        progress = passed / interval

        return self._mix_colors(white, amber, progress)

    def _update_color_state(self) -> None:
        """
        Update timer colors from current runtime state.
        Обновить цвета таймера из текущего runtime-состояния.
        """
        color = self._resolve_timer_color(self._current_seconds)
        color_hex = color.name()

        self.outer_frame.setStyleSheet(
            f"""
            QFrame#timerOuterFrame {{
                background-color: #404040;
                border: 4px solid {color_hex};
                border-radius: 18px;
            }}
            """
        )

        self.title_label.setStyleSheet(
            f"""
            color: {color_hex};
            font-size: 24px;
            font-weight: 700;
            padding-top: 4px;
            """
        )

        self._apply_font_size(text_color=color_hex)

    def _format_seconds(self, seconds: int) -> str:
        """
        Format seconds to MM:SS.
        Отформатировать секунды в MM:SS.
        """
        minutes = seconds // 60
        secs = seconds % 60
        return f"{minutes:02d}:{secs:02d}"

    def _trigger_tick_pulse(self) -> None:
        """
        Trigger visible pulse animation for dangerous zone.
        Запустить заметную пульсацию для опасной зоны таймера.
        """
        self._pulse_animation.stop()
        self._current_font_px = self._pulse_font_px
        self._apply_font_size()
        self._pulse_animation.start()

    def _apply_font_size(self, text_color: str | None = None) -> None:
        """
        Apply current numeric font size through stylesheet in px.
        Применить текущий размер цифр через stylesheet в px.
        """
        if text_color is None:
            text_color = self._resolve_timer_color(self._current_seconds).name()

        self.value_label.setStyleSheet(
            f"""
            color: {text_color};
            font-size: {int(self._current_font_px)}px;
            font-weight: 800;
            padding: 0px 8px 8px 8px;
            """
        )
        self.value_label.update()
        self.update()

    def getPulseFontPx(self) -> float:
        """
        Return current animated font pixel size.
        Вернуть текущий анимируемый pixel size шрифта.
        """
        return float(self._current_font_px)

    def setPulseFontPx(self, size: float) -> None:
        """
        Update animated font pixel size.
        Обновить анимируемый pixel size шрифта.
        """
        self._current_font_px = float(size)
        self._apply_font_size()

    pulseFontPx = Property(float, getPulseFontPx, setPulseFontPx)

    def set_seconds(self, seconds: int) -> None:
        """
        Display remaining seconds and update dynamic visual state.
        Отобразить оставшееся количество секунд и обновить динамическое визуальное состояние.
        """
        seconds = max(0, seconds)

        if seconds > self._initial_total_seconds:
            self._initial_total_seconds = seconds

        if self._initial_total_seconds == 0 and seconds > 0:
            self._initial_total_seconds = seconds

        self._current_seconds = seconds
        self.value_label.setText(self._format_seconds(seconds))
        self._update_color_state()

        if 0 < seconds <= 5:
            self._trigger_tick_pulse()

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
        Mark timer as stopped and reset pulse state.
        Отметить таймер как остановленный и сбросить состояние пульсации.
        """
        self.title_label.setText("Таймер [СТОП]")
        self._pulse_animation.stop()
        self._current_font_px = self._base_font_px

        if self._current_seconds <= 0:
            self._initial_total_seconds = 0
            self.outer_frame.setStyleSheet(
                f"""
                QFrame#timerOuterFrame {{
                    background-color: #404040;
                    border: 4px solid {self._default_border_color};
                    border-radius: 18px;
                }}
                """
            )
            self.title_label.setStyleSheet(
                f"""
                color: {self._default_text_color};
                font-size: 24px;
                font-weight: 700;
                padding-top: 4px;
                """
            )
            self._apply_font_size(text_color=self._default_text_color)
        else:
            self._update_color_state()