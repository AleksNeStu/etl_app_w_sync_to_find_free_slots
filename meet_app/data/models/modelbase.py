"""The declarative_base() base class contains a MetaData object where newly
defined Table objects are collected. This object is intended to be accessed
directly for MetaData-specific operations. Such as, to issue CREATE statements
for all tables."""

import sqlalchemy.ext.declarative as dec


SqlAlchemyBase = dec.declarative_base()


def _unique(session, cls, hashfunc, queryfunc, constructor, arg, kw):
    """Provide the "guts" to the unique recipe.

    Is given a Session to work with, and associates a dictionary with
    the Session() which keeps track of current "unique" keys.
    """
    cache = getattr(session, '_unique_cache', None)
    if cache is None:
        session._unique_cache = cache = {}

    key = (cls, hashfunc(*arg, **kw))
    if key in cache:
        return cache[key]
    else:
        with session.no_autoflush:
            q = session.query(cls)
            q = queryfunc(q, *arg, **kw)
            obj = q.first()
            if not obj:
                obj = constructor(*arg, **kw)
                session.add(obj)
        cache[key] = obj
        return obj


# Avoid sqlalchemy.exc.IntegrityError: (sqlite3.IntegrityError) UNIQUE constraint failed
class UniqueMixin(object):
    @classmethod
    def unique_hash(cls, *arg, **kw):
        raise NotImplementedError()

    @classmethod
    def unique_filter(cls, query, *arg, **kw):
        raise NotImplementedError()

    @classmethod
    def as_unique(cls, session, *arg, **kw):
        return _unique(
            session,
            cls,
            cls.unique_hash,
            cls.unique_filter,
            cls,
            arg, kw
        )