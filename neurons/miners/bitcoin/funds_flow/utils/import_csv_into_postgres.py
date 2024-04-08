import os
import time

import pandas as pd
from sqlalchemy import create_engine, types


class ExecutionTimeLogger:
    def __init__(self, logger_name):
        self.logger_name = logger_name
    
    def log(self, message):
        print(f"{self.logger_name}: {message}")
    
    def __enter__(self):
        self.start_time = time.time()
        self.log(f"Started")
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        end_time = time.time()
        execution_time = end_time - self.start_time
        self.log(f"Finished in {execution_time} seconds")
        
if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    
    POSTGRES_HOST = os.environ.get("POSTGRES_HOST") or '127.0.0.1'
    POSTGRES_PORT = os.environ.get("POSTGRES_PORT") or 5432
    POSTGRES_DB = os.environ.get("POSTGRES_DB") or 'bitcoin'
    POSTGRES_USER = os.environ.get("POSTGRES_USER") or ''
    POSTGRES_PASSWORD = os.environ.get("POSTGRES_PASSWORD") or ''
    BALANCES_CSV_FILE_PATH = os.environ.get("BALANCES_CSV_FILE_PATH") or ''
    
    with ExecutionTimeLogger("create_engine"):
        engine = create_engine(f'postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}')
        
    with ExecutionTimeLogger("read_csv"):
        df = pd.read_csv(BALANCES_CSV_FILE_PATH, sep=';')

    data_types = {
        'address': types.VARCHAR(length=255),
        'balance': types.BIGINT,
    }
    with ExecutionTimeLogger("to_sql"):
        df.to_sql('accounts', engine, if_exists='replace', index=False, dtype=data_types)
    engine.dispose()
