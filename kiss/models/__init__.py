from elixir import *


def get_or_create(cls, **kwargs):
	instance = session.query(cls).filter_by(**kwargs).first()
	if instance:
		return instance
	else:
		instance = cls(**kwargs)
		return instance
Entity.get_or_create = classmethod(get_or_create) #monkey patch =)
