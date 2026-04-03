import time


class TimerService:
    """
    Countdown timer service for quiz questions.
    Сервис обратного отсчета для вопросов викторины.
    """

    def run_timer(self, seconds: int) -> None:
        """
        Run console countdown timer.
        Запустить консольный обратный отсчет.
        """
        for remaining in range(seconds, 0, -1):
            print(f"\rОсталось времени: {remaining:02d} сек.", end="", flush=True)
            time.sleep(1)

        print("\rВремя вышло!                 ")