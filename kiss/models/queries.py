from kiss.core.exceptions import EmptyResultException


class QueryResultWrapper(object):
    """
    Provides an iterator over the results of a raw Query, additionally doing
    two things:
    - converts rows from the database into model instances
    - ensures that multiple iterations do not result in multiple queries
    """
    def __init__(self, model, cursor):
        self.model = model
        self.cursor = cursor
        self._result_cache = []
        self._populated = False
    
    def model_from_rowset(self, model_class, row_dict):
        instance = model_class()
        for attr, value in row_dict.iteritems():
            if attr in instance._meta.fields:
                field = instance._meta.fields[attr]
                setattr(instance, attr, field.python_value(value))
            else:
                setattr(instance, attr, value)
        return instance    
    
    def _row_to_dict(self, row, result_cursor):
        return dict((result_cursor.description[i][0], value)
            for i, value in enumerate(row))
    
    def __iter__(self):
        if not self._populated:
            return self
        else:
            return iter(self._result_cache)
    
    def next(self):
        row = self.cursor.fetchone()
        if row:
            row_dict = self._row_to_dict(row, self.cursor)
            instance = self.model_from_rowset(self.model, row_dict)
            self._result_cache.append(instance)
            return instance
        else:
            self._populated = True
            raise StopIteration


# semantic wrappers for ordering the results of a `SelectQuery`
def asc(f):
    return (f, 'ASC')

def desc(f):
    return (f, 'DESC')

# wrappers for performing aggregation in a `SelectQuery`
def Count(f, alias='count'):
    return ('COUNT', f, alias)

def Max(f, alias='max'):
    return ('MAX', f, alias)

def Min(f, alias='min'):
    return ('MIN', f, alias)

def Sum(f, alias='sum'):
    return ('SUM', f, alias)

# decorator for query methods to indicate that they change the state of the
# underlying data structures
def returns_clone(func):
    def inner(self, *args, **kwargs):
        clone = self.clone()
        res = func(clone, *args, **kwargs)
        return clone
    return inner


class Node(object):
    def __init__(self, connector='AND', children=None):
        self.connector = connector
        self.children = children or []
        self.negated = False
    
    def connect(self, rhs, connector):
        if isinstance(rhs, Q):
            if connector == self.connector:
                self.children.append(rhs)
                return self
            else:
                p = Node(connector)
                p.children = [self, rhs]
                return p
        elif isinstance(rhs, Node):
            p = Node(connector)
            p.children = [self, rhs]
            return p
    
    def __or__(self, rhs):
        return self.connect(rhs, 'OR')

    def __and__(self, rhs):
        return self.connect(rhs, 'AND')
    
    def __invert__(self):
        self.negated = not self.negated
        return self

    def __nonzero__(self):
        return bool(self.children)
    
    def __unicode__(self):
        query = []
        nodes = []
        for child in self.children:
            if isinstance(child, Q):
                query.append(unicode(child))
            elif isinstance(child, Node):
                nodes.append('(%s)' % unicode(child))
        query.extend(nodes)
        connector = ' %s ' % self.connector
        query = connector.join(query)
        if self.negated:
            query = 'NOT %s' % query
        return query
    

class Q(object):
    def __init__(self, _model=None, **kwargs):
        self.model = _model
        self.query = kwargs
        self.parent = None
        self.negated = False
    
    def connect(self, connector):
        if self.parent is None:
            self.parent = Node(connector)
            self.parent.children.append(self)
    
    def __or__(self, rhs):
        self.connect('OR')
        return self.parent | rhs
    
    def __and__(self, rhs):
        self.connect('AND')
        return self.parent & rhs
    
    def __invert__(self):
        self.negated = not self.negated
        return self
    
    def __unicode__(self):
        bits = ['%s = %s' % (k, v) for k, v in self.query.items()]
        if len(self.query.items()) > 1:
            connector = ' AND '
            expr = '(%s)' % connector.join(bits)
        else:
            expr = bits[0]
        if self.negated:
            expr = 'NOT %s' % expr
        return expr


def apply_model(model, item):
    if isinstance(item, Node):
        for child in item.children:
            apply_model(model, child)
    elif isinstance(item, Q):
        if item.model is None:
            item.model = model

def parseq(model, *args, **kwargs):
    node = Node()
    
    for piece in args:
        apply_model(model, piece)
        if isinstance(piece, (Q, Node)):
            node.children.append(piece)
        else:
            raise TypeError('Unknown object: %s', piece)

    if kwargs:
        node.children.append(Q(model, **kwargs))

    return node

