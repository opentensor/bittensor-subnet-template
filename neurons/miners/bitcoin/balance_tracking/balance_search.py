import os
from neurons.setup_logger import setup_logger

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from .balance_model import Base, BalanceChange

logger = setup_logger("BalanceSearch")


class BalanceSearch:
    def __init__(self, db_url: str = None):
        self.engine = create_engine(db_url)
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
