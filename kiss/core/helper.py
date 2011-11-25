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
