import time
from typing import Optional

# Timer class
class TimerError(Exception):
    """A custom exception used to report errors in use of Timer class."""


#TODO: this is placed here temporarily. It's a part of what should be control logic and 
# instances passed or built (builder) based on control flow settings.
# currently this is dynamic and created in specific functional logic.
class TimerNames(Enum):
    ProcessTimer = "process_timer"
    AutogenerationLoopTimer = "autogeneration_loop_timer"
    generationStartTime = "generation_start_time"
    lastGenerationTime = "last_generation_time"
    
    
class Timer:
    """create a master timer object that holds child-timers.
    Inspiration from codetiming: https://github.com/realpython/codetiming/tree/main"""

    class timer:
        """a child timer object."""

        def __init__(self, logger=None, name=None, start_time=None):
            self.logger = logger
            self.name = name
            self._start_time = start_time
            self.last = None

        def __repr__(self) -> str:
            return f"{self.__class__.__name__}(name={self.name}, logger={self.logger}, start_time={self._start_time}, last={self.last})"

    def get_formatted_time(
        self, name: Optional[str] = None, format: Optional[str] = None
    ):
        if not format:
            format = self._time_format
        if name:
            return time.strftime(format, time.gmtime(self._timers[name].last))
        else:
            return time.strftime(format, time.gmtime(self.last))

    def make_formatted_time(self, seconds: float, format=None):
        if not format:
            format = self._time_format
        return time.strftime(format, time.gmtime(seconds))

    def __init__(self, logger=print, time_frmt="%m-%Y-%d %Hh:%Mm:%Ss"):
        self.logger = logger
        self._start_time = None
        self.last = None
        self._timers = {}
        self._time_format = time_frmt

    def start(self, name=None) -> None:
        """Start the timer."""
        # if self._start_time is not None:
        #     raise TimerError("Timer is running. Use .stop() to stop it")

        # log when timer starts
        if self.logger:
            if name:
                self.logger("Timer {name} started...".format(name=name))
            else:
                self.logger("Timer started...")

        self._start_time = time.perf_counter()
        if name:
            self._timers[name] = Timer.timer(
                logger=self.logger, name=name, start_time=time.perf_counter()
            )

    def stop(self, name=None) -> float:
        """Stop the timer and report the elapsed time."""
        if self._start_time is None:
            raise TimerError("Timer is not running. Use .start() to start it")

        # calculate elapsed time
        self.last = time.perf_counter() - self._start_time

        if name:
            self._timers[name].last = (
                time.perf_counter() - self._timers[name]._start_time
            )

        # report elapsed time
        if self.logger:
            if name:
                self.logger(
                    "Timer {name} reported elapsed time: {sec}".format(
                        name=name, sec=self.last
                    )
                )
            else:
                self.logger(
                    "Timer reported elapsed time: {sec}".format(
                        sec=self._timers[name].last
                    )
                )

        return self.last
