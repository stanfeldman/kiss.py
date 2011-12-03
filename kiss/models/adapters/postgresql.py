from kiss.models.core import BaseAdapter, Database
from kiss.core.exceptions import ImproperlyConfigured
try:
    import psycopg2
except ImportError:
    psycopg2 = None
    

class PostgresqlAdapter(BaseAdapter):
    operations = {
        'lt': '< %s',
        'lte': '<= %s',
        'gt': '> %s',
        'gte': '>= %s',
        'eq': '= %s',
        'ne': '!= %s', # watch yourself with this one
        'in': 'IN (%s)', # special-case to list q-marks
        'is': 'IS %s',
        'icontains': 'ILIKE %s', # surround param with %'s
        'contains': 'LIKE %s', # surround param with *'s
        'istartswith': 'ILIKE %s',
        'startswith': 'LIKE %s',
    }
        
    def connect(self, options):
        if not psycopg2:
            raise ImproperlyConfigured('psycopg2 must be installed on the system')
        return psycopg2.connect(
        	host=options["host"], 
        	database=options["database"], 
        	user=options["user"], 
        	password=options["password"])
    
    def get_field_overrides(self):
        return {
            'primary_key': 'SERIAL',
            'datetime': 'TIMESTAMP',
            'decimal': 'NUMERIC',
            'boolean': 'BOOLEAN',
        }
    
    def last_insert_id(self, cursor, model):
        cursor.execute("SELECT CURRVAL('\"%s_%s_seq\"')" % (
            model._meta.db_table, model._meta.pk_name))
        return cursor.fetchone()[0]
        

class PostgresqlDatabase(Database):
    def __init__(self, connect_kwargs):
        super(PostgresqlDatabase, self).__init__(PostgresqlAdapter(), connect_kwargs)
    
    def get_indexes_for_table(self, table):
        res = self.execute("""
            SELECT c2.relname, i.indisprimary, i.indisunique
            FROM pg_catalog.pg_class c, pg_catalog.pg_class c2, pg_catalog.pg_index i
            WHERE c.relname = %s AND c.oid = i.indrelid AND i.indexrelid = c2.oid
            ORDER BY i.indisprimary DESC, i.indisunique DESC, c2.relname""", (table,))
        return sorted([(r[0], r[1]) for r in res.fetchall()])
    
    def get_tables(self):
        res = self.execute("""
            SELECT c.relname
            FROM pg_catalog.pg_class c
            LEFT JOIN pg_catalog.pg_namespace n ON n.oid = c.relnamespace
            WHERE c.relkind IN ('r', 'v', '')
                AND n.nspname NOT IN ('pg_catalog', 'pg_toast')
                AND pg_catalog.pg_table_is_visible(c.oid)
            ORDER BY c.relname""")
        return [row[0] for row in res.fetchall()]
