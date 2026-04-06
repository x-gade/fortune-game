from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QObject, QTimer, QUrl, Signal
from PySide6.QtMultimedia import QAudioOutput, QMediaPlayer
from PySide6.QtWidgets import QApplication

from models.question import Question
from models.round import Round
from models.team import Team
from services.game_service import GameService
from ui.admin_window import AdminWindow
from ui.display_window import DisplayWindow
from utils.helpers import get_next_id


APP_STYLESHEET = """
QWidget {
    background-color: #3a3a3a;
    color: #f0f0f0;
    font-size: 13px;
}

QLabel {
    color: #f0f0f0;
}

QPushButton {
    background-color: #505050;
    color: #ffffff;
    border: 1px solid #707070;
    border-radius: 6px;
    padding: 6px 10px;
}

QPushButton:hover {
    background-color: #5e5e5e;
}

QPushButton:pressed {
    background-color: #444444;
}

QComboBox {
    background-color: #505050;
    color: #ffffff;
    border: 1px solid #707070;
    border-radius: 4px;
    padding: 4px 8px;
}

QComboBox QAbstractItemView {
    background-color: #454545;
    color: #ffffff;
    selection-background-color: #606060;
}

QTextEdit {
    background-color: #2f2f2f;
    color: #f5f5f5;
    border: 1px solid #666666;
}

QToolTip {
    background-color: #505050;
    color: #ffffff;
    border: 1px solid #707070;
}
"""


