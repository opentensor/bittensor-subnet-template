from sqlalchemy import Column, Integer, BigInteger, String, PrimaryKeyConstraint, Index, TIMESTAMP
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class BalanceChange(Base):
    __tablename__   = 'balance_changes'

    address     = Column(String, primary_key=True)
    block       = Column(Integer, primary_key=True)
    d_balance   = Column(BigInteger)
    
    __table_args__ = (
        PrimaryKeyConstraint('address', 'block'),
    )


class CurrentBalance(Base):
    __tablename__   = 'current_balances'
    
    address     = Column(String, primary_key=True)
    balance     = Column(BigInteger)
    
    __table_args__ = (
        PrimaryKeyConstraint('address'),
        Index('idx_balance', 'balance')
    )


class Block(Base):
    __tablename__   = 'blocks'
    
    block_height     = Column(Integer, primary_key=True)
    timestamp        = Column(TIMESTAMP)
    
    __table_args__ = (
        PrimaryKeyConstraint('block_height'),
        Index('idx_timestamp', 'timestamp')
    )
