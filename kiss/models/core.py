from __future__ import with_statement
from datetime import datetime
import copy
import decimal
import logging
import os
import re
import threading
import time
from kiss.core.exceptions import DoesNotExist, EmptyResultException
from queries import SelectQuery, InsertQuery, UpdateQuery, DeleteQuery, RawQuery
from putils.patterns import Singleton
from putils.types import Boolean


class BaseAdapter(Singleton):
    """
    The various subclasses of `BaseAdapter` provide a bridge between the high-
    level `Engine` abstraction and the underlying python libraries like
    psycopg2.  It also provides a way to unify the pythonic field types with
    the underlying column types used by the database engine.
    
    The `BaseAdapter` provides two types of mappings:    
    - mapping between filter operations and their database equivalents
    - mapping between basic field types and their database column types
    
    The `BaseAdapter` also is the mechanism used by the `Engine` class to:
    - handle connections with the database
    - extract information from the database cursor
    """
    
    operations = {'eq': '= %s'}
    interpolation = '%s'
    
    def get_field_types(self):
        field_types = {
            'integer': 'INTEGER',
            'float': 'REAL',
            'decimal': 'DECIMAL',
            'string': 'VARCHAR',
            'text': 'TEXT',
            'datetime': 'DATETIME',
            'primary_key': 'INTEGER',
            'foreign_key': 'INTEGER',
            'boolean': 'SMALLINT',
        }
        field_types.update(self.get_field_overrides())
        return field_types
    
    def get_field_overrides(self):
        return {}
    
    def connect(self, **kwargs):
        raise NotImplementedError
    
    def close(self, conn):
        conn.close()
    
    def lookup_cast(self, lookup, value):
        if lookup in ('contains', 'icontains'):
            return '%%%s%%' % value
        elif lookup in ('startswith', 'istartswith'):
            return '%s%%' % value
        return value
    
    def last_insert_id(self, cursor, model):
        return cursor.lastrowid
    
    def rows_affected(self, cursor):
        return cursor.rowcount


class Engine(Singleton):
    """
    A high-level api for working with the supported database engines.  `Engine`
    provides a wrapper around some of the functions performed by the `Adapter`,
    in addition providing support for:
    - execution of SQL queries
    - creating and dropping tables and indexes
    """
    
    def __init__(self, adapter, connect_kwargs, threadlocals=False):
        self.adapter = adapter
        self.connect_kwargs = connect_kwargs
        self.database = self.connect_kwargs["database"]        
        if threadlocals:
            self.__local = threading.local()
        else:
            self.__local = type('DummyLocal', (object,), {})       
        self._conn_lock = threading.Lock()
        BaseModelOptions.database = self
    
    def connect(self):
        with self._conn_lock:
            self.__local.conn = self.adapter.connect(self.connect_kwargs)
            self.__local.closed = False
    
    def close(self):
        with self._conn_lock:
            self.adapter.close(self.__local.conn)
            self.__local.closed = True
    
    def get_conn(self):
        if not hasattr(self.__local, 'closed') or self.__local.closed:
            self.connect()
        return self.__local.conn
    
    def get_cursor(self):
        return self.get_conn().cursor()
    
    def execute(self, sql, params=None, commit=False):
        cursor = self.get_cursor()
        res = cursor.execute(sql, params or ())
        if commit:
            self.commit()
        return cursor
    
    def commit(self):
        self.get_conn().commit()
    
    def rollback(self):
        self.get_conn().rollback()
    
    def last_insert_id(self, cursor, model):
        return self.adapter.last_insert_id(cursor, model)
    
    def rows_affected(self, cursor):
        return self.adapter.rows_affected(cursor)
    
    def column_for_field(self, db_field):
        try:
            return self.adapter.get_field_types()[db_field]
        except KeyError:
            raise AttributeError('Unknown field type: "%s", valid types are: %s' % \
                db_field, ', '.join(self.adapter.get_field_types().keys())
            )
    
    def create_table(self, model_class, safe=False):
        framing = safe and "CREATE TABLE IF NOT EXISTS %s (%s);" or "CREATE TABLE %s (%s);"
        columns = []

        for field in model_class._meta.fields.values():
            columns.append(field.to_sql())

        query = framing % (model_class._meta.db_table, ', '.join(columns))
        
        self.execute(query, commit=True)
    
    def create_index(self, model_class, field, unique=False):
        framing = 'CREATE %(unique)s INDEX %(model)s_%(field)s ON %(model)s(%(field)s);'
        
        if field not in model_class._meta.fields:
            raise AttributeError(
                'Field %s not on model %s' % (field, model_class)
            )
        
        unique_expr = Boolean.ternary(unique, 'UNIQUE', '')
        
        query = framing % {
            'unique': unique_expr,
            'model': model_class._meta.db_table,
            'field': field
        }
        
        self.execute(query, commit=True)
    
    def drop_table(self, model_class, fail_silently=False):
        framing = fail_silently and 'DROP TABLE IF EXISTS %s;' or 'DROP TABLE %s;'
        self.execute(framing % model_class._meta.db_table, commit=True)
    
    def get_indexes_for_table(self, table):
        raise NotImplementedError
    
    def get_tables(self):
        raise NotImplementedError


