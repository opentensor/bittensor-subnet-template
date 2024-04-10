from sqlalchemy import Column, Integer, BigInteger, String, PrimaryKeyConstraint
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class BalanceChange(Base):
    __tablename__   = 'balance_changes'  # Replace with your actual table name

    address     = Column(String, primary_key=True)
    block       = Column(Integer, primary_key=True)
    d_balance   = Column(BigInteger)
    
    __table_args__ = (
        PrimaryKeyConstraint('address', 'block'),
    )
