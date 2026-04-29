import logging
import time
from dataclasses import dataclass
from typing import List
from abc import ABC, abstractmethod


logger = logging.getLogger('bspg')
logger.addHandler(logging.NullHandler())


class LogLevel:
	DEBUG = 'DEBUG'
	INFO = 'INFO'
	WARNING = 'WARNING'
	ERROR = 'ERROR'
	CRITICAL = 'CRITICAL'


@dataclass
class LogMessage:
	level: str
	source: str
	message: str
	timestamp: float = 0.0


class DebugSink(ABC):
	@abstractmethod
	def emit(self, log: LogMessage) -> None:
		raise NotImplementedError()


class LogRouter:
	def __init__(self):
		self.sinks: List[DebugSink] = []

	def add_sink(self, sink: DebugSink) -> None:
		if sink not in self.sinks:
			self.sinks.append(sink)

	def remove_sink(self, sink: DebugSink) -> None:
		if sink in self.sinks:
			self.sinks.remove(sink)

	def log(self, level: str, source: str, message: str) -> None:
		lm = LogMessage(level=level, source=source, message=message, timestamp=time.time())
		for s in list(self.sinks):
			try:
				s.emit(lm)
			except Exception:
				# avoid raising from sinks
				logger.exception('Log sink failed')


class BSPGLogger:
	def __init__(self, router: LogRouter):
		self.router = router

	def debug(self, source: str, message: str):
		self.router.log(LogLevel.DEBUG, source, message)

	def info(self, source: str, message: str):
		self.router.log(LogLevel.INFO, source, message)

	def warning(self, source: str, message: str):
		self.router.log(LogLevel.WARNING, source, message)

	def error(self, source: str, message: str):
		self.router.log(LogLevel.ERROR, source, message)

	def critical(self, source: str, message: str):
		self.router.log(LogLevel.CRITICAL, source, message)


# module-level router and logger instance
router = LogRouter()
bspg_logger = BSPGLogger(router)