class FieldDescriptor(object):
    def __init__(self, field):
        self.field = field
        self._cache_name = '__%s' % self.field.name
    
    def __get__(self, instance, instance_type=None):
        if instance:
            return getattr(instance, self._cache_name, None)
        return self.field
    
    def __set__(self, instance, value):
        setattr(instance, self._cache_name, value)


class Field(object):
    db_field = ''
    default = None
    field_template = "%(column_type)s%(nullable)s"
    _field_counter = 0
    _order = 0

    def get_attributes(self):
        return {}
    
    def __init__(self, null=False, db_index=False, unique=False, verbose_name=None,
                 help_text=None, *args, **kwargs):
        self.null = null
        self.db_index = db_index
        self.unique = unique
        self.attributes = self.get_attributes()
        self.default = kwargs.get('default', None)
        self.verbose_name = verbose_name
        self.help_text = help_text
        
        kwargs['nullable'] = Boolean.ternary(self.null, '', ' NOT NULL')
        self.attributes.update(kwargs)
        
        Field._field_counter += 1
        self._order = Field._field_counter
    
    def add_to_class(self, klass, name):
        self.name = name
        self.model = klass
        self.verbose_name = self.verbose_name or re.sub('_+', ' ', name).title()
        setattr(klass, name, FieldDescriptor(self))
    
    def render_field_template(self):
        col_type = self.model._meta.database.column_for_field(self.db_field)
        self.attributes['column_type'] = col_type
        return self.field_template % self.attributes
    
    def to_sql(self):
        rendered = self.render_field_template()
        return '%s %s' % (self.name, rendered)
    
    def null_wrapper(self, value, default=None):
        if (self.null and value is None) or default is None:
            return value
        return value or default
    
    def db_value(self, value):
        return value
    
    def python_value(self, value):
        return value
    
    def lookup_value(self, lookup_type, value):
        return self.db_value(value)

    def class_prepared(self):
        pass


class CharField(Field):
    db_field = 'string'
    field_template = '%(column_type)s(%(max_length)d)%(nullable)s'
    
    def get_attributes(self):
        return {'max_length': 255}
    
    def db_value(self, value):
        if self.null and value is None:
            return value
        value = value or ''
        return value[:self.attributes['max_length']]
    
    def lookup_value(self, lookup_type, value):
        if lookup_type == 'contains':
            return '*%s*' % self.db_value(value)
        elif lookup_type == 'icontains':
            return '%%%s%%' % self.db_value(value)
        else:
            return self.db_value(value)
    

class TextField(Field):
    db_field = 'text'
    
    def db_value(self, value):
        return self.null_wrapper(value, '')
    
    def lookup_value(self, lookup_type, value):
        if lookup_type == 'contains':
            return '*%s*' % self.db_value(value)
        elif lookup_type == 'icontains':
            return '%%%s%%' % self.db_value(value)
        else:
            return self.db_value(value)


