import os
from neurons.setup_logger import setup_logger

from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.sql import select

from .balance_model import Base, BalanceChange

logger = setup_logger("BalanceIndexer")


class BalanceIndexer:
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
        
        # check if table exists and create if not
        connection = self.engine.connect()

        # Create an inspector
        inspector = inspect(self.engine)

        # Check if the table already exists
        if not inspector.has_table('balance_changes'):
            # Create the table in the database
            Base.metadata.create_all(self.engine)
            logger.info("Created `balance_changes` table")

        # Close the connection
        connection.close()

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


    from decimal import getcontext

    # Set the precision high enough to handle satoshis for Bitcoin transactions
    getcontext().prec = 28

    def create_rows_focused_on_balance_changes(self, in_memory_graph, _bitcoin_node):
        block_node = in_memory_graph["block"]
        block_height = block_node.block_height
        transactions = block_node.transactions

        balance_changes_by_address = {}
        changed_addresses = []

        for tx in transactions:
            in_amount_by_address, out_amount_by_address, input_addresses, output_addresses, in_total_amount, out_total_amount = _bitcoin_node.process_in_memory_txn_for_indexing(tx)
            
            for address in input_addresses:
                if not address in balance_changes_by_address:
                    balance_changes_by_address[address] = 0
                    changed_addresses.append(address)
                balance_changes_by_address[address] -= in_amount_by_address[address]
            
            for address in output_addresses:
                if not address in balance_changes_by_address:
                    balance_changes_by_address[address] = 0
                    changed_addresses.append(address)
                balance_changes_by_address[address] += out_amount_by_address[address]

        logger.info(f"Adding {len(changed_addresses)} row(s)...")
        
        new_rows = [BalanceChange(address=address, d_balance=balance_changes_by_address[address], block=block_height) for address in changed_addresses]

        with self.Session() as session:
            try:
                # Add the new rows to the session
                session.add_all(new_rows)
                
                # Commit the session to save the changes to the database
                session.commit()
                
                return True
                
            except SQLAlchemyError as e:
                # Rollback the session in case of an error
                session.rollback()
                logger.error(f"An exception occurred: {e}")
                
                return False
