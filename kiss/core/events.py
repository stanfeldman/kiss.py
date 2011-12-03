from kiss.core.helpers import Singleton


class Eventer(object):
	__metaclass__ = Singleton
	
	def __init__(self, mapping={}):
		self.__mapping = mapping
		
	def subscribe(self, signal, slot):
		if not signal in self.__mapping:
			self.__mapping[signal] = []
		self.__mapping[signal].append(slot)
		
	def publish(self, signal, *argc, **argw):
		if signal in self.__mapping:
			for slot in self.__mapping[signal]:
				slot(*argc, **argw)

		
class Event(object):
	APPLICATION_AFTER_LOAD = 0
