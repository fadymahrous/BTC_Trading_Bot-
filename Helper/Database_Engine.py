import configparser
from os import path, getenv
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
import logging
from Helper.AWS_And_DB_Config_Schema import AWSConfig
from Infrastructure.Get_AWS_Data import Get_AWS_Data


class DatabaseEngine:
    def __init__(self, config_path='Config/config.ini'):
        self.logger = logging.getLogger('combined_OHLC_trade')

        # Load configuration
        try:
            config = configparser.ConfigParser()
            config.optionxform = str  # preserve case
            config.read(path.join(config_path))
            self.db_config = AWSConfig(**dict(config['AWS_General']))
            self.logger.info("Database configuration loaded successfully.")
        except Exception as e:
            self.logger.error(f"Failed to load database configuration: {e}")
            raise

        # Load endpoint from environment variable
        self.db_endpoint = getenv('db_endpoint')
        if not self.db_endpoint:
            self.logger.error('Database endpoint is not defined. Please set the environment variable "db_endpoint".')
            raise ValueError('Database endpoint is not defined. Please set the environment variable "db_endpoint".')

        # Initialize AWS data handler
        self.get_aws_configuration = Get_AWS_Data(self.db_config.region_name)

    def _check_db_connection(self, engine):
        """Test connection to the database."""
        try:
            with engine.connect() as connection:
                result = connection.execute(text('SELECT 1'))
                self.logger.info(f"Database connection test successful. Query result: {result.scalar()}")
                return True
        except Exception as e:
            self.logger.error(f"Database connection failed: {e}")
            raise

    def create_postgres_engine(self):
        """Create and return a SQLAlchemy engine for the configured PostgreSQL database."""
        try:
            engine = create_engine(
                f'postgresql+psycopg2://{self.db_config.masterusername}:'
                f'{self.db_config.masteruserpassword}@{self.db_endpoint}:'
                f'{self.db_config.db_port}/{self.db_config.dbname}'
            )
            self.logger.info("SQLAlchemy engine created successfully.")
            if self._check_db_connection(engine):
                return engine
        except SQLAlchemyError as e:
            self.logger.error(f"Failed to create SQLAlchemy engine: {e}")
            raise
