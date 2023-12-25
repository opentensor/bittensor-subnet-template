import traceback
from sqlalchemy import create_engine, Column, String, DateTime, func, Integer, Float, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import datetime
import bittensor as bt

Base = declarative_base()

class BlacklistRegistry(Base):
    __tablename__ = "blacklist_registry"

    id = Column(Integer, primary_key=True, autoincrement=True)
    ip_address = Column(String)
    hot_key = Column(String)
    updated = Column(DateTime, default=datetime.datetime.utcnow)

    # Define the composite index
    __table_args__ = (Index('ix_ip_hotkey', 'ip_address', 'hot_key'),)

class BlacklistRegistryManager:
    def __init__(self, connection_string="sqlite:////data/blacklist_registry.db"):
        self.engine = create_engine(connection_string)
        Base.metadata.create_all(self.engine)

    def get_blacklist(self):
        session = sessionmaker(bind=self.engine)()
        try:
            return session.query(BlacklistRegistry).all()
        except Exception as e:
            bt.logging.error(f"Error occurred: {traceback.format_exc()}")
        finally:
            session.close()

    def remove_all(self):
        session = sessionmaker(bind=self.engine)()
        try:
            session.query(BlacklistRegistry).delete()
            session.commit()
        except Exception as e:
            session.rollback()
            bt.logging.error(f"Error occurred: {traceback.format_exc()}")
        finally:
            session.close()

    def try_add_to_blacklist(self, ip_address, hot_key):
        session = sessionmaker(bind=self.engine)()
        try:
            # check if by ip_address and hot_key
            existing = session.query(BlacklistRegistry).filter(BlacklistRegistry.ip_address == ip_address, BlacklistRegistry.hot_key == hot_key).first()
            if existing:
                return

            blacklist = BlacklistRegistry(ip_address=ip_address, hot_key=hot_key)
            session.add(blacklist)
            session.commit()
        except Exception as e:
            session.rollback()
            bt.logging.error(f"Error occurred: {traceback.format_exc()}")
        finally:
            session.close()