class DateTimeField(Field):
    db_field = 'datetime'
    
    def python_value(self, value):
        if isinstance(value, basestring):
            value = value.rsplit('.', 1)[0]
            return datetime(*time.strptime(value, '%Y-%m-%d %H:%M:%S')[:6])
        return value


class IntegerField(Field):
    db_field = 'integer'
    
    def db_value(self, value):
        return self.null_wrapper(value, 0)
    
    def python_value(self, value):
        if value is not None:
            return int(value)


class BooleanField(IntegerField):
    db_field = 'boolean'
    
    def db_value(self, value):
        return bool(value)
    
    def python_value(self, value):
        return bool(value)


class FloatField(Field):
    db_field = 'float'
    
    def db_value(self, value):
        return self.null_wrapper(value, 0.0)
    
    def python_value(self, value):
        if value is not None:
            return float(value)


class DecimalField(Field):
    db_field = 'decimal'
    field_template = '%(column_type)s(%(max_digits)d, %(decimal_places)d)%(nullable)s'
    
    def get_attributes(self):
        return {
            'max_digits': 10,
            'decimal_places': 5,
        }
    
    def db_value(self, value):
        return self.null_wrapper(value, decimal.Decimal(0))
    
    def python_value(self, value):
        if value is not None:
            if isinstance(value, decimal.Decimal):
                return value
            return decimal.Decimal(str(value))


class PrimaryKeyField(IntegerField):
    db_field = 'primary_key'
    field_template = "%(column_type)s NOT NULL PRIMARY KEY"


class ForeignRelatedObject(object):    
    def __init__(self, to, field):
        self.to = to
        self.field = field
        self.field_name = self.field.name
        self.cache_name = '_cache_%s' % self.field_name
    
    def __get__(self, instance, instance_type=None):
        if not instance:
            return self.field
        
        if not getattr(instance, self.cache_name, None):
            id = getattr(instance, self.field_name, 0)
            qr = self.to.select().where(**{self.to._meta.pk_name: id})
            try:
                setattr(instance, self.cache_name, qr.get())
            except self.to.DoesNotExist:
                if not self.field.null:
                    raise
        return getattr(instance, self.cache_name, None)
    
    def __set__(self, instance, obj):
        assert isinstance(obj, self.to), "Cannot assign %s, invalid type" % obj
        setattr(instance, self.field_name, obj.get_pk())
        setattr(instance, self.cache_name, obj)


class ReverseForeignRelatedObject(object):
    def __init__(self, related_model, name):
        self.field_name = name
        self.related_model = related_model
    
    def __get__(self, instance, instance_type=None):
        query = {self.field_name: instance.get_pk()}
        qr = self.related_model.select().where(**query)
        return qr


class ForeignKeyField(IntegerField):
    db_field = 'foreign_key'
    field_template = '%(column_type)s%(nullable)s REFERENCES %(to_table)s (%(to_pk)s)%(cascade)s%(extra)s'
    
    def __init__(self, to, null=False, related_name=None, cascade=False, extra=None, *args, **kwargs):
        self.to = to
        self._related_name = related_name
        self.cascade = cascade
        self.extra = extra

        kwargs.update({
            'cascade': ' ON DELETE CASCADE' if self.cascade else '',
            'extra': self.extra or '',
        })
        super(ForeignKeyField, self).__init__(null=null, *args, **kwargs)
    
    def add_to_class(self, klass, name):
        self.descriptor = name
        self.name = name + '_id'
        self.model = klass

        if self.to == 'self':
            self.to = self.model

        self.verbose_name = self.verbose_name or re.sub('_', ' ', name).title()
        
        if self._related_name is not None:
            self.related_name = self._related_name
        else:
            self.related_name = klass._meta.db_table + '_set'
        
        klass._meta.rel_fields[name] = self.name
        setattr(klass, self.descriptor, ForeignRelatedObject(self.to, self))
        setattr(klass, self.name, None)
        
        reverse_rel = ReverseForeignRelatedObject(klass, self.name)
        setattr(self.to, self.related_name, reverse_rel)
        self.to._meta.reverse_relations[self.related_name] = klass
    
    def lookup_value(self, lookup_type, value):
        if isinstance(value, Model):
            return value.get_pk()
        return value or None
    
    def db_value(self, value):
        if isinstance(value, Model):
            return value.get_pk()
        return value

    def class_prepared(self):
        # unfortunately because we may not know the primary key field
        # at the time this field's add_to_class() method is called, we
        # need to update the attributes after the class has been built
        self.attributes.update({
            'to_table': self.to._meta.db_table,
            'to_pk': self.to._meta.pk_name,
        })


