from sqlalchemy import create_engine, Column, String, DateTime, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import datetime

Base = declarative_base()


class MinerRegistry(Base):
    __tablename__ = "miner_registry"

    hot_key = Column(String, primary_key=True)
    ip_address = Column(String)
    network = Column(String)
    assets = Column(String)
    model_type = Column(String)
    updated = Column(DateTime, default=datetime.datetime.utcnow)

    def __repr__(self):
        return f"<MinerRegistry(ip_address='{self.ip_address}', hot_key='{self.hot_key}, network='{self.network}', assets='{self.assets}', model_type='{self.model_type}', updated='{self.updated}')>"


class MinerRegistryManager:
    def __init__(self, db_path="sqlite:///miner_registry.db"):
        self.engine = create_engine(db_path)

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

    def store_miner_metadata(self, hot_key, ip_address, network, assets, model_type):
        session = sessionmaker(bind=self.engine)()
        try:
            existing_miner = (
                session.query(MinerRegistry).filter_by(hot_key=hot_key).first()
            )

            if existing_miner:
                existing_miner.network = network
                existing_miner.ip_address = ip_address
                existing_miner.assets = assets
                existing_miner.model_type = model_type
                existing_miner.updated = datetime.datetime.utcnow()
            else:
                new_miner = MinerRegistry(
                    ip_address=ip_address,
                    hot_key=hot_key,
                    network=network,
                    assets=assets,
                    model_type=model_type,
                )
                session.add(new_miner)

            session.commit()
        except Exception as e:
            session.rollback()
            print(f"Error occurred: {e}")
        finally:
            session.close()
