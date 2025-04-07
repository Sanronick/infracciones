import oracledb
from config import Config


class ConectorDB:
    def __init__(self):
        self.config=Config()


    def __enter__(self):
        self.connection=oracledb.connect(
            user=self.config.db_user,
            password=self.config.db_password,
            dsn=f'{self.config.db_host}:{self.config.db_port}/{self.config.db_service}'
        )

        return self.connection.cursor()
    
    def __exit__(self,exc_type,exc_val,exc_tb):
        self.connection.close()