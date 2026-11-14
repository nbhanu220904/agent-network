from psycopg_pool import ConnectionPool
from pgvector.psycopg import register_vector
from app.config import settings

def _configure(conn):
    register_vector(conn)

pool = ConnectionPool(settings.database_url, configure=_configure, open=True)