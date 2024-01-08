import traceback
from sqlalchemy import create_engine, Column, String, DateTime, func, Integer, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import datetime
import bittensor as bt


Base = declarative_base()

class MinerRegistry(Base):
    __tablename__ = "miner_registry"

    hot_key = Column(String, primary_key=True)
    ip_address = Column(String)
    network = Column(String)
    model_type = Column(String)
    response_time = Column(Float)
    score = Column(Float)
    run_id = Column(String)
    updated = Column(DateTime, default=datetime.datetime.utcnow)

class MinerRegistryManager:
    def __init__(self):
        self.engine = create_engine("sqlite:////data/miner_registry.db")
        Base.metadata.create_all(self.engine)

    def store_miner_metadata(self, hot_key, ip_address, network, model_type, response_time, score, run_id):
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
                existing_miner.run_id = run_id
            else:
                new_miner = MinerRegistry(
                    ip_address=ip_address,
                    hot_key=hot_key,
                    network=network,
                    model_type=model_type,
                    response_time=response_time,
                    score=score,
                    run_id=run_id,
                )
                session.add(new_miner)

            session.commit()
        except Exception as e:
            session.rollback()
            bt.logging.error(f"Error occurred: {traceback.format_exc()}")
        finally:
            session.close()

    def get_miner_distribution(self, all_networks):
        session = sessionmaker(bind=self.engine)()
        try:
            # Initialize distribution with 1 for each network
            miner_distribution = {network: 1 for network in all_networks}

            # Query MinerRegistry, group by network, and count the number of miners in each group
            distribution_query = (
                session.query(MinerRegistry.network, func.count(MinerRegistry.network))
                .group_by(MinerRegistry.network)
                .all()
            )

            # Update the counts in miner_distribution based on the query results
            for network, count in distribution_query:
                miner_distribution[network] = max(count, 1)  # Ensures a minimum count of 1

            return miner_distribution

        except Exception as e:
            bt.logging.error(f"Error occurred: {traceback.format_exc()}")
            return {}
        finally:
            session.close()

    def detect_multiple_run_id(self, run_id, allowed_num=9):
        session = sessionmaker(bind=self.engine)()
        try:
            repeated_run_id = (
                session.query(
                    MinerRegistry.run_id.label('run_id'),
                    func.count(MinerRegistry.run_id)
                )
                .filter(
                    MinerRegistry.run_id == run_id
                )
                .group_by('run_id')
                .having(func.count('run_id') > allowed_num)
                .all()
            )

            for run_id, count in repeated_run_id:
                bt.logging.info(f"run_id {run_id} is used {count} times. allowed_num is max {allowed_num}")

            if len(repeated_run_id) == 0:
                return False

            return True

        except Exception as e:
            bt.logging.error(f"Error occurred: {traceback.format_exc()}")
            return False
        finally:
            session.close()