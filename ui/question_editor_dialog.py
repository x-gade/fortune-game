from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
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

    MEDIA_ROOT = Path("data/media")
    SECRET_VIDEO_NAME = "video_secret.mp4"
    RESPONSE_VIDEO_NAME = "video_response.mp4"

    def __init__(self, rounds: list, parent=None) -> None:
        """
        Initialize question editor dialog.
        Инициализация диалога создания вопроса.
        """
        super().__init__(parent)

        self.setWindowTitle("Добавить вопрос")
        self.resize(620, 680)

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

        self.category_input = QTextEdit()
        self.category_input.setFixedHeight(40)

        self.difficulty_combo = QComboBox()
        self.difficulty_combo.addItem("Не указана", None)
        self.difficulty_combo.addItem("easy", "easy")
        self.difficulty_combo.addItem("medium", "medium")
        self.difficulty_combo.addItem("hard", "hard")

        self.media_type_combo = QComboBox()
        self.media_type_combo.addItem("Нет", None)
        self.media_type_combo.addItem("Видео", "video")

        self.media_folder_combo = QComboBox()
        self.refresh_media_button = QPushButton("Обновить папки")

        self.media_info_label = QLabel("")
        self.media_info_label.setWordWrap(True)
        self.media_info_label.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        self.media_info_label.setStyleSheet("color: #d0d0d0;")

        self.used_checkbox = QCheckBox("Сразу пометить как закрытый")
        self.used_checkbox.setChecked(False)

        self.error_label = QLabel("")
        self.error_label.setStyleSheet("color: #ff6b6b;")
        self.error_label.setAlignment(Qt.AlignCenter)

        self.save_button = QPushButton("Сохранить")
        self.cancel_button = QPushButton("Отмена")

        self._build_layout()
        self._connect_events()
        self._reload_media_folders()
        self._apply_media_mode()

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
        form.addRow("Сложность:", self.difficulty_combo)
        form.addRow("Тип медиа:", self.media_type_combo)

        media_folder_row = QHBoxLayout()
        media_folder_row.addWidget(self.media_folder_combo, 1)
        media_folder_row.addWidget(self.refresh_media_button)
        form.addRow("Папка медиа:", media_folder_row)

        form.addRow("Состояние папки:", self.media_info_label)
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
        self.refresh_media_button.clicked.connect(self._reload_media_folders)
        self.media_type_combo.currentIndexChanged.connect(self._apply_media_mode)
        self.media_folder_combo.currentIndexChanged.connect(self._update_media_info)

    def _reload_media_folders(self) -> None:
        """
        Reload available media folders from data/media.
        Перезагрузить доступные папки медиа из data/media.
        """
        current_path = self.media_folder_combo.currentData()

        self.media_folder_combo.blockSignals(True)
        self.media_folder_combo.clear()
        self.media_folder_combo.addItem("Не выбрано", None)

        if self.MEDIA_ROOT.exists() and self.MEDIA_ROOT.is_dir():
            media_dirs = sorted(
                [path for path in self.MEDIA_ROOT.iterdir() if path.is_dir()],
                key=lambda item: item.name.casefold(),
            )

            for media_dir in media_dirs:
                self.media_folder_combo.addItem(media_dir.name, str(media_dir))

        if current_path is not None:
            for index in range(self.media_folder_combo.count()):
                if self.media_folder_combo.itemData(index) == current_path:
                    self.media_folder_combo.setCurrentIndex(index)
                    break

        self.media_folder_combo.blockSignals(False)
        self._update_media_info()

    def _apply_media_mode(self) -> None:
        """
        Apply current media mode to folder widgets.
        Применить текущий режим медиа к виджетам папки.
        """
        is_video = self.media_type_combo.currentData() == "video"

        self.media_folder_combo.setEnabled(is_video)
        self.refresh_media_button.setEnabled(is_video)
        self.media_info_label.setEnabled(is_video)

        if not is_video:
            self.media_folder_combo.setCurrentIndex(0)
            self.media_info_label.setText(
                "Для обычного вопроса папка медиа не используется."
            )
            return

        self._update_media_info()

    def _get_selected_media_dir(self) -> Path | None:
        """
        Return selected media directory.
        Вернуть выбранную папку медиа.
        """
        selected_path = self.media_folder_combo.currentData()
        if not selected_path:
            return None

        media_dir = Path(selected_path)
        if not media_dir.exists() or not media_dir.is_dir():
            return None

        return media_dir

    def _update_media_info(self) -> None:
        """
        Update media folder status text.
        Обновить текст статуса папки медиа.
        """
        if self.media_type_combo.currentData() != "video":
            self.media_info_label.setText(
                "Для обычного вопроса папка медиа не используется."
            )
            return

        media_dir = self._get_selected_media_dir()
        if media_dir is None:
            self.media_info_label.setText(
                "Выбери папку вопроса из data/media. "
                "Внутри должен быть video_secret.mp4. "
                "video_response.mp4 может присутствовать, а может отсутствовать."
            )
            return

        secret_path = media_dir / self.SECRET_VIDEO_NAME
        response_path = media_dir / self.RESPONSE_VIDEO_NAME

        secret_state = "есть" if secret_path.exists() else "нет"
        response_state = "есть" if response_path.exists() else "нет"

        self.media_info_label.setText(
            f"Папка: {media_dir.name}\n"
            f"video_secret.mp4: {secret_state}\n"
            f"video_response.mp4: {response_state}\n"
            "Если video_response.mp4 отсутствует, текст ответа обязателен."
        )

    def _validate_and_accept(self) -> None:
        """
        Validate fields before accepting dialog.
        Проверить поля перед подтверждением диалога.
        """
        question_text = self.question_text.toPlainText().strip()
        answer_text = self.answer_text.toPlainText().strip()
        media_type = self.media_type_combo.currentData()

        if not question_text:
            self.error_label.setText("Текст вопроса обязателен.")
            return

        if media_type != "video" and not answer_text:
            self.error_label.setText("Для обычного вопроса ответ обязателен.")
            return

        if media_type == "video":
            media_dir = self._get_selected_media_dir()
            if media_dir is None:
                self.error_label.setText("Для видеовопроса выбери папку из data/media.")
                return

            secret_path = media_dir / self.SECRET_VIDEO_NAME
            response_path = media_dir / self.RESPONSE_VIDEO_NAME

            if not secret_path.exists():
                self.error_label.setText(
                    "В выбранной папке нет video_secret.mp4."
                )
                return

            if not response_path.exists() and not answer_text:
                self.error_label.setText(
                    "Если video_response.mp4 отсутствует, укажи текст ответа."
                )
                return

        self.error_label.clear()
        self.accept()

    def get_payload(self) -> dict:
        """
        Return dialog payload for creating question.
        Вернуть полезную нагрузку диалога для создания вопроса.
        """
        media_type = self.media_type_combo.currentData()
        media_dir = self._get_selected_media_dir()

        return {
            "round_id": self.round_combo.currentData(),
            "text": self.question_text.toPlainText().strip(),
            "answer": self.answer_text.toPlainText().strip(),
            "timer_seconds": self.timer_spin.value(),
            "points": self.points_spin.value(),
            "used": self.used_checkbox.isChecked(),
            "category": self.category_input.toPlainText().strip() or None,
            "difficulty": self.difficulty_combo.currentData(),
            "media_type": media_type,
            "media_path": str(media_dir) if media_type == "video" and media_dir else None,
        }