def find_models(item):
    seen = set()
    if isinstance(item, Node):
        for child in item.children:
            seen.update(find_models(child))
    elif isinstance(item, Q):
        seen.add(item.model)
    return seen


class BaseQuery(object):
    query_separator = '__'
    requires_commit = True
    force_alias = False
    
    def __init__(self, model):
        self.model = model
        self.query_context = model
        self.database = self.model._meta.database
        self.operations = self.database.adapter.operations
        self.interpolation = self.database.adapter.interpolation
        
        self._dirty = True
        self._where = []
        self._where_models = set()
        self._joins = {}
        self._joined_models = set()
    
    def _clone_dict_graph(self, dg):
        cloned = {}
        for node, edges in dg.items():
            cloned[node] = list(edges)
        return cloned
    
    def clone_where(self):
        return list(self._where)
    
    def clone_joins(self):
        return self._clone_dict_graph(self._joins)
    
    def clone(self):
        raise NotImplementedError
    
    def lookup_cast(self, lookup, value):
        return self.database.adapter.lookup_cast(lookup, value)
    
    def parse_query_args(self, model, **query):
        parsed = []
        for lhs, rhs in query.iteritems():
            if self.query_separator in lhs:
                lhs, op = lhs.rsplit(self.query_separator, 1)
            else:
                op = 'eq'
            
            try:
                field = model._meta.get_field_by_name(lhs)
            except AttributeError:
                field = model._meta.get_related_field_by_name(lhs)
                if field is None:
                    raise
                if isinstance(rhs, Model):
                    rhs = rhs.get_pk()
            
            if op == 'in':
                if isinstance(rhs, SelectQuery):
                    lookup_value = rhs
                    operation = 'IN (%s)'
                else:
                    if not rhs:
                        raise EmptyResultException
                    lookup_value = [field.db_value(o) for o in rhs]
                    operation = self.operations[op] % \
                        (','.join([self.interpolation for v in lookup_value]))
            elif op == 'is':
                if rhs is not None:
                    raise ValueError('__is lookups only accept None')
                operation = 'IS NULL'
                lookup_value = []
            else:
                lookup_value = field.db_value(rhs)
                operation = self.operations[op]
            
            parsed.append(
                (field.name, (operation, self.lookup_cast(op, lookup_value)))
            )
        
        return parsed
    
    @returns_clone
    def where(self, *args, **kwargs):
        parsed = parseq(self.query_context, *args, **kwargs)
        if parsed:
            self._where.append(parsed)
            self._where_models.update(find_models(parsed))

    @returns_clone
    def join(self, model, join_type=None, on=None):
        if self.query_context._meta.rel_exists(model):
            self._joined_models.add(model)
            self._joins.setdefault(self.query_context, [])
            self._joins[self.query_context].append((model, join_type, on))
            self.query_context = model
        else:
            raise AttributeError('No foreign key found between %s and %s' % \
                (self.query_context.__name__, model.__name__))

    @returns_clone
    def switch(self, model):
        if model == self.model:
            self.query_context = model
            return

        if model in self._joined_models:
            self.query_context = model
            return
        raise AttributeError('You must JOIN on %s' % model.__name__)
    
    def use_aliases(self):
        return len(self._joined_models) > 0 or self.force_alias

    def combine_field(self, alias, field_name):
        if alias:
            return '%s.%s' % (alias, field_name)
        return field_name
    
    def follow_joins(self, current, alias_map, alias_required, alias_count, seen=None):
        computed = []
        seen = seen or set()
        
        if current not in self._joins:
            return computed
        
        for i, (model, join_type, on) in enumerate(self._joins[current]):
            seen.add(model)
            
            if alias_required:
                alias_count += 1
                alias_map[model] = 't%d' % alias_count
            else:
                alias_map[model] = ''
            
            from_model = current
            field = from_model._meta.get_related_field_for_model(model, on)
            if field:
                left_field = field.name
                right_field = model._meta.pk_name
            else:
                field = from_model._meta.get_reverse_related_field_for_model(model, on)
                left_field = from_model._meta.pk_name
                right_field = field.name
            
            if join_type is None:
                if field.null and model not in self._where_models:
                    join_type = 'LEFT OUTER'
                else:
                    join_type = 'INNER'
            
            computed.append(
                '%s JOIN %s AS %s ON %s = %s' % (
                    join_type,
                    model._meta.db_table,
                    alias_map[model],
                    self.combine_field(alias_map[from_model], left_field),
                    self.combine_field(alias_map[model], right_field),
                )
            )
            
            computed.extend(self.follow_joins(model, alias_map, alias_required, alias_count, seen))
        
        return computed
    
    def compile_where(self):
        alias_count = 0
        alias_map = {}

        alias_required = self.use_aliases()
        
        if alias_required:
            alias_count += 1
            alias_map[self.model] = 't%d' % alias_count
        else:
            alias_map[self.model] = ''
        
        computed_joins = self.follow_joins(self.model, alias_map, alias_required, alias_count)
        
        clauses = [self.parse_node(node, alias_map) for node in self._where]
        
        return computed_joins, clauses, alias_map
    
    def flatten_clauses(self, clauses):
        where_with_alias = []
        where_data = []
        for query, data in clauses:
            where_with_alias.append(query)
            where_data.extend(data)
        return where_with_alias, where_data
    
    def convert_where_to_params(self, where_data):
        flattened = []
        for clause in where_data:
            if isinstance(clause, (tuple, list)):
                flattened.extend(clause)
            else:
                flattened.append(clause)
        return flattened
    
    def parse_node(self, node, alias_map):
        query = []
        query_data = []
        for child in node.children:
            if isinstance(child, Q):
                parsed, data = self.parse_q(child, alias_map)
                query.append(parsed)
                query_data.extend(data)
            elif isinstance(child, Node):
                parsed, data = self.parse_node(child, alias_map)
                query.append('(%s)' % parsed)
                query_data.extend(data)
        connector = ' %s ' % node.connector
        query = connector.join(query)
        if node.negated:
            query = 'NOT (%s)' % query
        return query, query_data
    
    def parse_q(self, q, alias_map):
        model = q.model or self.model
        query = []
        query_data = []
        parsed = self.parse_query_args(model, **q.query)
        for (name, lookup) in parsed:
            operation, value = lookup
            if isinstance(value, SelectQuery):
                sql, value = self.convert_subquery(value)
                operation = operation % sql

            query_data.append(value)
            
            combined = self.combine_field(alias_map[model], name)
            query.append('%s %s' % (combined, operation))
        
        if len(query) > 1:
            query = '(%s)' % (' AND '.join(query))
        else:
            query = query[0]
        
        if q.negated:
            query = 'NOT %s' % query
        
        return query, query_data

    def convert_subquery(self, subquery):
        subquery.query, orig_query = subquery.model._meta.pk_name, subquery.query
        subquery.force_alias, orig_alias = True, subquery.force_alias
        sql, data = subquery.sql()
        subquery.query = orig_query
        subquery.force_alias = orig_alias
        return sql, data
    
    def raw_execute(self):
        query, params = self.sql()
        return self.database.execute(query, params, self.requires_commit)


