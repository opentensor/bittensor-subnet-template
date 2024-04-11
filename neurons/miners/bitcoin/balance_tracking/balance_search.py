import os
from neurons.setup_logger import setup_logger

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from .balance_model import Base, BalanceChange

logger = setup_logger("BalanceSearch")


class BalanceSearch:
    def __init__(
        self,
        postgres_host: str = None,
        postgres_port: int = 0,
        postgres_db: str = None,
        postgres_user: str = None,
        postgres_password: str = None,
    ):
        if postgres_host is None:
            self.postgres_host = (
                os.environ.get("POSTGRES_HOST") or '127.0.0.1'
            )
        else:
            self.postgres_host = postgres_host

        if postgres_port == 0:
            self.postgres_port = int(os.environ.get("POSTGRES_PORT")) or 5432
        else:
            self.postgres_port = postgres_port

        if postgres_db is None:
            self.postgres_db = os.environ.get("POSTGRES_DB") or 'bitcoin'
        else:
            self.postgres_db = postgres_db
            
        if postgres_user is None:
            self.postgres_user = os.environ.get("POSTGRES_USER") or ''
        else:
            self.postgres_user = postgres_user
            
        if postgres_password is None:
            self.postgres_password = os.environ.get("POSTGRES_PASSWORD") or ''
        else:
            self.postgres_password = postgres_password

        self.engine = create_engine(f'postgresql://{self.postgres_user}:{self.postgres_password}@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}')
        self.Session = sessionmaker(bind=self.engine)

    def close(self):
        self.engine.dispose()

    def get_latest_block_number(self):
        with self.Session() as session:
            try:
                latest_balance_change = session.query(BalanceChange).order_by(BalanceChange.block.desc()).first()
                latest_block = latest_balance_change.block
            except Exception as e:
                latest_block = 0
            return latest_block
