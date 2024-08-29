import unittest
from datetime import datetime, timedelta
from rewarder import CompetitionLeader, RewarderConfig, Rewarder

class TestRewarder(unittest.TestCase):

    def test_single_competition_single_leader(self):
        """Test case 1: Only one competition with 1 leader -> leader takes it all"""
        competitions_leaders = {
            "competition-1": CompetitionLeader(hotkey="leader-1", leader_since=datetime.now())
        }
        scores = {"leader-1": 0}
        rewarder_config = RewarderConfig(competition_leader_mapping=competitions_leaders, scores=scores)
        rewarder = Rewarder(config=rewarder_config)
        
        rewarder.update_scores()

        # Assert that the leader takes it all
        self.assertAlmostEqual(rewarder.scores["leader-1"], 1.0)

    def test_three_competitions_three_leaders_no_reduction(self):
        """Test case 2: 3 competitions with 3 different leaders, no reduction -> all have 33% of the shares"""
        reward_split_by_three = 1 / 3
        competitions_leaders = {
            "competition-1": CompetitionLeader(hotkey="leader-1", leader_since=datetime.now()),
            "competition-2": CompetitionLeader(hotkey="leader-2", leader_since=datetime.now()),
            "competition-3": CompetitionLeader(hotkey="leader-3", leader_since=datetime.now())
        }
        scores = {"leader-1": 0, "leader-2": 0, "leader-3": 0}
        rewarder_config = RewarderConfig(competition_leader_mapping=competitions_leaders, scores=scores)
        rewarder = Rewarder(config=rewarder_config)
        rewarder.update_scores()

        # Assert that all leaders have roughly 1/3 of the shares
        self.assertAlmostEqual(rewarder.scores["leader-1"], reward_split_by_three, places=2)
        self.assertAlmostEqual(rewarder.scores["leader-2"], reward_split_by_three, places=2)
        self.assertAlmostEqual(rewarder.scores["leader-3"], reward_split_by_three, places=2)

    def test_three_competitions_three_leaders_with_reduction(self):
        """Test case 3: 3 competitions with 3 different leaders, one has a reduced share by 10%"""
        first_competion_leader_since = datetime.now() - timedelta(days=21)

        base_share = 1/3
        reduction_factor = 0.9  # 10% reduction
        expected_share_leader_1 = base_share * reduction_factor
        expected_reduction = base_share - expected_share_leader_1
        expected_share_leader_2_3 = base_share + (expected_reduction / 2)  # Distributed reduction
        
        scores = {"leader-1": 0, "leader-2": 0, "leader-3": 0}

        competitions_leaders = {
            "competition-1": CompetitionLeader(hotkey="leader-1", leader_since=first_competion_leader_since),
            "competition-2": CompetitionLeader(hotkey="leader-2", leader_since=datetime.now()),
            "competition-3": CompetitionLeader(hotkey="leader-3", leader_since=datetime.now())
        }
        
        rewarder_config = RewarderConfig(competition_leader_mapping=competitions_leaders, scores=scores)
        rewarder = Rewarder(config=rewarder_config)

        rewarder.update_scores()
        # Assert that leader-1 has the reduced share and others are higher
        self.assertAlmostEqual(rewarder.scores["leader-1"], expected_share_leader_1, places=2)
        self.assertAlmostEqual(rewarder.scores["leader-2"], expected_share_leader_2_3, places=2)
        self.assertAlmostEqual(rewarder.scores["leader-3"], expected_share_leader_2_3, places=2)

    def test_three_competitions_three_leaders_two_reductions(self):
        """Test case 4: 3 competitions with 3 different leaders, two with reduced shares"""
        competitions_leaders = {
            "competition-1": CompetitionLeader(hotkey="leader-1", leader_since=datetime.now() - timedelta(days=21)),
            "competition-2": CompetitionLeader(hotkey="leader-2", leader_since=datetime.now() - timedelta(days=35)),
            "competition-3": CompetitionLeader(hotkey="leader-3", leader_since=datetime.now())
        }
        scores = {"leader-1": 0, "leader-2": 0, "leader-3": 0}
        rewarder_config = RewarderConfig(competition_leader_mapping=competitions_leaders, scores=scores)
        rewarder = Rewarder(config=rewarder_config)

        rewarder.update_scores()

        base_share = 1 / 3
        reduction_factor_leader_1 = 0.9  # 10% reduction
        reduction_factor_leader_2 = 0.7  # 30% reduction

        expected_share_leader_1 = base_share * reduction_factor_leader_1
        expected_share_leader_2 = base_share * reduction_factor_leader_2
        expected_share_leader_3 = base_share
        # Calculate distributed reduction
        remaining_share_leader_1 = base_share - expected_share_leader_1
        remaining_share_leader_2 = base_share - expected_share_leader_2

        # Leaders 2 and 3 gets their base share plus the distributed reduction from Leader 1
        expected_share_leader_2 += remaining_share_leader_1 / 2
        expected_share_leader_3 += remaining_share_leader_1 / 2

        # Leaders 1 and 3 gets their base share plus the distributed reduction from Leader 2

        expected_share_leader_1 += remaining_share_leader_2 / 2
        expected_share_leader_3 += remaining_share_leader_2 / 2

        self.assertAlmostEqual(rewarder.scores["leader-1"], expected_share_leader_1, places=2)
        self.assertAlmostEqual(rewarder.scores["leader-2"], expected_share_leader_2, places=2)
        self.assertAlmostEqual(rewarder.scores["leader-3"], expected_share_leader_3, places=2)

    def test_three_competitions_three_leaders_all_different_reductions(self):
        """Test case 5: All competitors have different degrees of reduced shares"""
        competitions_leaders = {
            "competition-1": CompetitionLeader(hotkey="leader-1", leader_since=datetime.now() - timedelta(days=21)),
            "competition-2": CompetitionLeader(hotkey="leader-2", leader_since=datetime.now() - timedelta(days=35)),
            "competition-3": CompetitionLeader(hotkey="leader-3", leader_since=datetime.now() - timedelta(days=49))
        }
        scores = {"leader-1": 0, "leader-2": 0, "leader-3": 0}
        rewarder_config = RewarderConfig(competition_leader_mapping=competitions_leaders, scores=scores)
        rewarder = Rewarder(config=rewarder_config)

        rewarder.update_scores()

        base_share = 1 / 3
        reduction_factor_leader_1 = 0.9  # 10% reduction
        reduction_factor_leader_2 = 0.7  # 30% reduction
        reduction_factor_leader_3 = 0.5  # 50% reduction

        expected_share_leader_1 = base_share * reduction_factor_leader_1
        expected_share_leader_2 = base_share * reduction_factor_leader_2
        expected_share_leader_3 = base_share * reduction_factor_leader_3
        # Calculate distributed reduction
        remaining_share_leader_1 = base_share - expected_share_leader_1
        remaining_share_leader_2 = base_share - expected_share_leader_2
        remaining_share_leader_3 = base_share - expected_share_leader_3

        # Leaders 2 and 3 gets their base share plus the distributed reduction from Leader 1
        expected_share_leader_2 += remaining_share_leader_1 / 2
        expected_share_leader_3 += remaining_share_leader_1 / 2

        # Leaders 1 and 3 gets their base share plus the distributed reduction from Leader 2
        expected_share_leader_1 += remaining_share_leader_2 / 2
        expected_share_leader_3 += remaining_share_leader_2 / 2

        # Leaders 1 and 2 gets their base share plus the distributed reduction from Leader 3
        expected_share_leader_1 += remaining_share_leader_3 / 2
        expected_share_leader_2 += remaining_share_leader_3 / 2

        self.assertAlmostEqual(rewarder.scores["leader-1"], expected_share_leader_1, places=2)
        self.assertAlmostEqual(rewarder.scores["leader-2"], expected_share_leader_2, places=2)
        self.assertAlmostEqual(rewarder.scores["leader-3"], expected_share_leader_3, places=2)

    def test_three_competitions_three_leaders_all_same_reductions(self):
        """Test case 6: All competitors have the same amount of reduced shares"""
        competitions_leaders = {
            "competition-1": CompetitionLeader(hotkey="leader-1", leader_since=datetime.now() - timedelta(days=21)),
            "competition-2": CompetitionLeader(hotkey="leader-2", leader_since=datetime.now() - timedelta(days=21)),
            "competition-3": CompetitionLeader(hotkey="leader-3", leader_since=datetime.now() - timedelta(days=21))
        }
        scores = {"leader-1": 0, "leader-2": 0, "leader-3": 0}
        rewarder_config = RewarderConfig(competition_leader_mapping=competitions_leaders, scores=scores)
        rewarder = Rewarder(config=rewarder_config)

        rewarder.update_scores()

        base_share = 1 / 3
        reduction_factor = 0.9  # 10% reduction for all

        expected_share_leader_1 = base_share * reduction_factor
        expected_share_leader_2 = base_share * reduction_factor
        expected_share_leader_3 = base_share * reduction_factor

        # Calculate distributed reduction
        remaining_share_leader_1 = base_share - expected_share_leader_1
        remaining_share_leader_2 = base_share - expected_share_leader_2
        remaining_share_leader_3 = base_share - expected_share_leader_3

        # Leaders 2 and 3 gets their base share plus the distributed reduction from Leader 1
        expected_share_leader_2 += remaining_share_leader_1 / 2
        expected_share_leader_3 += remaining_share_leader_1 / 2

        # Leaders 1 and 3 gets their base share plus the distributed reduction from Leader 2
        expected_share_leader_1 += remaining_share_leader_2 / 2
        expected_share_leader_3 += remaining_share_leader_2 / 2

        # Leaders 1 and 2 gets their base share plus the distributed reduction from Leader 3
        expected_share_leader_1 += remaining_share_leader_3 / 2
        expected_share_leader_2 += remaining_share_leader_3 / 2

        # All should have the same shares
        self.assertAlmostEqual(rewarder.scores["leader-1"], expected_share_leader_1, places=2)
        self.assertAlmostEqual(rewarder.scores["leader-2"], expected_share_leader_2, places=2)
        self.assertAlmostEqual(rewarder.scores["leader-3"], expected_share_leader_3, places=2)

    def test_three_competitions_three_leaders_all_maximum_reductions(self):
        """Test case 7: All competitors have maximum reduced shares (90%)"""
        competitions_leaders = {
            "competition-1": CompetitionLeader(hotkey="leader-1", leader_since=datetime.now() - timedelta(days=91)),
            "competition-2": CompetitionLeader(hotkey="leader-2", leader_since=datetime.now() - timedelta(days=91)),
            "competition-3": CompetitionLeader(hotkey="leader-3", leader_since=datetime.now() - timedelta(days=91))
        }
        scores = {"leader-1": 0, "leader-2": 0, "leader-3": 0}
        rewarder_config = RewarderConfig(competition_leader_mapping=competitions_leaders, scores=scores)
        rewarder = Rewarder(config=rewarder_config)

        rewarder.update_scores()

        base_share = 1 / 3
        reduction_factor = 0.1  # 90% reduction for all

        expected_share_leader_1 = base_share * reduction_factor
        expected_share_leader_2 = base_share * reduction_factor
        expected_share_leader_3 = base_share * reduction_factor

        # Calculate distributed reduction
        remaining_share_leader_1 = base_share - expected_share_leader_1
        remaining_share_leader_2 = base_share - expected_share_leader_2
        remaining_share_leader_3 = base_share - expected_share_leader_3

        # Leaders 2 and 3 gets their base share plus the distributed reduction from Leader 1
        expected_share_leader_2 += remaining_share_leader_1 / 2
        expected_share_leader_3 += remaining_share_leader_1 / 2

        # Leaders 1 and 3 gets their base share plus the distributed reduction from Leader 2
        expected_share_leader_1 += remaining_share_leader_2 / 2
        expected_share_leader_3 += remaining_share_leader_2 / 2

        # Leaders 1 and 2 gets their base share plus the distributed reduction from Leader 3
        expected_share_leader_1 += remaining_share_leader_3 / 2
        expected_share_leader_2 += remaining_share_leader_3 / 2

        # All should have the same shares
        self.assertAlmostEqual(rewarder.scores["leader-1"], expected_share_leader_1, places=2)
        self.assertAlmostEqual(rewarder.scores["leader-2"], expected_share_leader_2, places=2)
        self.assertAlmostEqual(rewarder.scores["leader-3"], expected_share_leader_3, places=2)

    def test_three_competitions_two_competitors(self):
        """Test case 8: 3 competitions but only 2 competitors"""
        competitions_leaders = {
            "competition-1": CompetitionLeader(hotkey="leader-1", leader_since=datetime.now() - timedelta(days=21)),
            "competition-2": CompetitionLeader(hotkey="leader-1", leader_since=datetime.now() - timedelta(days=10)),
            "competition-3": CompetitionLeader(hotkey="leader-2", leader_since=datetime.now())
        }
        scores = {"leader-1": 0, "leader-2": 0}
        rewarder_config = RewarderConfig(competition_leader_mapping=competitions_leaders, scores=scores)
        rewarder = Rewarder(config=rewarder_config)

        rewarder.update_scores()

        base_share = 1 / 3
        reduction_factor_leader_1_competition_1 = 0.9  # 10% reduction for 21 days

        # Calculate expected scores
        expected_share_leader_1_competition_1 = base_share * reduction_factor_leader_1_competition_1
        expected_share_leader_1_competition_2 = base_share
        expected_share_leader_2 = base_share

        remaining_share_leader_1_competition_1 = base_share - expected_share_leader_1_competition_1
        # The competitors of competition 2 and 3 (including leader-1) get the distributed reduction    
        expected_score_leader_1 = expected_share_leader_1_competition_1 + expected_share_leader_1_competition_2\
              + remaining_share_leader_1_competition_1 / 2
        expected_score_leader_2 = expected_share_leader_2 + remaining_share_leader_1_competition_1 / 2

        self.assertAlmostEqual(rewarder.scores["leader-1"], expected_score_leader_1, places=2)
        self.assertAlmostEqual(rewarder.scores["leader-2"], expected_score_leader_2, places=2)

    def test_five_competitions_three_competitors_two_repeating(self):
        """Test case 9: 5 competitions with 3 competitors, 2 of them are repeating"""
        competitions_leaders = {
            "competition-1": CompetitionLeader(hotkey="leader-1", leader_since=datetime.now() - timedelta(days=21)),  # 10% reduction
            "competition-2": CompetitionLeader(hotkey="leader-2", leader_since=datetime.now() - timedelta(days=10)),  # No reduction
            "competition-3": CompetitionLeader(hotkey="leader-1", leader_since=datetime.now()),  # No reduction
            "competition-4": CompetitionLeader(hotkey="leader-3", leader_since=datetime.now() - timedelta(days=35)),  # 30% reduction
            "competition-5": CompetitionLeader(hotkey="leader-2", leader_since=datetime.now())  # No reduction
        }
        scores = {"leader-1": 0, "leader-2": 0, "leader-3": 0}
        rewarder_config = RewarderConfig(competition_leader_mapping=competitions_leaders, scores=scores)
        rewarder = Rewarder(config=rewarder_config)

        rewarder.update_scores()

        base_share = 1 / 5
        reduction_factor_leader_1_competition_1 = 0.9  # 10% reduction for 21 days
        reduction_factor_leader_3_competition_4 = 0.7  # 30% reduction for 35 days

        # Calculate expected shares for each leader
        expected_share_leader_1_competition_1 = base_share * reduction_factor_leader_1_competition_1
        expected_share_leader_1_competition_3 = base_share
        expected_share_leader_2_competition_2 = base_share
        expected_share_leader_2_competition_5 = base_share
        expected_share_leader_3_competition_4 = base_share * reduction_factor_leader_3_competition_4

        remaining_share_leader_1_competition_1 = base_share - expected_share_leader_1_competition_1
        remaining_share_leader_3_competition_4 = base_share - expected_share_leader_3_competition_4

        # Calculate final scores with distributed reduction shares
        expected_score_leader_1 = expected_share_leader_1_competition_1 + expected_share_leader_1_competition_3\
              + (remaining_share_leader_1_competition_1 / 3) + (remaining_share_leader_3_competition_4 / 2)
        expected_score_leader_2 = expected_share_leader_2_competition_2 + expected_share_leader_2_competition_5\
              + (remaining_share_leader_1_competition_1 / 3) + (remaining_share_leader_3_competition_4 / 2)
        expected_score_leader_3 = expected_share_leader_3_competition_4 + (remaining_share_leader_1_competition_1 / 3)

        self.assertAlmostEqual(rewarder.scores["leader-1"], expected_score_leader_1, places=2)
        self.assertAlmostEqual(rewarder.scores["leader-2"], expected_score_leader_2, places=2)
        self.assertAlmostEqual(rewarder.scores["leader-3"], expected_score_leader_3, places=2)


if __name__ == "__main__":
    unittest.main()