class RawQuery(BaseQuery):
    def __init__(self, model, query, *params):
        self._sql = query
        self._params = list(params)
        super(RawQuery, self).__init__(model)

    def clone(self):
        return RawQuery(self.model, self._sql, *self._params)
    
    def sql(self):
        return self._sql, self._params
    
    def execute(self):
        return QueryResultWrapper(self.model, self.raw_execute())
    
    def join(self):
        raise AttributeError('Raw queries do not support joining programmatically')
    
    def where(self):
        raise AttributeError('Raw queries do not support querying programmatically')
    
    def switch(self):
        raise AttributeError('Raw queries do not support switching contexts')
    
    def __iter__(self):
        return self.execute()


class SelectQuery(BaseQuery):
    requires_commit = False
    
    def __init__(self, model, query=None):
        self.query = query or '*'
        self._group_by = []
        self._having = []
        self._order_by = []
        self._limit = None
        self._offset = None
        self._distinct = False
        self._qr = None
        super(SelectQuery, self).__init__(model)
    
    def clone(self):
        query = SelectQuery(self.model, self.query)
        query.query_context = self.query_context
        query._group_by = list(self._group_by)
        query._having = list(self._having)
        query._order_by = list(self._order_by)
        query._limit = self._limit
        query._offset = self._offset
        query._distinct = self._distinct
        query._qr = self._qr
        query._where = self.clone_where()
        query._where_models = set(self._where_models)
        query._joined_models = self._joined_models.copy()
        query._joins = self.clone_joins()
        return query
    
    @returns_clone
    def paginate(self, page, paginate_by=20):
        if page > 0:
            page -= 1
        self._limit = paginate_by
        self._offset = page * paginate_by
    
    @returns_clone
    def limit(self, num_rows):
        self._limit = num_rows
    
    @returns_clone
    def offset(self, num_rows):
        self._offset = num_rows
    
    def count(self):
        clone = self.order_by()
        clone._limit = clone._offset = None
        
        if clone.use_aliases():
            clone.query = 'COUNT(t1.%s)' % (clone.model._meta.pk_name)
        else:
            clone.query = 'COUNT(%s)' % (clone.model._meta.pk_name)
        
        res = clone.database.execute(*clone.sql())
        
        return res.fetchone()[0]
    
    @returns_clone
    def group_by(self, clause):
        model = self.query_context
        
        if isinstance(clause, basestring):
            fields = (clause,)
        elif isinstance(clause, (list, tuple)):
            fields = clause
        elif issubclass(clause, Model):
            model = clause
            fields = clause._meta.get_field_names()
        
        self._group_by.append((model, fields))
    
    @returns_clone
    def having(self, clause):
        self._having.append(clause)
    
    @returns_clone
    def distinct(self):
        self._distinct = True
    
    @returns_clone
    def order_by(self, *clauses):
        order_by = []
        
        for clause in clauses:
            if isinstance(clause, tuple):
                if len(clause) == 3:
                    model, field, ordering = clause
                elif len(clause) == 2:
                    if isinstance(clause[0], basestring):
                        model = self.query_context
                        field, ordering = clause
                    else:
                        model, field = clause
                        ordering = 'ASC'
                else:
                    raise ValueError('Incorrect arguments passed in order_by clause')
            else:
                model = self.query_context
                field = clause
                ordering = 'ASC'
        
            order_by.append(
                (model, field, ordering)
            )
        
        self._order_by = order_by
    
    def exists(self):
        clone = self.paginate(1, 1)
        clone.query = '(1) AS a'
        curs = self.database.execute(*clone.sql())
        return bool(curs.fetchone())
    
    def get(self, *args, **kwargs):
        try:
            orig_ctx = self.query_context
            self.query_context = self.model
            obj = self.where(*args, **kwargs).paginate(1, 1).execute().next()
            return obj
        except StopIteration:
            raise self.model.DoesNotExist('instance matching query does not exist:\nSQL: %s\nPARAMS: %s' % (
                self.sql()
            ))
        finally:
            self.query_context = orig_ctx
    
    def filter(self, *args, **kwargs):
        return filter_query(self, *args, **kwargs)
    
    def annotate(self, related_model, aggregation=None):
        return annotate_query(self, related_model, aggregation)

    def parse_select_query(self, alias_map):
        if isinstance(self.query, (list, tuple)):
            query = {self.model: self.query}
        else:
            query = self.query
        
        if isinstance(query, basestring):
            if query in ('*', self.model._meta.pk_name) and self.use_aliases():
                return '%s.%s' % (alias_map[self.model], query)
            return query
        elif isinstance(query, dict):
            qparts = []
            aggregates = []
            for model, cols in query.iteritems():
                alias = alias_map.get(model, '')
                for col in cols:
                    if isinstance(col, tuple):
                        if len(col) == 3:
                            func, col, col_alias = col
                            aggregates.append('%s(%s) AS %s' % \
                                (func, self.combine_field(alias, col), col_alias)
                            )
                        elif len(col) == 2:
                            col, col_alias = col
                            qparts.append('%s AS %s' % \
                                (self.combine_field(alias, col), col_alias)
                            )
                    else:
                        qparts.append(self.combine_field(alias, col))
            return ', '.join(qparts + aggregates)
        else:
            raise TypeError('Unknown type encountered parsing select query')
    
    def sql(self):
        joins, clauses, alias_map = self.compile_where()
        where, where_data = self.flatten_clauses(clauses)
        
        table = self.model._meta.db_table

        params = []
        group_by = []
        
        if self.use_aliases():
            table = '%s AS %s' % (table, alias_map[self.model])
            for model, clause in self._group_by:
                alias = alias_map[model]
                for field in clause:
                    group_by.append(self.combine_field(alias, field))
        else:
            group_by = [c[1] for c in self._group_by]

        parsed_query = self.parse_select_query(alias_map)
        
        if self._distinct:
            sel = 'SELECT DISTINCT'
        else:
            sel = 'SELECT'
        
        select = '%s %s FROM %s' % (sel, parsed_query, table)
        joins = '\n'.join(joins)
        where = ' AND '.join(where)
        group_by = ', '.join(group_by)
        having = ' AND '.join(self._having)
        
        order_by = []
        for piece in self._order_by:
            model, field, ordering = piece
            if self.use_aliases() and field in model._meta.fields:
                field = '%s.%s' % (alias_map[model], field)
            order_by.append('%s %s' % (field, ordering))
        
        pieces = [select]
        
        if joins:
            pieces.append(joins)
        if where:
            pieces.append('WHERE %s' % where)
            params.extend(self.convert_where_to_params(where_data))
        
        if group_by:
            pieces.append('GROUP BY %s' % group_by)
        if having:
            pieces.append('HAVING %s' % having)
        if order_by:
            pieces.append('ORDER BY %s' % ', '.join(order_by))
        if self._limit:
            pieces.append('LIMIT %d' % self._limit)
        if self._offset:
            pieces.append('OFFSET %d' % self._offset)
        
        return ' '.join(pieces), params
    
    def execute(self):
        if self._dirty or not self._qr:
            try:
                self._qr = QueryResultWrapper(self.model, self.raw_execute())
                self._dirty = False
                return self._qr
            except EmptyResultException:
                return iter([])
        else:
            # call the __iter__ method directly
            return iter(self._qr)
    
    def __iter__(self):
        return self.execute()


