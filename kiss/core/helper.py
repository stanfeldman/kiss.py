class Helper(object):
	@staticmethod
	def flat(d, delimiter="/", key="", out={}):
		for k,v in d.iteritems():
			new_key = key + delimiter + k
			if isinstance(v, dict):
				Helper.flat(v, delimiter, new_key, out)
			else:
				out[new_key] = v
		return out
		
class Singleton(type):
     def __init__(cls, name, bases, dict):
         super(Singleton, cls).__init__(name, bases, dict)
         cls.instance = None
         
     def __call__(cls,*args,**kw):
         if cls.instance is None:
             cls.instance = super(Singleton, cls).__call__(*args, **kw)
         return cls.instance