class BaseModelOptions(object):
    ordering = None

    def __init__(self, model_class, options=None):
        # configurable options
        for k, v in options.items():
            setattr(self, k, v)
        
        self.rel_fields = {}
        self.reverse_relations = {}
        self.fields = {}
        self.model_class = model_class
    
    def get_sorted_fields(self):
        return sorted(self.fields.items(), key=lambda (k,v): (k == self.pk_name and 1 or 2, v._order))
    
    def get_field_names(self):
        return [f[0] for f in self.get_sorted_fields()]
    
    def get_fields(self):
        return [f[1] for f in self.get_sorted_fields()]
    
    def get_field_by_name(self, name):
        if name in self.fields:
            return self.fields[name]
        raise AttributeError('Field named %s not found' % name)
    
    def get_related_field_by_name(self, name):
        if name in self.rel_fields:
            return self.fields[self.rel_fields[name]]
    
    def get_related_field_for_model(self, model, name=None):
        for field in self.fields.values():
            if isinstance(field, ForeignKeyField) and field.to == model:
                if name is None or name == field.name or name == field.descriptor:
                    return field
    
    def get_reverse_related_field_for_model(self, model, name=None):
        for field in model._meta.fields.values():
            if isinstance(field, ForeignKeyField) and field.to == self.model_class:
                if name is None or name == field.name or name == field.descriptor:
                    return field
    
    def rel_exists(self, model):
        return self.get_related_field_for_model(model) or \
               self.get_reverse_related_field_for_model(model)


class BaseModel(type):
    inheritable_options = ['database', 'ordering']
    
    def __new__(cls, name, bases, attrs):
        cls = super(BaseModel, cls).__new__(cls, name, bases, attrs)

        if not bases:
            return cls

        attr_dict = {}
        meta = attrs.pop('Meta', None)
        if meta:
            attr_dict = meta.__dict__
        
        for b in bases:
            base_meta = getattr(b, '_meta', None)
            if not base_meta:
                continue
            
            for (k, v) in base_meta.__dict__.items():
                if k in cls.inheritable_options and k not in attr_dict:
                    attr_dict[k] = v
                elif k == 'fields':
                    for field_name, field_obj in v.items():
                        if isinstance(field_obj, PrimaryKeyField):
                            continue
                        if field_name in cls.__dict__:
                            continue
                        if isinstance(field_obj, ForeignKeyField):
                            field_name = field_obj.descriptor
                        field_copy = copy.deepcopy(field_obj)
                        setattr(cls, field_name, field_copy)

        _meta = BaseModelOptions(cls, attr_dict)
        
        if not hasattr(_meta, 'db_table'):
            _meta.db_table = re.sub('[^a-z]+', '_', cls.__name__.lower())

        setattr(cls, '_meta', _meta)
        
        _meta.pk_name = None

        for name, attr in cls.__dict__.items():
            if isinstance(attr, Field):
                attr.add_to_class(cls, name)
                _meta.fields[attr.name] = attr
                if isinstance(attr, PrimaryKeyField):
                    _meta.pk_name = attr.name
        
        if _meta.pk_name is None:
            _meta.pk_name = 'id'
            pk = PrimaryKeyField()
            pk.add_to_class(cls, _meta.pk_name)
            _meta.fields[_meta.pk_name] = pk

        _meta.model_name = cls.__name__

        for field in _meta.fields.values():
            field.class_prepared()
                
        if hasattr(cls, '__unicode__'):
            setattr(cls, '__repr__', lambda self: '<%s: %s>' % (
                _meta.model_name, self.__unicode__()))

        exception_class = type('%sDoesNotExist' % _meta.model_name, (DoesNotExist,), {})
        cls.DoesNotExist = exception_class
        
        return cls


