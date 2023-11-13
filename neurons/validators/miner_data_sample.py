from sqlalchemy import create_engine, Column, String, DateTime, Integer
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import datetime
import scipy.stats as stats

Base = declarative_base()


class MinerDataSample(Base):
    __tablename__ = "miner_data_samples"

    id = Column(Integer, primary_key=True)
    hot_key = Column(String)
    network = Column(String)
    model_type = Column(String)
    block_height = Column(Integer)
    recorded = Column(DateTime, default=datetime.datetime.utcnow)

    def __repr__(self):
        return f"<MinerDataSample(id='{self.id}', hot_key='{self.hot_key}', network='{self.network}', model_type='{self.model_type}', block_height='{self.block_height}', recorded='{self.recorded}')>"


class MinerDataSample:
    def __init__(self, db_path="sqlite:///miner_data_samples.db"):
        self.engine = create_engine(db_path)

    def is_block_heights_random(self, hot_key, network, model_type, n=100):
        session = sessionmaker(bind=self.engine)()
        try:
            # Fetch the last N block heights
            block_heights = (
                session.query(MinerDataSample.block_height)
                .filter(
                    MinerDataSample.hot_key == hot_key,
                    MinerDataSample.network == network,
                    MinerDataSample.model_type == model_type,
                )
                .order_by(MinerDataSample.recorded.desc())
                .limit(n)
                .all()
            )

            if len(block_heights) < n:
                return True  # Not enough data to determine randomness, so we assume its correct

            # Convert to a list of integers
            block_heights = [bh[0] for bh in block_heights]

            # Define bins for the Chi-Square test
            num_bins = 10  # Adjust the number of bins as needed
            bins = pd.cut(block_heights, num_bins, labels=False)

            # Perform the Chi-Square Test
            chi_square_stat, p_value = stats.chisquare(pd.value_counts(bins))

            # Determine if the block heights are random based on the p-value
            # Typically, if p < 0.05, we reject the null hypothesis of identical average scores
            return p_value >= 0.05
        except Exception as e:
            print(f"Error occurred: {e}")
            return False
        finally:
            session.close()

    def store_miner_data_sample(self, hot_key, network, model_type, data_sample):
        session = sessionmaker(bind=self.engine)()
        try:
            new_data_sample = MinerDataSample(
                hot_key=hot_key,
                network=network,
                model_type=model_type,
                block_height=data_sample,
            )
            session.add(new_data_sample)
            session.commit()
        except Exception as e:
            session.rollback()
            print(f"Error occurred: {e}")
        finally:
            session.close()