class GameController(QObject):
    """
    UI game controller for multi-window workflow.
    UI-контроллер игры для работы с несколькими окнами.
    """

    wheel_spin_requested = Signal(list, int)
    question_selected = Signal(object)
    answer_requested = Signal(str)
    public_answer_requested = Signal(str)
    scoreboard_changed = Signal(object)
    round_title_changed = Signal(str)
    status_changed = Signal(str)
    timer_updated = Signal(int)
    timer_started = Signal()
    timer_paused = Signal()
    timer_stopped = Signal()
    video_requested = Signal(dict)
    questions_changed = Signal()
    teams_changed = Signal()
    rounds_changed = Signal()
    active_team_changed = Signal(str)
    next_team_changed = Signal(str)
    round_progress_changed = Signal(str)
    video_state_changed = Signal()
    extra_time_state_changed = Signal(dict)

    QUESTION_VIDEO_NAME = "video_secret.mp4"
    ANSWER_VIDEO_NAME = "video_response.mp4"

    EXTRA_TIME_RULES = {
        10: 5,
        15: 10,
        30: 25,
        60: 45,
    }

    MAX_TEAMS = 4

    def __init__(self, data_path: str) -> None:
        """
        Initialize UI controller and core game services.
        Инициализация UI-контроллера и базовых игровых сервисов.
        """
        super().__init__()

        self.game = GameService(data_path=data_path)

        self.current_question: Question | None = None
        self.last_question: Question | None = None
        self.current_question_resolved: bool = True
        self.current_team_id: int | None = None
        self.remaining_seconds: int = 0

        self.round_team_order: list[Team] = []
        self.round_turn_index: int = 0

        self.current_question_extra_time_seconds: int = 0
        self.current_question_penalty_percent: int = 0
        self.current_question_time_expired: bool = False

        self.extra_time_usage_by_round: dict[int, dict[int, dict[str, int | bool]]] = {}

        self.timer = QTimer(self)
        self.timer.setInterval(1000)
        self.timer.timeout.connect(self._on_timer_tick)

        self.wheel_audio_output = QAudioOutput(self)
        self.wheel_audio_output.setVolume(0.65)

        self.wheel_player = QMediaPlayer(self)
        self.wheel_player.setAudioOutput(self.wheel_audio_output)

        self.timer_tick_audio_output = QAudioOutput(self)
        self.timer_tick_audio_output.setVolume(0.90)

        self.timer_tick_player = QMediaPlayer(self)
        self.timer_tick_player.setAudioOutput(self.timer_tick_audio_output)
        self.timer_tick_player.setLoops(QMediaPlayer.Infinite)

        self.timer_heartbeat_audio_output = QAudioOutput(self)
        self.timer_heartbeat_audio_output.setVolume(0.85)

        self.timer_heartbeat_player = QMediaPlayer(self)
        self.timer_heartbeat_player.setAudioOutput(self.timer_heartbeat_audio_output)

        self.gong_audio_output = QAudioOutput(self)
        self.gong_audio_output.setVolume(1.0)

        self.gong_player = QMediaPlayer(self)
        self.gong_player.setAudioOutput(self.gong_audio_output)

        self.wheel_sound_path = Path("assets") / "wolf.mp3"
        self.timer_tick_sound_path = Path("assets") / "ticking-timer.mp3"
        self.timer_heartbeat_sound_path = Path("assets") / "human-single-heart-beat.wav"
        self.gong_sound_path = Path("assets") / "gong.mp3"

        self._timer_tick_loop_enabled = False

        self._gong_fade_timer = QTimer(self)
        self._gong_fade_timer.setInterval(50)
        self._gong_fade_timer.timeout.connect(self._process_gong_fade)

        self._gong_duration_ms = 0
        self._gong_elapsed_ms = 0
        self._gong_fade_start_ratio = 0.50
        self._gong_fade_end_ratio = 0.75

        self.active_video_mode: str | None = None
        self.answer_already_revealed: bool = False

        self.display_window = None

    def bind_display_window(self, display_window) -> None:
        """
        Bind public display window to controller.
        Привязать публичное окно отображения к контроллеру.
        """
        self.display_window = display_window
        self.video_state_changed.emit()
        self._emit_extra_time_state()

    def _save_all(self) -> None:
        """
        Persist all current game entities.
        Сохранить все текущие игровые сущности.
        """
        self.game.data_loader.save_all(
            settings=self.game.settings,
            teams=self.game.teams,
            rounds=self.game.rounds,
            questions=self.game.questions,
        )

    def _build_round_team_order(self) -> list[Team]:
        """
        Build alphabetical team order for active round.
        Построить алфавитный порядок команд для активного раунда.
        """
        return sorted(self.game.teams, key=lambda team: team.name.casefold())

    def _get_active_team(self) -> Team | None:
        """
        Return current answering team.
        Вернуть текущую отвечающую команду.
        """
        if not self.round_team_order:
            return None

        if self.round_turn_index < 0 or self.round_turn_index >= len(self.round_team_order):
            self.round_turn_index = 0

        return self.round_team_order[self.round_turn_index]

    def _get_next_team(self) -> Team | None:
        """
        Return next team in turn order.
        Вернуть следующую команду в очереди.
        """
        if not self.round_team_order:
            return None

        next_index = (self.round_turn_index + 1) % len(self.round_team_order)
        return self.round_team_order[next_index]

    def _advance_turn(self) -> None:
        """
        Move turn pointer to next team.
        Сдвинуть указатель хода на следующую команду.
        """
        if not self.round_team_order:
            return

        self.round_turn_index = (self.round_turn_index + 1) % len(self.round_team_order)
        self._emit_round_runtime_info()
        self._emit_extra_time_state()

    def _emit_round_runtime_info(self) -> None:
        """
        Emit current team, next team and round progress text.
        Отправить текущую команду, следующую команду и прогресс раунда.
        """
        active_team = self._get_active_team()
        next_team = self._get_next_team()

        self.active_team_changed.emit(
            active_team.name if active_team is not None else "Нет активной команды"
        )
        self.next_team_changed.emit(
            next_team.name if next_team is not None else "Нет следующей команды"
        )

        round_id = self.game.state.current_round_id
        if round_id is None:
            self.round_progress_changed.emit("Раунд не выбран")
            self._emit_extra_time_state()
            return

        unused_count = self.game.question_service.get_unused_count_by_round(round_id)
        total_count = len(self.game.question_service.get_questions_by_round(round_id))
        used_count = total_count - unused_count

        self.round_progress_changed.emit(
            f"Раунд: сыграно {used_count} из {total_count}, осталось {unused_count}"
        )
        self._emit_extra_time_state()

    def _start_wheel_sound(self) -> None:
        """
        Start wheel sound while spinning.
        Запустить звук волчка во время вращения.
        """
        if not self.wheel_sound_path.exists():
            self.status_changed.emit(
                f"Файл звука не найден: {self.wheel_sound_path.as_posix()}"
            )
            return

        source_url = QUrl.fromLocalFile(str(self.wheel_sound_path.resolve()))

        if self.wheel_player.source() != source_url:
            self.wheel_player.setSource(source_url)

        self.wheel_player.stop()
        self.wheel_player.play()

    def _stop_wheel_sound(self) -> None:
        """
        Stop wheel sound after spin is finished.
        Остановить звук волчка после завершения вращения.
        """
        self.wheel_player.stop()

    def _set_timer_tick_volume_for_seconds(self, seconds: int) -> None:
        """
        Set timer tick volume depending on remaining seconds.

        До 30 секунд тик тихий.
        С 30 до 6 секунд громкость увеличивается примерно на 20%.

        Настроить громкость тика таймера в зависимости от оставшегося времени.

        До 30 секунд тик тихий.
        С 30 до 6 секунд громкость увеличивается примерно на 20%.
        """
        base_volume = 0.10
        boosted_volume = base_volume * 1.20

        if seconds > 30:
            self.timer_tick_audio_output.setVolume(base_volume)
            return

        if 6 <= seconds <= 30:
            self.timer_tick_audio_output.setVolume(boosted_volume)
            return

        self.timer_tick_audio_output.setVolume(base_volume)

    def _start_timer_tick_loop(self) -> None:
        """
        Start quiet looping timer tick sound.
        Запустить зацикленное тихое тиканье таймера.
        """
        if not self.timer_tick_sound_path.exists():
            return

        source_url = QUrl.fromLocalFile(str(self.timer_tick_sound_path.resolve()))

        if self.timer_tick_player.source() != source_url:
            self.timer_tick_player.setSource(source_url)

        self._set_timer_tick_volume_for_seconds(self.remaining_seconds)
        self._timer_tick_loop_enabled = True

        if self.timer_tick_player.playbackState() != QMediaPlayer.PlayingState:
            self.timer_tick_player.play()

    def _stop_timer_tick_loop(self) -> None:
        """
        Stop looping timer tick sound.
        Остановить зацикленное тиканье таймера.
        """
        self._timer_tick_loop_enabled = False
        self.timer_tick_player.stop()

    def _play_timer_heartbeat_once(self) -> None:
        """
        Play heartbeat sound once.
        Проиграть один удар сердца.
        """
        if not self.timer_heartbeat_sound_path.exists():
            return

        source_url = QUrl.fromLocalFile(str(self.timer_heartbeat_sound_path.resolve()))

        if self.timer_heartbeat_player.source() != source_url:
            self.timer_heartbeat_player.setSource(source_url)

        self.timer_heartbeat_player.stop()
        self.timer_heartbeat_player.play()

    def _play_gong(self) -> None:
        """
        Play gong sound and fade it out programmatically.

        The gong starts at full volume.
        From 50% of its duration volume begins to fade out.
        By 75% of its duration the sound becomes fully silent and stops.

        Проиграть звук гонга и плавно затушить его программно.

        Гонг запускается на полной громкости.
        С 50% длительности начинается плавное затухание.
        К 75% длительности звук полностью затихает и останавливается.
        """
        if not self.gong_sound_path.exists():
            return

        source_url = QUrl.fromLocalFile(str(self.gong_sound_path.resolve()))

        if self.gong_player.source() != source_url:
            self.gong_player.setSource(source_url)

        self._stop_gong()

        self.gong_audio_output.setVolume(1.0)
        self._gong_elapsed_ms = 0
        self._gong_duration_ms = 0

        self.gong_player.play()

        QTimer.singleShot(120, self._start_gong_fade_logic)

    def _start_gong_fade_logic(self) -> None:
        """
        Start gong fade timer after media duration becomes available.
        Запустить таймер затухания гонга после получения длительности медиа.
        """
        duration = self.gong_player.duration()

        if duration <= 0:
            QTimer.singleShot(120, self._start_gong_fade_logic)
            return

        self._gong_duration_ms = duration
        self._gong_elapsed_ms = 0
        self._gong_fade_timer.start()

    def _process_gong_fade(self) -> None:
        """
        Process gong fade-out in real time.
        Обработать плавное затухание гонга в реальном времени.
        """
        if self._gong_duration_ms <= 0:
            self._stop_gong()
            return

        step_ms = self._gong_fade_timer.interval()
        self._gong_elapsed_ms += step_ms

        fade_start_ms = int(self._gong_duration_ms * self._gong_fade_start_ratio)
        fade_end_ms = int(self._gong_duration_ms * self._gong_fade_end_ratio)

        if self._gong_elapsed_ms < fade_start_ms:
            return

        if self._gong_elapsed_ms >= fade_end_ms:
            self.gong_audio_output.setVolume(0.0)
            self._stop_gong()
            return

        fade_range = max(fade_end_ms - fade_start_ms, 1)
        progress = (self._gong_elapsed_ms - fade_start_ms) / fade_range
        volume = 1.0 - progress

        self.gong_audio_output.setVolume(max(0.0, min(1.0, volume)))

    def _stop_gong(self) -> None:
        """
        Stop gong playback and fade timer.
        Остановить воспроизведение гонга и таймер затухания.
        """
        self._gong_fade_timer.stop()
        self.gong_player.stop()
        self.gong_audio_output.setVolume(1.0)
        self._gong_duration_ms = 0
        self._gong_elapsed_ms = 0

    def _stop_all_timer_sounds(self) -> None:
        """
        Stop all timer-related sounds.
        Остановить все звуки таймера.
        """
        self._stop_timer_tick_loop()
        self.timer_heartbeat_player.stop()
        self._stop_gong()

    def _sync_timer_sound_state(self) -> None:
        """
        Synchronize timer sound mode with current remaining seconds.
        Синхронизировать режим звука таймера с текущим остатком секунд.
        """
        if not self.timer.isActive():
            self._stop_all_timer_sounds()
            return

        if self.remaining_seconds <= 0:
            self._stop_all_timer_sounds()
            return

        if self.remaining_seconds <= 5:
            self._stop_timer_tick_loop()
            return

        self._set_timer_tick_volume_for_seconds(self.remaining_seconds)

        if not self._timer_tick_loop_enabled:
            self._start_timer_tick_loop()

    def _get_media_dir(self, question: Question | None) -> Path | None:
        """
        Return media directory for question.
        Вернуть папку медиа для вопроса.
        """
        if question is None:
            return None

        if question.media_type != "video":
            return None

        if not question.media_path:
            return None

        media_dir = Path(question.media_path)
        if not media_dir.exists() or not media_dir.is_dir():
            return None

        return media_dir

    def _get_question_video_path(self, question: Question | None) -> Path | None:
        """
        Return path to question video if exists.
        Вернуть путь к видео вопроса, если оно существует.
        """
        media_dir = self._get_media_dir(question)
        if media_dir is None:
            return None

        video_path = media_dir / self.QUESTION_VIDEO_NAME
        if video_path.exists():
            return video_path

        return None

    def _get_answer_video_path(self, question: Question | None) -> Path | None:
        """
        Return path to answer video if exists.
        Вернуть путь к видео ответа, если оно существует.
        """
        media_dir = self._get_media_dir(question)
        if media_dir is None:
            return None

        video_path = media_dir / self.ANSWER_VIDEO_NAME
        if video_path.exists():
            return video_path

        return None

    def _play_question_video(self, question: Question | None) -> bool:
        """
        Play question video if available.
        Проиграть видео вопроса, если оно доступно.
        """
        question_video_path = self._get_question_video_path(question)
        if question_video_path is None:
            return False

        self.active_video_mode = "question"
        self.video_requested.emit(
            {
                "path": str(question_video_path),
                "mode": "question",
            }
        )
        self.video_state_changed.emit()
        return True

    def _play_answer_video(self, question: Question | None) -> bool:
        """
        Play answer video if available.
        Проиграть видео ответа, если оно доступно.
        """
        answer_video_path = self._get_answer_video_path(question)
        if answer_video_path is None:
            return False

        self.active_video_mode = "answer"
        self.video_requested.emit(
            {
                "path": str(answer_video_path),
                "mode": "answer",
            }
        )
        self.video_state_changed.emit()
        return True

    def _reveal_answer(self, question: Question | None) -> None:
        """
        Reveal answer as text or response video depending on question media.
        Показать ответ текстом или через видеоответ в зависимости от медиа вопроса.
        """
        if question is None:
            self.status_changed.emit("Нет вопроса для показа ответа.")
            return

        self.last_question = question
        self.answer_already_revealed = True

        answer_text = (question.answer or "").strip()
        if answer_text:
            self.answer_requested.emit(answer_text)

        if self._play_answer_video(question):
            self.status_changed.emit("Запущен видеоответ.")
            return

        if answer_text:
            self.public_answer_requested.emit(answer_text)
            self.status_changed.emit("Ответ показан.")
            self.video_state_changed.emit()
            return

        self.public_answer_requested.emit("Ответ не указан.")
        self.status_changed.emit("Видеоответ отсутствует, текст ответа не задан.")
        self.video_state_changed.emit()

    def _get_current_round_extra_time_bucket(self) -> dict[int, dict[str, int | bool]]:
        """
        Return extra-time usage bucket for current round.
        Вернуть корзину использования допвремени для текущего раунда.
        """
        round_id = self.game.state.current_round_id
        if round_id is None:
            return {}

        if round_id not in self.extra_time_usage_by_round:
            self.extra_time_usage_by_round[round_id] = {}

        return self.extra_time_usage_by_round[round_id]

    def _get_team_extra_time_usage(self, team_id: int | None) -> dict[str, int | bool] | None:
        """
        Return extra-time usage for team in current round.
        Вернуть использование допвремени команды в текущем раунде.
        """
        if team_id is None:
            return None

        bucket = self._get_current_round_extra_time_bucket()
        return bucket.get(team_id)

    def _get_current_award_ratio(self) -> float:
        """
        Return award multiplier for current question.
        Вернуть множитель награды для текущего вопроса.
        """
        if self.current_question is None:
            return 0.0

        if self.current_question_time_expired:
            return 0.05

        if self.current_question_penalty_percent > 0:
            return max(0.0, (100 - self.current_question_penalty_percent) / 100.0)

        return 1.0

    def _get_current_award_points(self) -> int:
        """
        Return effective award points for current question.
        Вернуть фактическую награду в очках для текущего вопроса.
        """
        if self.current_question is None:
            return 0

        base_points = max(int(self.current_question.points), 0)
        ratio = self._get_current_award_ratio()

        if base_points <= 0:
            return 0

        value = round(base_points * ratio)
        return max(1, value)

    def _build_extra_time_state_payload(self) -> dict:
        """
        Build payload for extra-time UI synchronization.
        Построить payload для синхронизации UI допвремени.
        """
        round_id = self.game.state.current_round_id
        active_team = self._get_active_team()

        team_states = []
        bucket = self._get_current_round_extra_time_bucket() if round_id is not None else {}

        for team in self.get_all_teams():
            team_usage = bucket.get(team.id)
            used = team_usage is not None

            team_states.append(
                {
                    "team_id": team.id,
                    "team_name": team.name,
                    "used": used,
                    "bonus_seconds": int(team_usage["bonus_seconds"]) if used else 0,
                    "penalty_percent": int(team_usage["penalty_percent"]) if used else 0,
                    "is_active": active_team is not None and team.id == active_team.id,
                }
            )

        base_points = int(self.current_question.points) if self.current_question is not None else 0
        award_points = self._get_current_award_points()

        if self.current_question_time_expired:
            award_percent = 5
        elif self.current_question_penalty_percent > 0:
            award_percent = 100 - self.current_question_penalty_percent
        else:
            award_percent = 100 if self.current_question is not None else 0

        return {
            "round_id": round_id,
            "active_team_id": active_team.id if active_team is not None else None,
            "active_team_name": active_team.name if active_team is not None else "Нет активной команды",
            "base_points": base_points,
            "award_points": award_points,
            "award_percent": award_percent,
            "time_expired": self.current_question_time_expired,
            "selected_bonus_seconds": self.current_question_extra_time_seconds,
            "selected_penalty_percent": self.current_question_penalty_percent,
            "team_states": team_states,
            "available_bonus_seconds": list(self.EXTRA_TIME_RULES.keys()),
        }

    def _emit_extra_time_state(self) -> None:
        """
        Emit extra-time UI state.
        Отправить UI-состояние допвремени.
        """
        self.extra_time_state_changed.emit(self._build_extra_time_state_payload())

    def apply_extra_time(self, bonus_seconds: int) -> None:
        """
        Apply additional time for active team once per round.

        Award penalty is calculated from base question points.
        Extra time can be used only once per team in the current round.

        Применить дополнительное время для активной команды один раз за раунд.

        Штраф к награде считается от базовой стоимости вопроса.
        Допвремя можно использовать только один раз на команду в текущем раунде.
        """
        if bonus_seconds not in self.EXTRA_TIME_RULES:
            self.status_changed.emit("Недопустимый тип дополнительного времени.")
            return

        round_id = self.game.state.current_round_id
        if round_id is None:
            self.status_changed.emit("Сначала выбери раунд.")
            return

        if self.current_question is None or self.current_question_resolved:
            self.status_changed.emit("Нет активного вопроса для добавления времени.")
            return

        if self.current_team_id is None:
            self.status_changed.emit("Нет активной команды для добавления времени.")
            return

        if self.current_question_time_expired:
            self.status_changed.emit("Время уже вышло. Дополнительное время больше недоступно.")
            return

        if self.remaining_seconds <= 0 and not self.timer.isActive():
            self.status_changed.emit("Сначала запусти таймер, затем добавляй время.")
            return

        bucket = self._get_current_round_extra_time_bucket()
        if self.current_team_id in bucket:
            team = self.get_team_by_id(self.current_team_id)
            team_name = team.name if team is not None else f"id={self.current_team_id}"
            self.status_changed.emit(
                f"Команда '{team_name}' уже использовала дополнительное время в этом раунде."
            )
            self._emit_extra_time_state()
            return

        penalty_percent = self.EXTRA_TIME_RULES[bonus_seconds]

        self.remaining_seconds += bonus_seconds
        self.current_question_extra_time_seconds = bonus_seconds
        self.current_question_penalty_percent = penalty_percent

        bucket[self.current_team_id] = {
            "used": True,
            "bonus_seconds": bonus_seconds,
            "penalty_percent": penalty_percent,
        }

        self.timer_updated.emit(self.remaining_seconds)
        self._sync_timer_sound_state()

        team = self.get_team_by_id(self.current_team_id)
        team_name = team.name if team is not None else f"id={self.current_team_id}"

        self.status_changed.emit(
            f"Команде '{team_name}' добавлено {bonus_seconds} сек. "
            f"Награда за вопрос теперь {100 - penalty_percent}% "
            f"от базовой стоимости."
        )
        self._emit_extra_time_state()

    def clear_active_question_state(self) -> None:
        """
        Clear active runtime state of current question.
        Очистить runtime-состояние активного текущего вопроса.
        """
        self.timer.stop()
        self._stop_wheel_sound()
        self._stop_all_timer_sounds()

        if self.display_window is not None:
            self.display_window.stop_video()

        self.current_question = None
        self.current_question_resolved = True
        self.current_team_id = None
        self.remaining_seconds = 0
        self.active_video_mode = None
        self.answer_already_revealed = False

        self.current_question_extra_time_seconds = 0
        self.current_question_penalty_percent = 0
        self.current_question_time_expired = False

        self.timer_updated.emit(0)
        self.timer_stopped.emit()
        self.video_state_changed.emit()
        self._emit_extra_time_state()

    def select_round(self, round_id: int | None) -> None:
        """
        Set current round manually from admin window.
        Установить текущий раунд вручную из окна администратора.
        """
        if round_id is None:
            self.game.state.current_round_id = None
            self.clear_active_question_state()
            self.round_title_changed.emit("Раунд не выбран")
            self.status_changed.emit("Раунд не выбран.")
            self._emit_round_runtime_info()
            self._emit_extra_time_state()
            return

        self.clear_active_question_state()

        self.game.state.current_round_id = round_id
        self.round_team_order = self._build_round_team_order()
        self.round_turn_index = 0

        round_name = next(
            (round_item.name for round_item in self.game.rounds if round_item.id == round_id),
            f"Раунд {round_id}",
        )

        self.round_title_changed.emit(round_name)
        self.status_changed.emit(f"Выбран раунд: {round_name}")
        self._emit_round_runtime_info()
        self._emit_extra_time_state()

    def spin_next_question(self) -> None:
        """
        Select next question for current round and current team in queue.
        Выбрать следующий вопрос текущего раунда для текущей команды по очереди.
        """
        round_id = self.game.state.current_round_id
        if round_id is None:
            self.status_changed.emit("Сначала выбери раунд.")
            return

        if not self.current_question_resolved:
            self.status_changed.emit("Сначала заверши текущий вопрос.")
            return

        if not self.round_team_order:
            self.round_team_order = self._build_round_team_order()
            self.round_turn_index = 0

        active_team = self._get_active_team()
        if active_team is None:
            self.status_changed.emit("Нет доступных команд.")
            return

        available_questions = self.game.question_service.get_available_questions(round_id=round_id)
        if not available_questions:
            self.status_changed.emit("В этом раунде больше нет доступных вопросов.")
            return

        selected_question = self.game.question_service.pick_random_question(round_id=round_id)
        if selected_question is None:
            self.status_changed.emit("Не удалось выбрать вопрос.")
            return

        self.current_question = selected_question
        self.last_question = selected_question
        self.current_question_resolved = False
        self.current_team_id = active_team.id
        self.active_video_mode = None
        self.answer_already_revealed = False
        self.remaining_seconds = 0

        self.current_question_extra_time_seconds = 0
        self.current_question_penalty_percent = 0
        self.current_question_time_expired = False

        self.game.state.current_team_id = active_team.id
        self.game.state.current_question_id = selected_question.id

        labels = self.game.wheel_service.build_wheel_labels(available_questions)
        target_index = self.game.wheel_service.pick_target_index(
            questions=available_questions,
            target_question_id=selected_question.id,
        )

        self._start_wheel_sound()
        self.wheel_spin_requested.emit(labels, target_index)
        self.status_changed.emit(f"Колесо вращается. Отвечает команда: {active_team.name}")
        self._emit_round_runtime_info()
        self.video_state_changed.emit()
        self._emit_extra_time_state()

    def on_public_wheel_finished(self) -> None:
        """
        Reveal selected question after public wheel animation.
        Показать выбранный вопрос после завершения публичной анимации колеса.
        """
        self._stop_wheel_sound()

        if self.current_question is None:
            return

        self.question_selected.emit(self.current_question)
        self.last_question = self.current_question

        team = self._get_active_team()
        if team is not None:
            self.status_changed.emit(f"Вопрос показан. Отвечает команда: {team.name}")
        else:
            self.status_changed.emit("Вопрос показан.")

        if self.current_question.media_type == "video":
            if self._play_question_video(self.current_question):
                self.status_changed.emit("Запущен видеовопрос.")
            else:
                self.status_changed.emit(
                    "У видеовопроса не найден файл video_secret.mp4."
                )
                self.video_state_changed.emit()
        else:
            self.video_state_changed.emit()

        self._emit_extra_time_state()

    def on_video_finished(self) -> None:
        """
        Handle finished video depending on current video mode.
        Обработать завершение видео в зависимости от текущего режима.
        """
        finished_mode = self.active_video_mode
        self.active_video_mode = None
        self.video_state_changed.emit()

        if finished_mode == "question":
            self.status_changed.emit("Видео вопроса завершено. Таймер запускается автоматически.")
            self.start_timer()
            return

        if finished_mode == "answer":
            self.status_changed.emit("Видео ответа завершено.")
            return

        self.status_changed.emit("Видео завершено.")

    def repeat_question(self) -> None:
        """
        Repeat current question text or replay question video.
        Повторно показать текущий вопрос или заново проиграть видео вопроса.
        """
        question = self.current_question or self.last_question
        if question is None:
            self.status_changed.emit("Нет активного вопроса для повтора.")
            return

        self.question_selected.emit(question)

        if question.media_type == "video":
            self.pause_timer()
            if self._play_question_video(question):
                self.status_changed.emit("Видеовопрос запущен повторно.")
                return

        self.status_changed.emit("Вопрос повторен.")
        self.video_state_changed.emit()

    def show_answer(self) -> None:
        """
        Show answer for current or last question.
        Показать ответ на текущий или последний вопрос.
        """
        question = self.current_question or self.last_question
        self._reveal_answer(question)

    def start_timer(self) -> None:
        """
        Start or resume timer for current question.
        Запустить или продолжить таймер для текущего вопроса.
        """
        if self.current_question is None:
            self.status_changed.emit("Нет активного вопроса для запуска таймера.")
            return

        if self.current_question_time_expired and self.remaining_seconds <= 0:
            self.status_changed.emit("Время по этому вопросу уже истекло. Повторный запуск недоступен.")
            return

        if self.remaining_seconds <= 0:
            self.remaining_seconds = self.game.question_service.get_question_timer(
                self.current_question
            )
            self.timer_updated.emit(self.remaining_seconds)

        self.timer.start()
        self._sync_timer_sound_state()

        if 0 < self.remaining_seconds <= 5:
            self._play_timer_heartbeat_once()

        self.timer_started.emit()
        self.status_changed.emit("Таймер запущен.")
        self._emit_extra_time_state()

    def pause_timer(self) -> None:
        """
        Pause active timer.
        Поставить активный таймер на паузу.
        """
        if self.timer.isActive():
            self.timer.stop()
            self._stop_all_timer_sounds()
            self.timer_paused.emit()
            self.status_changed.emit("Таймер поставлен на паузу.")
            self._emit_extra_time_state()

    def stop_timer(self) -> None:
        """
        Stop timer and reset current countdown value.

        If question time already expired, keep zero to prevent abuse.
        Если время по вопросу уже истекло, сохранить ноль, чтобы нельзя было обойти правило.
        """
        self.timer.stop()
        self._stop_all_timer_sounds()

        if self.current_question_time_expired:
            self.remaining_seconds = 0
        elif self.current_question is not None:
            self.remaining_seconds = self.game.question_service.get_question_timer(
                self.current_question
            )
        else:
            self.remaining_seconds = 0

        self.timer_updated.emit(self.remaining_seconds)
        self.timer_stopped.emit()
        self.status_changed.emit("Таймер остановлен.")
        self._emit_extra_time_state()

    def is_video_question_context(self) -> bool:
        """
        Check whether current context is a video question.
        Проверить, относится ли текущий контекст к видеовопросу.
        """
        question = self.current_question or self.last_question
        if question is None:
            return False
        return question.media_type == "video"

    def is_video_visible_now(self) -> bool:
        """
        Check whether video is currently visible on display window.
        Проверить, показывается ли сейчас видео в публичном окне.
        """
        if self.display_window is None:
            return False
        return self.display_window.video_widget.isVisible()

    def is_video_paused(self) -> bool:
        """
        Check whether current public video is paused.
        Проверить, находится ли текущее публичное видео на паузе.
        """
        if self.display_window is None:
            return False
        return self.display_window.video_widget.player.playbackState() == QMediaPlayer.PausedState

    def toggle_video_pause_resume(self) -> None:
        """
        Toggle pause/resume for current public video.
        Переключить паузу/продолжение текущего публичного видео.
        """
        if not self.is_video_question_context():
            self.status_changed.emit("Текущий вопрос не является видеовопросом.")
            self.video_state_changed.emit()
            return

        if self.display_window is None or not self.is_video_visible_now():
            self.status_changed.emit("Сейчас видео не воспроизводится.")
            self.video_state_changed.emit()
            return

        if self.is_video_paused():
            self.display_window.resume_video()
            self.status_changed.emit("Видео продолжено.")
        else:
            self.display_window.pause_video()
            self.status_changed.emit("Видео поставлено на паузу.")

        self.video_state_changed.emit()

    def mark_correct(self) -> None:
        """
        Mark answer as correct and award points.
        If answer was not shown before, reveal it once.
        Отметить ответ как верный и начислить очки.
        Если ответ еще не показывался, показать его один раз.
        """
        if self.current_question is None or self.current_team_id is None:
            self.status_changed.emit("Нет активного вопроса или команды.")
            return

        if self.current_question_resolved:
            self.status_changed.emit("Этот вопрос уже завершен.")
            return

        self.timer.stop()
        self._stop_all_timer_sounds()
        self.timer_stopped.emit()

        if not self.answer_already_revealed:
            self._reveal_answer(self.current_question)

        awarded_points = self._get_current_award_points()
        self.game.score_service.add_points(self.current_team_id, awarded_points)
        self.game.state.last_result_correct = True

        if self.current_question_time_expired:
            status_text = (
                f"Ответ засчитан после истечения времени. "
                f"Начислено {awarded_points} очков (5% от базовой награды)."
            )
        elif self.current_question_penalty_percent > 0:
            status_text = (
                f"Ответ засчитан. Начислено {awarded_points} очков "
                f"({100 - self.current_question_penalty_percent}% от базовой награды)."
            )
        else:
            status_text = f"Ответ засчитан. Начислено {awarded_points} очков."

        self._finalize_current_question(status_text)

    def mark_wrong(self) -> None:
        """
        Mark answer as incorrect.
        If answer was not shown before, reveal it once.
        Отметить ответ как неверный.
        Если ответ еще не показывался, показать его один раз.
        """
        if self.current_question is None:
            self.status_changed.emit("Нет активного вопроса.")
            return

        if self.current_question_resolved:
            self.status_changed.emit("Этот вопрос уже завершен.")
            return

        self.timer.stop()
        self._stop_all_timer_sounds()
        self.timer_stopped.emit()

        if not self.answer_already_revealed:
            self._reveal_answer(self.current_question)

        self.game.state.last_result_correct = False
        self._finalize_current_question("Ответ не засчитан.")

    def _finalize_current_question(self, status_text: str) -> None:
        """
        Finalize current question and persist updated state.
        Завершить текущий вопрос и сохранить обновленное состояние.
        """
        if self.current_question is None:
            return

        finished_question_id = self.current_question.id
        finished_round_id = self.game.state.current_round_id
        finished_team_id = self.current_team_id
        awarded_points = self._get_current_award_points() if self.game.state.last_result_correct else 0

        self.game.question_service.mark_used(finished_question_id)

        self.game.state.history.append(
            (
                f"round={finished_round_id}; "
                f"team={finished_team_id}; "
                f"question={finished_question_id}; "
                f"media={getattr(self.current_question, 'media_type', None)}; "
                f"correct={self.game.state.last_result_correct}; "
                f"extra_time={self.current_question_extra_time_seconds}; "
                f"penalty_percent={self.current_question_penalty_percent}; "
                f"time_expired={self.current_question_time_expired}; "
                f"awarded_points={awarded_points}"
            )
        )

        self._save_all()
        self.scoreboard_changed.emit(self.game.teams)

        self.current_question_resolved = True
        self.current_question = None
        self.current_team_id = None
        self.remaining_seconds = 0
        self.active_video_mode = None

        self.current_question_extra_time_seconds = 0
        self.current_question_penalty_percent = 0
        self.current_question_time_expired = False

        self._stop_all_timer_sounds()
        self.timer_updated.emit(0)
        self.timer_stopped.emit()
        self.video_state_changed.emit()

        self._advance_turn()
        self.questions_changed.emit()
        self._emit_extra_time_state()

        if finished_round_id is not None:
            if self.game.question_service.get_unused_count_by_round(finished_round_id) == 0:
                self.status_changed.emit(
                    f"{status_text} Раунд завершен, вопросы закончились."
                )
                self._emit_round_runtime_info()
                return

        self.status_changed.emit(status_text)

    def _on_timer_tick(self) -> None:
        """
        Tick timer down by one second.
        Уменьшить таймер на одну секунду.
        """
        self.remaining_seconds -= 1
        current_value = max(self.remaining_seconds, 0)

        self.timer_updated.emit(current_value)

        if 0 < current_value <= 5:
            self._stop_timer_tick_loop()
            self._play_timer_heartbeat_once()
        elif current_value > 5:
            self._sync_timer_sound_state()

        if self.remaining_seconds <= 0:
            self.remaining_seconds = 0
            self.current_question_time_expired = True
            self.timer.stop()
            self._stop_all_timer_sounds()
            self._play_gong()
            self.timer_stopped.emit()
            self.status_changed.emit("Время вышло.")
            self._emit_extra_time_state()

    def get_questions_for_round(self, round_id: int | None = None) -> list[Question]:
        """
        Return questions for admin list.
        Вернуть вопросы для списка администратора.
        """
        return self.game.question_service.get_questions_by_round(round_id)

    def save_questions_state(self) -> None:
        """
        Persist current questions and related state.
        Сохранить текущее состояние вопросов и связанных данных.
        """
        self._save_all()
        self.questions_changed.emit()
        self._emit_round_runtime_info()
        self._emit_extra_time_state()

    def reset_current_question(self, question_id: int) -> None:
        """
        Reset selected question to unused state.
        Сбросить выбранный вопрос в состояние неиспользованного.
        """
        self.game.question_service.reset_question(question_id)

        if self.current_question is not None and self.current_question.id == question_id:
            self.clear_active_question_state()

        self.save_questions_state()
        self.status_changed.emit(f"Вопрос #{question_id} сброшен.")

    def reset_round_questions(self, round_id: int) -> None:
        """
        Reset all questions in selected round.
        Сбросить все вопросы выбранного раунда.
        """
        count = self.game.question_service.reset_round_questions(round_id)

        if self.current_question is not None and self.current_question.round_id == round_id:
            self.clear_active_question_state()

        if self.game.state.current_round_id == round_id:
            self.round_team_order = self._build_round_team_order()
            self.round_turn_index = 0

        if round_id in self.extra_time_usage_by_round:
            self.extra_time_usage_by_round[round_id].clear()

        self.save_questions_state()
        self.status_changed.emit(
            f"Сброшено вопросов в раунде: {count}. Дополнительное время раунда также очищено."
        )
        self._emit_extra_time_state()

    def reset_all_questions(self) -> None:
        """
        Reset all questions in game.
        Сбросить все вопросы игры.
        """
        count = self.game.question_service.reset_all_questions()
        self.clear_active_question_state()

        if self.game.state.current_round_id is not None:
            self.round_team_order = self._build_round_team_order()
            self.round_turn_index = 0

        self.extra_time_usage_by_round.clear()

        self.save_questions_state()
        self.status_changed.emit(
            f"Сброшено всех вопросов: {count}. Состояние дополнительного времени очищено."
        )
        self._emit_extra_time_state()

    def set_question_used(self, question_id: int, used: bool) -> None:
        """
        Update question used flag and persist changes.
        Обновить флаг used вопроса и сохранить изменения.
        """
        self.game.question_service.set_used(question_id, used)

        if (
            self.current_question is not None
            and self.current_question.id == question_id
            and not used
        ):
            self.current_question_resolved = False

        self.save_questions_state()
        state_text = "закрыт" if used else "открыт"
        self.status_changed.emit(f"Вопрос #{question_id} теперь {state_text}.")

    def add_manual_points(self, team_id: int | None, points: int) -> None:
        """
        Add points to selected team manually.
        Добавить очки выбранной команде вручную.
        """
        if team_id is None:
            self.status_changed.emit("Команда для начисления не выбрана.")
            return

        if points <= 0:
            self.status_changed.emit("Количество очков должно быть больше нуля.")
            return

        self.game.score_service.add_points(team_id, points)
        self._save_all()
        self.scoreboard_changed.emit(self.game.teams)

        team = self.game.score_service.get_team_by_id(team_id)
        self.status_changed.emit(
            f"Команде '{team.name}' начислено {points} очков вручную."
        )

    def remove_manual_points(self, team_id: int | None, points: int) -> None:
        """
        Remove points from selected team manually.
        Списать очки у выбранной команды вручную.
        """
        if team_id is None:
            self.status_changed.emit("Команда для списания не выбрана.")
            return

        if points <= 0:
            self.status_changed.emit("Количество очков должно быть больше нуля.")
            return

        self.game.score_service.remove_points(team_id, points)
        self._save_all()
        self.scoreboard_changed.emit(self.game.teams)

        team = self.game.score_service.get_team_by_id(team_id)
        self.status_changed.emit(
            f"У команды '{team.name}' списано {points} очков вручную."
        )

    def add_question(self, payload: dict) -> None:
        """
        Create and store new question from dialog payload.
        Создать и сохранить новый вопрос из payload диалога.
        """
        question = Question(
            id=get_next_id(self.game.questions),
            round_id=payload["round_id"],
            team_id=None,
            text=payload["text"],
            answer=payload["answer"],
            timer_seconds=payload["timer_seconds"],
            points=payload["points"],
            used=payload["used"],
            category=payload["category"],
            difficulty=payload["difficulty"],
            media_type=payload["media_type"],
            media_path=payload["media_path"],
        )

        self.game.question_service.add_question(question)
        self.save_questions_state()
        self.status_changed.emit(f"Добавлен вопрос #{question.id}.")

    def update_question(self, question_id: int, payload: dict) -> None:
        """
        Update existing question and persist changes.
        Обновить существующий вопрос и сохранить изменения.
        """
        question = self.game.question_service.update_question(question_id, payload)

        if self.current_question is not None and self.current_question.id == question_id:
            self.current_question = question

        if self.last_question is not None and self.last_question.id == question_id:
            self.last_question = question

        self.save_questions_state()
        self.status_changed.emit(f"Вопрос #{question_id} обновлен.")

    def delete_question(self, question_id: int) -> None:
        """
        Delete question and persist changes.
        Active question cannot be deleted during game flow.
        Удалить вопрос и сохранить изменения.
        Активный вопрос нельзя удалить во время игрового хода.
        """
        if self.current_question is not None and self.current_question.id == question_id:
            self.status_changed.emit(
                "Нельзя удалить вопрос, который сейчас участвует в игровом ходе."
            )
            return

        removed_question = self.game.question_service.delete_question(question_id)

        if self.last_question is not None and self.last_question.id == question_id:
            self.last_question = None

        self.save_questions_state()
        self.status_changed.emit(f"Вопрос #{removed_question.id} удален.")

    def get_question_by_id(self, question_id: int) -> Question | None:
        """
        Return question by identifier for UI helpers.
        Вернуть вопрос по идентификатору для UI-хелперов.
        """
        return self.game.question_service.get_question_by_id(question_id)

    def get_all_teams(self) -> list[Team]:
        """
        Return all teams.
        Вернуть все команды.
        """
        return self.game.team_service.get_all()

    def get_team_by_id(self, team_id: int) -> Team | None:
        """
        Return team by identifier.
        Вернуть команду по идентификатору.
        """
        return self.game.team_service.get_by_id(team_id)

    def reset_all_scores(self) -> None:
        """
        Reset scores of all teams to zero.
        Сбросить очки всех команд до нуля.
        """
        for team in self.game.teams:
            team.score = 0

        self._save_all()
        self.scoreboard_changed.emit(self.game.teams)
        self.teams_changed.emit()
        self.status_changed.emit("Очки всех команд сброшены.")

    def add_team(self, name: str) -> None:
        """
        Create and store a new team.
        Создать и сохранить новую команду.
        """
        normalized_name = (name or "").strip()
        if not normalized_name:
            self.status_changed.emit("Название команды не может быть пустым.")
            return

        if len(self.game.teams) >= self.MAX_TEAMS:
            self.status_changed.emit("Нельзя добавить больше 4 команд.")
            return

        if any(team.name.casefold() == normalized_name.casefold() for team in self.game.teams):
            self.status_changed.emit("Команда с таким названием уже существует.")
            return

        team = Team(id=get_next_id(self.game.teams), name=normalized_name, score=0)
        self.game.team_service.add_team(team)
        self._save_all()

        self.round_team_order = self._build_round_team_order()
        self.round_turn_index = 0

        self.scoreboard_changed.emit(self.game.teams)
        self.teams_changed.emit()
        self._emit_round_runtime_info()
        self._emit_extra_time_state()
        self.status_changed.emit(f"Команда '{team.name}' добавлена.")

    def update_team(self, team_id: int, name: str) -> None:
        """
        Update existing team name.
        Обновить имя существующей команды.
        """
        normalized_name = (name or "").strip()
        if not normalized_name:
            self.status_changed.emit("Название команды не может быть пустым.")
            return

        if any(
            team.id != team_id and team.name.casefold() == normalized_name.casefold()
            for team in self.game.teams
        ):
            self.status_changed.emit("Команда с таким названием уже существует.")
            return

        team = self.game.team_service.update_team(team_id, normalized_name)
        self._save_all()

        self.round_team_order = self._build_round_team_order()
        self.round_turn_index = 0

        self.scoreboard_changed.emit(self.game.teams)
        self.teams_changed.emit()
        self._emit_round_runtime_info()
        self._emit_extra_time_state()
        self.status_changed.emit(f"Команда #{team.id} обновлена.")

    def delete_team(self, team_id: int) -> None:
        """
        Delete existing team.
        Удалить существующую команду.
        """
        if self.current_question is not None and self.current_team_id == team_id:
            self.status_changed.emit(
                "Нельзя удалить команду, которая сейчас отвечает на активный вопрос."
            )
            return

        removed_team = self.game.team_service.delete_team(team_id)
        self._save_all()

        self.round_team_order = self._build_round_team_order()
        self.round_turn_index = 0

        if self.current_team_id == team_id:
            self.current_team_id = None
            self.game.state.current_team_id = None

        for round_bucket in self.extra_time_usage_by_round.values():
            if team_id in round_bucket:
                del round_bucket[team_id]

        self.scoreboard_changed.emit(self.game.teams)
        self.teams_changed.emit()
        self._emit_round_runtime_info()
        self._emit_extra_time_state()
        self.status_changed.emit(f"Команда '{removed_team.name}' удалена.")

    def get_all_rounds(self) -> list[Round]:
        """
        Return all rounds.
        Вернуть все раунды.
        """
        return self.game.round_service.get_all()

    def get_round_by_id(self, round_id: int) -> Round | None:
        """
        Return round by identifier.
        Вернуть раунд по идентификатору.
        """
        return self.game.round_service.get_by_id(round_id)

    def add_round(self, name: str) -> None:
        """
        Create and store a new round.
        Создать и сохранить новый раунд.
        """
        normalized_name = (name or "").strip()
        if not normalized_name:
            self.status_changed.emit("Название раунда не может быть пустым.")
            return

        if any(
            round_item.name.casefold() == normalized_name.casefold()
            for round_item in self.game.rounds
        ):
            self.status_changed.emit("Раунд с таким названием уже существует.")
            return

        round_item = Round(id=get_next_id(self.game.rounds), name=normalized_name)
        self.game.round_service.add_round(round_item)
        self._save_all()

        self.rounds_changed.emit()
        self.status_changed.emit(f"Раунд '{round_item.name}' добавлен.")

        if self.game.state.current_round_id is None:
            self.select_round(round_item.id)

    def update_round(self, round_id: int, name: str) -> None:
        """
        Update existing round name.
        Обновить имя существующего раунда.
        """
        normalized_name = (name or "").strip()
        if not normalized_name:
            self.status_changed.emit("Название раунда не может быть пустым.")
            return

        if any(
            round_item.id != round_id and round_item.name.casefold() == normalized_name.casefold()
            for round_item in self.game.rounds
        ):
            self.status_changed.emit("Раунд с таким названием уже существует.")
            return

        round_item = self.game.round_service.update_round(round_id, normalized_name)
        self._save_all()

        self.rounds_changed.emit()
        if self.game.state.current_round_id == round_id:
            self.round_title_changed.emit(round_item.name)
        self.status_changed.emit(f"Раунд #{round_item.id} обновлен.")
        self._emit_extra_time_state()

    def delete_round(self, round_id: int) -> None:
        """
        Delete existing round if it has no questions.
        Удалить существующий раунд, если у него нет вопросов.
        """
        if self.current_question is not None and self.current_question.round_id == round_id:
            self.status_changed.emit(
                "Нельзя удалить раунд, в котором сейчас идет активный вопрос."
            )
            return

        if self.game.question_service.get_questions_by_round(round_id):
            self.status_changed.emit(
                "Нельзя удалить раунд, пока в нем есть вопросы. Сначала удали или перенеси вопросы."
            )
            return

        removed_round = self.game.round_service.delete_round(round_id)
        self._save_all()

        if round_id in self.extra_time_usage_by_round:
            del self.extra_time_usage_by_round[round_id]

        if self.game.state.current_round_id == round_id:
            remaining_rounds = self.get_all_rounds()
            if remaining_rounds:
                self.select_round(remaining_rounds[0].id)
            else:
                self.select_round(None)

        self.rounds_changed.emit()
        self.status_changed.emit(f"Раунд '{removed_round.name}' удален.")
        self._emit_extra_time_state()

    def get_active_team_name(self) -> str:
        """
        Return active team display name.
        Вернуть имя текущей активной команды.
        """
        active_team = self._get_active_team()
        if active_team is None:
            return "Нет активной команды"
        return active_team.name

    def get_next_team_name(self) -> str:
        """
        Return next team display name.
        Вернуть имя следующей команды.
        """
        next_team = self._get_next_team()
        if next_team is None:
            return "Нет следующей команды"
        return next_team.name


