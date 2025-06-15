from sqlalchemy import text
from datetime import datetime, timedelta, timezone
from Helper.Database_Engine import DatabaseEngine
import logging

class CreateDatabaseSchema:
    def __init__(self, schema: str = 'trade'):
        if not schema:
            raise ValueError('Must provide a schema name to instantiate this class')
        if '/' in schema:
            raise ValueError("Schema name cannot contain '/' (invalid for PostgreSQL)")
        self.schema = schema
        self.logger = logging.getLogger('combined_OHLC_trade')

        # Create engine to connect to AWS-hosted PostgreSQL DB
        db_engine = DatabaseEngine()
        self.engine = db_engine.create_postgres_engine()

    def _create_schema_if_not_exists(self):
        with self.engine.connect() as conn:
            self.logger.info(f"Creating schema '{self.schema}' if it doesn't exist...")
            conn.execute(text(f"CREATE SCHEMA IF NOT EXISTS {self.schema}"))
            conn.commit()

    def create_tables_ohlc(self, table_name: str):
        if not table_name:
            raise ValueError("Must provide a table name to create tables")

        self.table_name = table_name
        self._create_schema_if_not_exists()

        base_table = f"{self.schema}.{self.table_name}"
        index_name = f"idx_{self.table_name}_date"

        trade_ohlc_sql = f"""
        CREATE TABLE IF NOT EXISTS {base_table} (
            date TIMESTAMPTZ NOT NULL,
            open NUMERIC,
            high NUMERIC,
            low NUMERIC,
            close NUMERIC,
            volume NUMERIC
        ) PARTITION BY RANGE (date);
        """

        create_index_sql = f"""
        CREATE INDEX IF NOT EXISTS {index_name}
        ON {base_table} (date);
        """

        try:
            with self.engine.connect() as conn:
                self.logger.info(f"Creating base partitioned table '{base_table}'...")
                conn.execute(text(trade_ohlc_sql))
                conn.execute(text(create_index_sql))
                conn.commit()
                self.logger.info(f"Table '{base_table}' and index '{index_name}' created successfully.")
        except Exception as e:
            self.logger.error(f"Failed to create table or index: {e}", exc_info=True)
            raise

    def create_partition(self, table_name: str, offset: int = 1):
        # This method creates partitions for the given offset (0 = today, 1 = tomorrow, etc.)
        if not table_name:
            raise ValueError('Must provide a table name to create partitions')
        self.table_name = table_name

        # Create partitions based on date offset
        partition_date = (datetime.now(timezone.utc) + timedelta(days=offset)).replace(hour=0, minute=0, second=0, microsecond=0)
        next_day = partition_date + timedelta(days=1)
        date_str = partition_date.strftime('%Y%m%d')

        create_statement = f"""
        CREATE TABLE IF NOT EXISTS {self.schema}.{self.table_name}_p_{date_str}
        PARTITION OF {self.schema}.{self.table_name}
        FOR VALUES FROM ('{partition_date}') TO ('{next_day}');
        """

        with self.engine.connect() as conn:
            self.logger.info(f"Creating partition for {partition_date.date()}...")
            conn.execute(text(create_statement))
            conn.commit()

if __name__ == '__main__':
    db_handler = CreateDatabaseSchema('trade')  # Avoid using invalid schema names like 'BTC/USDT'

    # db_handler.create_tables('btc_ohlc')
    # db_handler.create_partition('btc_ohlc')
