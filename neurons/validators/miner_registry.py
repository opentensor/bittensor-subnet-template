import os
import traceback

from sqlalchemy import create_engine, Column, String, DateTime, func, Integer, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import datetime

from neurons.validators.scoring import BLOCKCHAIN_IMPORTANCE

Base = declarative_base()


class MinerRegistry(Base):
    __tablename__ = "miner_registry"

    hot_key = Column(String, primary_key=True)
    ip_address = Column(String)
    network = Column(String)
    model_type = Column(String)
    response_time = Column(Float)
    score = Column(Float)
    updated = Column(DateTime, default=datetime.datetime.utcnow)

    def __repr__(self):
        return f"<MinerRegistry(ip_address='{self.ip_address}', hot_key='{self.hot_key}, network='{self.network}', model_type='{self.model_type}', updated='{self.updated}')>"

class MinerBlockRegistry(Base):
    __tablename__ = "miner_block_registry"

    id = Column(Integer, primary_key=True, autoincrement=True)
    hot_key = Column(String)
    network = Column(String)
    model_type = Column(String)
    block_height = Column(Integer)
    updated = Column(DateTime, default=datetime.datetime.utcnow)

class MinerRegistryManager:
    def __init__(self):
        self.engine = create_engine("sqlite:////data/miner_registry.db")
        Base.metadata.create_all(self.engine)

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
            print(f"Error occurred: {traceback.format_exc()}")
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
            print(f"Error occurred: {traceback.format_exc()}")
        finally:
            session.close()

    def store_miner_block_height(self, hot_key, network, model_type, block_height, bitcoin_cheat_factor_sample_size):
        session = sessionmaker(bind=self.engine)()
        try:
            new_miner = MinerBlockRegistry(
                hot_key=hot_key,
                network=network,
                model_type=model_type,
                block_height=block_height
            )
            session.add(new_miner)
            session.commit()

            # Count the number of records for the given hot_key
            count = session.query(MinerBlockRegistry).filter_by(hot_key=hot_key).count()

            # If count exceeds bitcoin_cheat_factor_sample_size, delete the oldest records
            if count > bitcoin_cheat_factor_sample_size:
                # Find the oldest records to delete
                oldest_records = session.query(MinerBlockRegistry) \
                    .filter_by(hot_key=hot_key) \
                    .order_by(MinerBlockRegistry.block_height.asc()) \
                    .limit(count - bitcoin_cheat_factor_sample_size)

                for record in oldest_records:
                    session.delete(record)

                session.commit()

        except Exception as e:
            session.rollback()
            print(f"Error occurred: {traceback.format_exc()}")
        finally:
            session.close()

    def clear_block_heights(self, hot_key, network, model_type):
        session = sessionmaker(bind=self.engine)()
        try:
            session.query(MinerBlockRegistry).filter_by(
                hot_key=hot_key, network=network, model_type=model_type
            ).delete()
            session.commit()
        except Exception as e:
            session.rollback()
            print(f"Error occurred: {traceback.format_exc()}")
        finally:
            session.close()

    def calculate_cheat_factor(self, hot_key, network, model_type, sample_size=256):
        session = sessionmaker(bind=self.engine)()
        try:
            entries = (
                session.query(MinerBlockRegistry.block_height)
                .filter(
                    MinerBlockRegistry.hot_key == hot_key,
                    MinerBlockRegistry.network == network,
                    MinerBlockRegistry.model_type == model_type
                )
                .order_by(MinerBlockRegistry.updated.desc())
                .limit(sample_size)
                .all()
            )

            if len(entries) < sample_size:
                return 0

            block_heights = [entry[0] for entry in entries]
            from collections import Counter
            counts = Counter(block_heights)
            repeats = sum(count - 1 for count in counts.values() if count > 1)
            total = len(block_heights)
            cheat_factor = repeats / total
            return cheat_factor

        except Exception as e:
            print(f"Error occurred: {traceback.format_exc()}")
            return 0
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
            print(f"Error occurred: {traceback.format_exc()}")
            return {}
        finally:
            session.close()