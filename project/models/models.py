from kiss.models import Entity, Field, Unicode, UnicodeText, OneToMany, ManyToOne


class Blog(Entity):
	creator = Field(Unicode)
	name = Field(Unicode)
	entries = OneToMany("Entry")


class Entry(Entity):
	title = Field(Unicode)
	body = Field(UnicodeText)
	blog = ManyToOne("Blog")
