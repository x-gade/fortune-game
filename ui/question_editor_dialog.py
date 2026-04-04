from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSpinBox,
    QTextEdit,
    QVBoxLayout,
)


class QuestionEditorDialog(QDialog):
    """
    Dialog for creating a new question.
    Диалог создания нового вопроса.
    """

    def __init__(self, rounds: list, parent=None) -> None:
        """
        Initialize question editor dialog.
        Инициализация диалога создания вопроса.
        """
        super().__init__(parent)

        self.setWindowTitle("Добавить вопрос")
        self.resize(520, 600)

        self.round_combo = QComboBox()
        for round_item in rounds:
            self.round_combo.addItem(round_item.name, round_item.id)

        self.question_text = QTextEdit()
        self.answer_text = QTextEdit()

        self.timer_spin = QSpinBox()
        self.timer_spin.setRange(1, 3600)
        self.timer_spin.setValue(30)

        self.points_spin = QSpinBox()
        self.points_spin.setRange(0, 100000)
        self.points_spin.setValue(100)

        self.category_input = QLineEdit()
        self.difficulty_input = QLineEdit()

        self.media_type_combo = QComboBox()
        self.media_type_combo.addItem("Нет", None)
        self.media_type_combo.addItem("Видео", "video")

        self.media_path_input = QLineEdit()

        self.used_checkbox = QCheckBox("Сразу пометить как закрытый")
        self.used_checkbox.setChecked(False)

        self.error_label = QLabel("")
        self.error_label.setStyleSheet("color: #ff6b6b;")
        self.error_label.setAlignment(Qt.AlignCenter)

        self.save_button = QPushButton("Сохранить")
        self.cancel_button = QPushButton("Отмена")

        self._build_layout()
        self._connect_events()

    def _build_layout(self) -> None:
        """
        Build dialog layout.
        Построить компоновку диалога.
        """
        form = QFormLayout()
        form.addRow("Раунд:", self.round_combo)
        form.addRow("Текст вопроса:", self.question_text)
        form.addRow("Ответ:", self.answer_text)
        form.addRow("Таймер (сек):", self.timer_spin)
        form.addRow("Очки:", self.points_spin)
        form.addRow("Категория:", self.category_input)
        form.addRow("Сложность:", self.difficulty_input)
        form.addRow("Тип медиа:", self.media_type_combo)
        form.addRow("Путь к медиа:", self.media_path_input)
        form.addRow("", self.used_checkbox)

        buttons = QHBoxLayout()
        buttons.addWidget(self.save_button)
        buttons.addWidget(self.cancel_button)

        layout = QVBoxLayout()
        layout.addLayout(form)
        layout.addWidget(self.error_label)
        layout.addLayout(buttons)

        self.setLayout(layout)

    def _connect_events(self) -> None:
        """
        Connect dialog actions.
        Подключить действия диалога.
        """
        self.save_button.clicked.connect(self._validate_and_accept)
        self.cancel_button.clicked.connect(self.reject)

    def _validate_and_accept(self) -> None:
        """
        Validate fields before accepting dialog.
        Проверить поля перед подтверждением диалога.
        """
        if not self.question_text.toPlainText().strip():
            self.error_label.setText("Текст вопроса обязателен.")
            return

        if not self.answer_text.toPlainText().strip():
            self.error_label.setText("Ответ обязателен.")
            return

        media_type = self.media_type_combo.currentData()
        media_path = self.media_path_input.text().strip()

        if media_type == "video" and not media_path:
            self.error_label.setText("Для видеовопроса укажи путь к файлу.")
            return

        self.accept()

    def get_payload(self) -> dict:
        """
        Return dialog payload for creating question.
        Вернуть полезную нагрузку диалога для создания вопроса.
        """
        return {
            "round_id": self.round_combo.currentData(),
            "text": self.question_text.toPlainText().strip(),
            "answer": self.answer_text.toPlainText().strip(),
            "timer_seconds": self.timer_spin.value(),
            "points": self.points_spin.value(),
            "used": self.used_checkbox.isChecked(),
            "category": self.category_input.text().strip() or None,
            "difficulty": self.difficulty_input.text().strip() or None,
            "media_type": self.media_type_combo.currentData(),
            "media_path": self.media_path_input.text().strip() or None,
        }