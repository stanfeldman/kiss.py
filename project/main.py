import sys, time, datetime
sys.path.append("..")
from kiss.core.application import Application
from settings import options

#app = Application(options)
#app.start()

import sys, time, datetime
from kiss.models.core import Model, CharField, TextField, DateTimeField, BooleanField, ForeignKeyField
from kiss.models.adapters.postgresql import PostgresqlDatabase

database = PostgresqlDatabase(host="localhost", database='test', user='postgres', password="postgres")


class DbModel(Model):
    class Meta:
        database = database


class Blog(DbModel):
    creator = CharField()
    name = CharField()


class Entry(DbModel):
    blog = ForeignKeyField(Blog)
    title = CharField()
    body = TextField()
    pub_date = DateTimeField()
    published = BooleanField(default=True)

    
#Blog.create_table()
#Entry.create_table()

time1 = time.time()
#blog = Blog()
blog = Blog.get(id=1)
blog.name = "super blog"
blog.creator = "Stas"
blog.save()
#entry = Entry()
entry = Entry.get(id=2)
entry.blog = blog
entry.title = "super post"
entry.body = "lkoeirsldfkwierj"
entry.pub_date = datetime.datetime.now()
entry.save()
time2 = time.time()
print "save time: %s" % (time2-time1)

time1 = time.time()
for blog in Blog.select():
	print blog.name
	print list(blog.entry_set)
time2 = time.time()
print "select time: %s" % (time2-time1)
