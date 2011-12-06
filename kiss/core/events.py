from putils.patterns import Singleton


class Eventer(Singleton):
	
	def __init__(self, mapping={}):
		self.mapping = {}
		for k,v in mapping.iteritems():
			for f in v:
				cl = f.im_class
				c = cl()
				self.subscribe(k, getattr(c, f.__name__))
		
	def subscribe(self, signal, slot):
		if not signal in self.mapping:
			self.mapping[signal] = []
		self.mapping[signal].append(slot)
		
	def unsubscribe(self, signal, slot):
		if signal in self.mapping:
			self.mapping[signal].remove(slot)
		
	def publish(self, signal, *argc, **argw):
		if signal in self.mapping:
			for slot in self.mapping[signal]:
				slot(*argc, **argw)

		
class Event(object):
	APPLICATION_AFTER_LOAD = 0