class UpdateQuery(BaseQuery):
    def __init__(self, model, **kwargs):
        self.update_query = kwargs
        super(UpdateQuery, self).__init__(model)
    
    def clone(self):
        query = UpdateQuery(self.model, **self.update_query)
        query._where = self.clone_where()
        query._where_models = set(self._where_models)
        query._joined_models = self._joined_models.copy()
        query._joins = self.clone_joins()
        return query
    
    def parse_update(self):
        sets = {}
        for k, v in self.update_query.iteritems():
            try:
                field = self.model._meta.get_field_by_name(k)
            except AttributeError:
                field = self.model._meta.get_related_field_by_name(k)
                if field is None:
                    raise
            
            sets[field.name] = field.db_value(v)
        
        return sets
    
    def sql(self):
        joins, clauses, alias_map = self.compile_where()
        where, where_data = self.flatten_clauses(clauses)
        set_statement = self.parse_update()

        params = []
        update_params = []

        for k, v in set_statement.iteritems():
            params.append(v)
            update_params.append('%s=%s' % (k, self.interpolation))
        
        update = 'UPDATE %s SET %s' % (
            self.model._meta.db_table, ', '.join(update_params))
        where = ' AND '.join(where)
        
        pieces = [update]
        
        if where:
            pieces.append('WHERE %s' % where)
            params.extend(self.convert_where_to_params(where_data))
        
        return ' '.join(pieces), params
    
    def join(self, *args, **kwargs):
        raise AttributeError('Update queries do not support JOINs in sqlite')
    
    def execute(self):
        result = self.raw_execute()
        return self.database.rows_affected(result)


