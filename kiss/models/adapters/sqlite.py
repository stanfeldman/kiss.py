from kiss.models.core import BaseAdapter, Engine
from kiss.core.exceptions import ImproperlyConfigured
try:
    import sqlite3
except ImportError:
    sqlite3 = None

if sqlite3:
	import decimal
	sqlite3.register_adapter(decimal.Decimal, lambda v: str(v))
	sqlite3.register_converter('decimal', lambda v: decimal.Decimal(v))


class SqliteAdapter(BaseAdapter):
    # note the sqlite library uses a non-standard interpolation string
    operations = {
        'lt': '< ?',
        'lte': '<= ?',
        'gt': '> ?',
        'gte': '>= ?',
        'eq': '= ?',
        'ne': '!= ?', # watch yourself with this one
        'in': 'IN (%s)', # special-case to list q-marks
        'is': 'IS ?',
        'icontains': "LIKE ? ESCAPE '\\'", # surround param with %'s
        'contains': "GLOB ?", # surround param with *'s
        'istartswith': "LIKE ? ESCAPE '\\'",
        'startswith': "GLOB ?",
    }
    interpolation = '?'
    
    def connect(self, options):
        if not sqlite3:
            raise ImproperlyConfigured('sqlite3 must be installed on the system')
        return sqlite3.connect(options["database"])
    
    def lookup_cast(self, lookup, value):
        if lookup == 'contains':
            return '*%s*' % value
        elif lookup == 'icontains':
            return '%%%s%%' % value
        elif lookup == 'startswith':
            return '%s*' % value
        elif lookup == 'istartswith':
            return '%s%%' % value
        return value
        
class SqliteEngine(Engine):
    def __init__(self, connect_kwargs):
        super(SqliteEngine, self).__init__(SqliteAdapter(), connect_kwargs)
    
    def get_indexes_for_table(self, table):
        res = self.execute('PRAGMA index_list(%s);' % table)
        rows = sorted([(r[1], r[2] == 1) for r in res.fetchall()])
        return rows
    
    def get_tables(self):
        res = self.execute('select name from sqlite_master where type="table" order by name')
        return [r[0] for r in res.fetchall()]
