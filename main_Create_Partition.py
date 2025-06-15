from Helper.Create_DatabaseSchema import Create_DatabaseSchema
from Helper.Database_Engine import DatabaseEngine
from sqlalchemy import inspect
from Helper.logger_setup import setup_logger
import logging
import re

logger = logging.getLogger('fetch_OHLC')

def main():
    
    engine_gen = DatabaseEngine()
    engine = engine_gen.create_postgres_engine()
    inspector = inspect(engine)
    
    # Get all tables in 'trade' schema
    all_tables = inspector.get_table_names(schema='trade')

    # Filter to base tables only (exclude partitions)
    base_tables = [t.split('_')[1] for t in all_tables if not re.search(r'_p_\d{8}$', t)]
    logger.info(f"Base tables found: {base_tables}")

    # Create partition for each base table
    create_table = Create_DatabaseSchema()
    for table_name in base_tables:
        logger.info(f"Creating partition for table: {table_name}")
        create_table.create_partition(table_name, offset=1)

if __name__ == '__main__':
    main()
