from contextlib import contextmanager
from sqlalchemy import create_engine, Column, Integer, String, DateTime, ForeignKey, UniqueConstraint, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, scoped_session, relationship, selectinload, subqueryload, joinedload
from datetime import datetime

Base = declarative_base()

class Miner(Base):
    __tablename__ = 'miners'
    id = Column(Integer, primary_key=True)
    uid = Column(String, nullable=False)
    hotkey = Column(String, nullable=False)
    uptime_start = Column(DateTime, default=datetime.utcnow)
    deregistered_date = Column(DateTime, nullable=True)
    is_deregistered = Column(Boolean, default=False)
    __table_args__ = (UniqueConstraint('uid', 'hotkey', name='_uid_hotkey_uc'),)
    downtimes = relationship('DowntimeLog', back_populates='miner', order_by="desc(DowntimeLog.start_time)")

class DowntimeLog(Base):
    __tablename__ = 'downtime_logs'
    id = Column(Integer, primary_key=True)
    miner_id = Column(Integer, ForeignKey('miners.id'))
    start_time = Column(DateTime)
    end_time = Column(DateTime, nullable=True)
    miner = relationship('Miner', back_populates='downtimes')

class UptimeManager:
    def __init__(self, db_url='sqlite:///miners.db'):
        self.engine = create_engine(db_url)
        Base.metadata.create_all(self.engine)
        self.session_factory = sessionmaker(bind=self.engine)
        self.Session = scoped_session(self.session_factory)


    @contextmanager
    def session_scope(self):
        """Provide a transactional scope around a series of operations."""
        session = self.Session()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def get_miner(self, uid, hotkey):
        with self.session_scope() as session:
            # Initialize the query on Miner
            query = session.query(Miner).options(joinedload(Miner.downtimes))

            # Apply filtering
            if hotkey is not None:
                query = query.filter(Miner.uid == uid, Miner.hotkey == hotkey)
            else:
                query = query.filter(Miner.uid == uid)

            # Fetch the first result that matches the query
            miner = query.first()

            if miner:
                # Expunge the object from the session to detach it
                session.expunge(miner)
                # Return the detached miner object
                return miner

            return None

    def try_update_miner(self, uid, hotkey):
        with self.session_scope() as session:
            existing_miner = session.query(Miner).filter(Miner.uid == uid).first()
            if existing_miner and existing_miner.hotkey != hotkey:
                existing_miner.is_deregistered = True
                existing_miner.deregistered_date = datetime.utcnow()
            if not existing_miner or existing_miner.is_deregistered:
                new_miner = Miner(uid=uid, hotkey=hotkey)
                session.add(new_miner)

    def up(self, uid, hotkey):
        with self.session_scope() as session:
            miner = session.query(Miner).filter(Miner.uid == uid, Miner.hotkey == hotkey).one()
            if miner:
                self.end_last_downtime(miner.id, session)
                return True
            return False

    def down(self, uid, hotkey):
        """Record the start of a new downtime for a miner, only if the last downtime is closed."""
        with self.session_scope() as session:
            miner = session.query(Miner).filter(Miner.uid == uid, Miner.hotkey == hotkey).one()
            if miner:
                # Check the most recent downtime entry
                most_recent_downtime = session.query(DowntimeLog).filter(DowntimeLog.miner_id == miner.id).order_by(DowntimeLog.start_time.desc()).first()

                # Check if there is no downtime recorded or if the most recent downtime is closed
                if not most_recent_downtime or most_recent_downtime.end_time is not None:
                    new_downtime = DowntimeLog(miner_id=miner.id, start_time=datetime.utcnow(), end_time=None)
                    session.add(new_downtime)
                    return True  # Indicate successful addition of new downtime
            return False  # No new downtime was added, either miner does not exist or last downtime is still open


    def end_last_downtime(self, miner_id, session):
        last_downtime = session.query(DowntimeLog).filter(DowntimeLog.miner_id == miner_id, DowntimeLog.end_time == None).first()
        if last_downtime:
            last_downtime.end_time = datetime.utcnow()

    def calculate_uptime(self, miner_id, period_seconds):
        with self.session_scope() as session:
            miner = session.query(Miner).filter(Miner.id == miner_id).one()
            active_period_end = miner.deregistered_date if miner.is_deregistered else datetime.utcnow()
            active_period_start = miner.uptime_start
            active_seconds = (active_period_end - active_period_start).total_seconds()

            total_downtime = sum(
                (log.end_time - log.start_time).total_seconds()
                for log in miner.downtimes
                if log.start_time >= active_period_start and log.end_time and log.end_time <= active_period_end
            )

            print(f"Active Seconds: {active_seconds}, Total Downtime: {total_downtime}")  # Debug output

            actual_uptime_seconds = max(0, active_seconds - total_downtime)
            return actual_uptime_seconds / active_seconds if active_seconds > 0 else 0


    def get_uptime_scores(self, miner_id):
        day = self.calculate_uptime(miner_id, 86400)
        week = self.calculate_uptime(miner_id, 604800)
        month = self.calculate_uptime(miner_id, 2629746)
        average = (day + week + month) / 3
        return {'daily': day, 'weekly': week, 'monthly': month, 'average': average}
