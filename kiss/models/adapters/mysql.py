from kiss.models.core import BaseAdapter, Engine
from kiss.core.exceptions import ImproperlyConfigured
try:
    import MySQLdb as mysql
except ImportError:
    mysql = None


class MySQLAdapter(BaseAdapter):
    operations = {
        'lt': '< %s',
        'lte': '<= %s',
        'gt': '> %s',
        'gte': '>= %s',
        'eq': '= %s',
        'ne': '!= %s', # watch yourself with this one
        'in': 'IN (%s)', # special-case to list q-marks
        'is': 'IS %s',
        'icontains': 'LIKE %s', # surround param with %'s
        'contains': 'LIKE BINARY %s', # surround param with *'s
        'istartswith': 'LIKE %s',
        'startswith': 'LIKE BINARY %s',
    }

    def connect(self, options):
        if not mysql:
            raise ImproperlyConfigured('MySQLdb must be installed on the system')
        return mysql.connect(
        	host=options["host"], 
        	db=options["database"], 
        	user=options["user"], 
        	passwd=options["password"])

    def get_field_overrides(self):
        return {
            'primary_key': 'integer AUTO_INCREMENT',
            'boolean': 'bool',
            'float': 'float',
            'text': 'longtext',
            'decimal': 'numeric',
        }

        
class MySQLEngine(Engine):
    def __init__(self, connect_kwargs):
        super(MySQLEngine, self).__init__(MySQLAdapter(), connect_kwargs)
    
    def get_indexes_for_table(self, table):
        res = self.execute('SHOW INDEXES IN %s;' % table)
        rows = sorted([(r[2], r[1] == 0) for r in res.fetchall()])
        return rows
    
    def get_tables(self):
        res = self.execute('SHOW TABLES;')
        return [r[0] for r in res.fetchall()]