class DeleteQuery(BaseQuery):
    def clone(self):
        query = DeleteQuery(self.model)
        query._where = self.clone_where()
        query._where_models = set(self._where_models)
        query._joined_models = self._joined_models.copy()
        query._joins = self.clone_joins()
        return query
    
    def sql(self):
        joins, clauses, alias_map = self.compile_where()
        where, where_data = self.flatten_clauses(clauses)

        params = []
        
        delete = 'DELETE FROM %s' % (self.model._meta.db_table)
        where = ' AND '.join(where)
        
        pieces = [delete]
        
        if where:
            pieces.append('WHERE %s' % where)
            params.extend(self.convert_where_to_params(where_data))
        
        return ' '.join(pieces), params
    
    def join(self, *args, **kwargs):
        raise AttributeError('Update queries do not support JOINs in sqlite')
    
    def execute(self):
        result = self.raw_execute()
        return self.database.rows_affected(result)


class InsertQuery(BaseQuery):
    def __init__(self, model, **kwargs):
        self.insert_query = kwargs
        super(InsertQuery, self).__init__(model)
    
    def parse_insert(self):
        cols = []
        vals = []
        for k, v in self.insert_query.iteritems():
            field = self.model._meta.get_field_by_name(k)
            cols.append(k)
            vals.append(field.db_value(v))
        
        return cols, vals
    
    def sql(self):
        cols, vals = self.parse_insert()
        
        insert = 'INSERT INTO %s (%s) VALUES (%s)' % (
            self.model._meta.db_table,
            ','.join(cols),
            ','.join(self.interpolation for v in vals)
        )
        
        return insert, vals
    
    def where(self, *args, **kwargs):
        raise AttributeError('Insert queries do not support WHERE clauses')
    
    def join(self, *args, **kwargs):
        raise AttributeError('Insert queries do not support JOINs')
    
    def execute(self):
        result = self.raw_execute()
        return self.database.last_insert_id(result, self.model)


