from psycopg_pool import ConnectionPool
from pgvector.psycopg import register_vector
from app.config import settings

def _configure(conn):
    register_vector(conn)

pool = ConnectionPool(
    settings.database_url,
    configure=_configure,
    min_size=1,
    max_size=5,
    max_idle=60,
    check=ConnectionPool.check_connection,  # test a connection before handing it out
    open=True,
)