def run_app() -> int:
    """
    Create application and initialize windows.
    Создать приложение и инициализировать окна.
    """
    app = QApplication([])
    app.setStyleSheet(APP_STYLESHEET)

    controller = GameController(data_path="data/game_data.json")
    display_window = DisplayWindow()
    controller.bind_display_window(display_window)

    admin_window = AdminWindow(controller=controller)

    controller.scoreboard_changed.connect(display_window.update_scores)
    controller.round_title_changed.connect(display_window.set_round_title)
    controller.status_changed.connect(display_window.set_status)
    controller.question_selected.connect(display_window.show_question)

    controller.answer_requested.connect(admin_window._show_answer)
    controller.public_answer_requested.connect(display_window.show_answer)

    controller.timer_updated.connect(display_window.timer_widget.set_seconds)
    controller.timer_started.connect(display_window.timer_widget.set_running)
    controller.timer_paused.connect(display_window.timer_widget.set_paused)
    controller.timer_stopped.connect(display_window.timer_widget.set_stopped)
    controller.video_requested.connect(display_window.play_video)
    controller.extra_time_state_changed.connect(display_window.update_extra_time_state)

    controller.wheel_spin_requested.connect(
        lambda labels, index: display_window.start_wheel_animation(
            {"labels": labels, "target_index": index}
        )
    )

    display_window.public_wheel_finished.connect(controller.on_public_wheel_finished)
    display_window.video_finished.connect(controller.on_video_finished)

    controller.scoreboard_changed.emit(controller.game.teams)
    controller._emit_extra_time_state()

    if controller.game.rounds:
        first_round_id = controller.game.rounds[0].id
        controller.select_round(first_round_id)
        admin_window.round_combo.setCurrentIndex(0)
    else:
        controller.round_title_changed.emit("Раунды отсутствуют")
        controller.status_changed.emit("Сначала добавь раунды и вопросы в настройках игры.")
        controller._emit_extra_time_state()

    admin_window.show()
    display_window.hide()

    return app.exec()