def model_or_select(m_or_q):
    if isinstance(m_or_q, BaseQuery):
        return (m_or_q.model, m_or_q)
    else:
        return (m_or_q, m_or_q.select())

def convert_lookup(model, joins, lookup):
    operations = model._meta.database.adapter.operations
    
    pieces = lookup.split('__')
    operation = None
    
    query_model = model
    
    if len(pieces) > 1:
        if pieces[-1] in operations:
            operation = pieces.pop()
        
        lookup = pieces.pop()
        
        # we have some joins
        if len(pieces):
            for piece in pieces:
                # piece is something like 'blog' or 'entry_set'
                joined_model = None
                for field in query_model._meta.get_fields():
                    if not isinstance(field, ForeignKeyField):
                        continue
                    
                    if piece in (field.name, field.descriptor, field.related_name):
                        joined_model = field.to
                
                if not joined_model:
                    try:
                        joined_model = query_model._meta.reverse_relations[piece]
                    except KeyError:
                        raise ValueError('Unknown relation: "%s" of "%s"' % (
                            piece,
                            query_model,
                        ))
                
                joins.setdefault(query_model, set())
                joins[query_model].add(joined_model)
                query_model = joined_model
    
    if operation:
        lookup = '%s__%s' % (lookup, operation)
    
    return query_model, joins, lookup


def filter_query(model_or_query, *args, **kwargs):
    """
    Provide a django-like interface for executing queries
    """
    model, select_query = model_or_select(model_or_query)
    
    query = {} # mapping of models to queries
    joins = {} # a graph of joins needed, passed into the convert_lookup function
    
    # traverse Q() objects, find any joins that may be lurking -- clean up the
    # lookups and assign the correct model
    def fix_q(node_or_q, joins):
        if isinstance(node_or_q, Node):
            for child in node_or_q.children:
                fix_q(child, joins)
        elif isinstance(node_or_q, Q):
            new_query = {}
            curr_model = node_or_q.model or model
            for raw_lookup, value in node_or_q.query.items():
                query_model, joins, lookup = convert_lookup(curr_model, joins, raw_lookup)
                new_query[lookup] = value
            node_or_q.model = query_model
            node_or_q.query = new_query
    
    for node_or_q in args:
        fix_q(node_or_q, joins)
    
    # iterate over keyword lookups and determine lookups and necessary joins
    for raw_lookup, value in kwargs.items():
        queried_model, joins, lookup = convert_lookup(model, joins, raw_lookup)
        query.setdefault(queried_model, [])
        query[queried_model].append((lookup, value))
    
    def follow_joins(current, query):
        if current in joins:
            for joined_model in joins[current]:
                query = query.switch(current)
                if joined_model not in query._joined_models:
                    query = query.join(joined_model)
                query = follow_joins(joined_model, query)
        return query
    select_query = follow_joins(model, select_query)
    
    for node in args:
        select_query = select_query.where(node)
    
    for model, lookups in query.items():
        qargs, qkwargs = [], {}
        for lookup in lookups:
            if isinstance(lookup, tuple):
                qkwargs[lookup[0]] = lookup[1]
            else:
                qargs.append(lookup)
        select_query = select_query.switch(model).where(*qargs, **qkwargs)

    return select_query

def annotate_query(select_query, related_model, aggregation):
    aggregation = aggregation or Count(related_model._meta.pk_name)
    model = select_query.model
    
    select_query = select_query.switch(model)
    cols = select_query.query
    
    # ensure the join is there
    if related_model not in select_query._joined_models:
        select_query = select_query.join(related_model).switch(model)
    
    # query for it
    if isinstance(cols, dict):
        selection = cols
        group_by = cols[model]
    elif isinstance(cols, basestring):
        selection = {model: [cols]}
        if cols == '*':
            group_by = model
        else:
            group_by = [col.strip() for col in cols.split(',')]
    elif isinstance(cols, (list, tuple)):
        selection = {model: cols}
        group_by = cols
    else:
        raise ValueError('Unknown type passed in to select query: "%s"' % type(cols))
    
    # query for the related object
    selection[related_model] = [aggregation]
    
    select_query.query = selection
    return select_query.group_by(group_by)
