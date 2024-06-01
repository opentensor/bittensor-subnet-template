import unittest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session

from neurons.validators.uptime import Downtimes, Base, MinerUptimeManager, Miners

class TestMinerUptimeManager(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine('sqlite:///:memory:')
        Base.metadata.create_all(self.engine)
        self.Session = scoped_session(sessionmaker(bind=self.engine))
        self.uptime_manager = MinerUptimeManager('sqlite:///:memory:')
        self.uptime_manager.Session = self.Session  # Ensure we use the same session factory
        self.session = self.Session()

    def tearDown(self):
        self.session.rollback()
        self.session.close()
        self.Session.remove()
        self.engine.dispose()

    def test_add_miner_for_first_time_its_up(self):
        self.uptime_manager.up(123, 'key123')
        miner = self.uptime_manager.get_miner('key123')

        self.assertIsNotNone(miner)
        self.assertEqual(miner.uid, 123)
        self.assertEqual(miner.hotkey, 'key123')

    def test_update_miner__when_up_with_different_uid(self):
        self.uptime_manager.up(123, 'key123')
        self.uptime_manager.up(100, 'key123')

        miner = self.uptime_manager.get_miner('key123')
        self.assertEqual(miner.uid, 100)

    def test_miner_up_and_down(self):
        self.uptime_manager.up(100, 'key123')
        self.uptime_manager.down(100, 'key123')
        self.uptime_manager.up(100, 'key123')

        miner = self.uptime_manager.get_miner('key123')
        self.assertTrue(len(miner.downtimes) == 1)

        self.uptime_manager.up(200, 'key123')
        miner = self.uptime_manager.get_miner('key123')
        self.assertTrue(len(miner.downtimes) == 1)

        uptimes = self.uptime_manager.get_uptime_scores('key123')
        print(f"{uptimes=}")


if __name__ == '__main__':
    unittest.main()
