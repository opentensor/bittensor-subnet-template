from sqlalchemy import Column, Integer, BigInteger, String, Date
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Balance(Base):
    __tablename__ = 'balances'  # Replace with your actual table name

    address = Column(String)
    balance = Column(BigInteger)
    block   = Column(Integer)
