from kiss.models import Model, CharField, TextField, DateTimeField, BooleanField, ForeignKeyField


class Blog(Model):
	creator = CharField()
	name = CharField()


class Entry(Model):
	blog = ForeignKeyField(Blog)
	title = CharField()
	body = TextField()
	pub_date = DateTimeField()
	published = BooleanField(default=True)
