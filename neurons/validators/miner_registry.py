from sqlalchemy import create_engine, Column, String, DateTime, func, Integer, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import datetime

Base = declarative_base()


class MinerRegistry(Base):
    __tablename__ = "miner_registry"

    hot_key = Column(String, primary_key=True)
    ip_address = Column(String)
    network = Column(String)
    model_type = Column(String)
    response_time = Column(Integer)
    score = Column(Float)
    updated = Column(DateTime, default=datetime.datetime.utcnow)

    def __repr__(self):
        return f"<MinerRegistry(ip_address='{self.ip_address}', hot_key='{self.hot_key}, network='{self.network}', model_type='{self.model_type}', updated='{self.updated}')>"


class MinerRegistryManager:
    def __init__(self, db_path="sqlite:///miner_registry.db"):
        self.engine = create_engine(db_path)
        Base.metadata.create_all(self.engine)

    def get_miner_distribution(self):
        pass

    # this method will be obsolete once we have a miner registry
    def get_miner_proportion(self, network, model_type):
        session = sessionmaker(bind=self.engine)()
        try:
            total_miners = session.query(func.count(MinerRegistry.ip_address)).scalar()
            matching_miners = (
                session.query(func.count(MinerRegistry.ip_address))
                .filter(
                    MinerRegistry.network == network,
                    MinerRegistry.model_type == model_type,
                )
                .scalar()
            )

            proportion = matching_miners / total_miners if total_miners > 0 else 0
            return proportion
        except Exception as e:
            print(f"Error occurred: {e}")
            return 0
        finally:
            session.close()

    def store_miner_metadata(self, hot_key, ip_address, network, model_type, response_time, score):
        session = sessionmaker(bind=self.engine)()
        try:
            existing_miner = (
                session.query(MinerRegistry).filter_by(hot_key=hot_key).first()
            )

            if existing_miner:
                existing_miner.network = network
                existing_miner.ip_address = ip_address
                existing_miner.model_type = model_type
                existing_miner.response_time = response_time
                existing_miner.updated = datetime.datetime.utcnow()
                existing_miner.score = score
            else:
                new_miner = MinerRegistry(
                    ip_address=ip_address,
                    hot_key=hot_key,
                    network=network,
                    model_type=model_type,
                    response_time=response_time,
                    score=score,
                )
                session.add(new_miner)

            session.commit()
        except Exception as e:
            session.rollback()
            print(f"Error occurred: {e}")
        finally:
            session.close()
