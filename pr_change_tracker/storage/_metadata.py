import sqlalchemy
from sqlalchemy import orm

type BigInt = int

registry = orm.registry(type_annotation_map={BigInt: sqlalchemy.BigInteger})