class Model(object):
    __metaclass__ = BaseModel
    
    def __init__(self, *args, **kwargs):
        self.get_field_dict()
        for k, v in kwargs.items():
            setattr(self, k, v)
    
    def __eq__(self, other):
        return other.__class__ == self.__class__ and \
               self.get_pk() and \
               other.get_pk() == self.get_pk()
    
    def get_field_dict(self):
        def get_field_val(field):
            field_value = getattr(self, field.name)
            if not self.get_pk() and field_value is None and field.default is not None:
                if callable(field.default):
                    field_value = field.default()
                else:
                    field_value = field.default
                setattr(self, field.name, field_value)
            return (field.name, field_value)
        
        pairs = map(get_field_val, self._meta.fields.values())
        return dict(pairs)
    
    @classmethod
    def table_exists(cls):
        return cls._meta.db_table in cls._meta.database.get_tables()
    
    @classmethod
    def create_table(cls, fail_silently=False):
        if fail_silently and cls.table_exists():
            return

        cls._meta.database.create_table(cls)
        
        for field_name, field_obj in cls._meta.fields.items():
            if isinstance(field_obj, PrimaryKeyField):
                cls._meta.database.create_index(cls, field_obj.name, True)
            elif isinstance(field_obj, ForeignKeyField):
                cls._meta.database.create_index(cls, field_obj.name, field_obj.unique)
            elif field_obj.db_index or field_obj.unique:
                cls._meta.database.create_index(cls, field_obj.name, field_obj.unique)
    
    @classmethod
    def drop_table(cls, fail_silently=False):
        cls._meta.database.drop_table(cls, fail_silently)
    
    @classmethod
    def filter(cls, *args, **kwargs):
        return filter_query(cls, *args, **kwargs)
    
    @classmethod
    def select(cls, query=None):
        select_query = SelectQuery(cls, query)
        if cls._meta.ordering:
            select_query = select_query.order_by(*cls._meta.ordering)
        return select_query
    
    @classmethod
    def update(cls, **query):
        return UpdateQuery(cls, **query)
    
    @classmethod
    def insert(cls, **query):
        return InsertQuery(cls, **query)
    
    @classmethod
    def delete(cls, **query):
        return DeleteQuery(cls, **query)
    
    @classmethod
    def raw(cls, sql, *params):
        return RawQuery(cls, sql, *params)

    @classmethod
    def create(cls, **query):
        inst = cls(**query)
        inst.save()
        return inst

    @classmethod
    def get_or_create(cls, **query):
        try:
            inst = cls.get(**query)
        except cls.DoesNotExist:
            inst = cls.create(**query)
        return inst
    
    @classmethod            
    def get(cls, *args, **kwargs):
        return cls.select().get(*args, **kwargs)
    
    def get_pk(self):
        return getattr(self, self._meta.pk_name, None)
    
    def save(self):
        field_dict = self.get_field_dict()
        field_dict.pop(self._meta.pk_name)
        if self.get_pk():
            update = self.update(
                **field_dict
            ).where(**{self._meta.pk_name: self.get_pk()})
            update.execute()
        else:
            insert = self.insert(**field_dict)
            new_pk = insert.execute()
            setattr(self, self._meta.pk_name, new_pk)

    def delete_instance(self):
        return self.delete().where(**{
            self._meta.pk_name: self.get_pk()
        }).execute()
