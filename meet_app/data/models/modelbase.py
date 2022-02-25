"""The declarative_base() base class contains a MetaData object where newly
defined Table objects are collected. This object is intended to be accessed
directly for MetaData-specific operations. Such as, to issue CREATE statements
for all tables."""

import sqlalchemy.ext.declarative as dec


SqlAlchemyBase = dec.declarative_base()
