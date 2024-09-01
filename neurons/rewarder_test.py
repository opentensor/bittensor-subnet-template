import pytest
from datetime import datetime, timedelta
from .rewarder import CompetitionLeader, Score, RewarderConfig, Rewarder

def test_update_scores_single_competitor():
    # Set up initial data for a single competitor
    competition_leaders = {
        "competition1": CompetitionLeader(hotkey="competitor1", leader_since=datetime.now() - timedelta(days=10))
    }

    scores = {
        "competitor1": Score(score=0.0, reduction=0.0)
    }

    # Set up the configuration with a single competition and a single competitor
    rewarder_config = RewarderConfig(
        competitionID_to_leader_hotkey_map=competition_leaders,
        hotkey_to_score_map=scores
    )

    rewarder = Rewarder(rewarder_config)
    rewarder.update_scores()

    # Check the updated scores and reductions for the single competitor
    updated_score = rewarder.scores["competitor1"].score
    updated_reduction = rewarder.scores["competitor1"].reduction

    # # With only one competitor, they should receive the full score of 1.0
    expected_score = 1.0
    expected_reduction = 0.0

    assert updated_score == expected_score, f"Expected score: {expected_score}, got: {updated_score}"
    assert updated_reduction == expected_reduction, f"Expected reduction: {expected_reduction}, got: {updated_reduction}"

def test_update_scores_multiple_competitors_no_reduction():
    # Set up initial data for multiple competitors
    competition_leaders = {
        "competition1": CompetitionLeader(hotkey="competitor1", leader_since=datetime.now() - timedelta(days=10)),
        "competition2": CompetitionLeader(hotkey="competitor2", leader_since=datetime.now() - timedelta(days=10)),
        "competition3": CompetitionLeader(hotkey="competitor3", leader_since=datetime.now() - timedelta(days=10))
    }

    scores = {
        "competitor1": Score(score=0.0, reduction=0.0),
        "competitor2": Score(score=0.0, reduction=0.0),
        "competitor3": Score(score=0.0, reduction=0.0)
    }

    # Set up the configuration with multiple competitions and multiple competitors
    rewarder_config = RewarderConfig(
        competitionID_to_leader_hotkey_map=competition_leaders,
        hotkey_to_score_map=scores
    )

    rewarder = Rewarder(rewarder_config)
    rewarder.update_scores()

    # Check the updated scores and reductions for the multiple competitors
    updated_scores = {hotkey: score.score for hotkey, score in rewarder.scores.items()}
    updated_reductions = {hotkey: score.reduction for hotkey, score in rewarder.scores.items()}

    # With multiple competitors and no reductions, they should all receive the same score of 1/3
    expected_score = 1/3
    expected_reduction = 0.0

    for _, score in updated_scores.items():
        assert score == expected_score, f"Expected score: {expected_score}, got: {score}"

    for _, reduction in updated_reductions.items():
        assert reduction == expected_reduction, f"Expected reduction: {expected_reduction}, got: {reduction}"

def test_update_scores_multiple_competitors_with_some_reduced_shares():
    # Set up initial data for multiple competitors
    competition_leaders = {
        "competition1": CompetitionLeader(hotkey="competitor1", leader_since=datetime.now() - timedelta(days=30 + 3 * 7)),
        "competition2": CompetitionLeader(hotkey="competitor2", leader_since=datetime.now() - timedelta(days=30 + 6 * 7)),
        "competition3": CompetitionLeader(hotkey="competitor3", leader_since=datetime.now() - timedelta(days=30)),
        "competition4": CompetitionLeader(hotkey="competitor4", leader_since=datetime.now() - timedelta(days=30)),
    }

    scores = {
        "competitor1": Score(score=0.0, reduction=0.0),
        "competitor2": Score(score=0.0, reduction=0.0),
        "competitor3": Score(score=0.0, reduction=0.0),
        "competitor4": Score(score=0.0, reduction=0.0),
    }

    # Set up the configuration with multiple competitions and multiple competitors
    rewarder_config = RewarderConfig(
        competitionID_to_leader_hotkey_map=competition_leaders,
        hotkey_to_score_map=scores
    )

    rewarder = Rewarder(rewarder_config)
    rewarder.update_scores()

    # Check the updated scores and reductions for the multiple competitors
    updated_scores = {hotkey: score.score for hotkey, score in rewarder.scores.items()}
    updated_reductions = {hotkey: score.reduction for hotkey, score in rewarder.scores.items()}

    # With multiple competitors and some reduced shares, they should receive different scores and reductions
    expected_reductions = {
        "competitor1": 1/4 * 0.3,
        "competitor2": 1/4 * 0.6,
        "competitor3": 0.0,
        "competitor4": 0.0,
    }

    expected_reductions_sum = sum(expected_reductions.values())
    expected_scores = {
        "competitor1": 1/4 - expected_reductions["competitor1"],
        "competitor2": 1/4 - expected_reductions["competitor2"],
        "competitor3": 1/4 + expected_reductions_sum/2,
        "competitor4": 1/4 + expected_reductions_sum/2,
    }

    for hotkey, score in updated_scores.items():
        assert score == pytest.approx(expected_scores[hotkey], rel=1e-9), f"Expected score: {expected_scores[hotkey]}, got: {score}"

    for hotkey, reduction in updated_reductions.items():
        assert reduction == pytest.approx(expected_reductions[hotkey], rel=1e-9), f"Expected reduction: {expected_reductions[hotkey]}, got: {reduction}"

def test_update_scores_all_competitors_with_reduced_shares():
    # Set up initial data for multiple competitors
    competition_leaders = {
        "competition1": CompetitionLeader(hotkey="competitor1", leader_since=datetime.now() - timedelta(days=30 + 3 * 7)),
        "competition2": CompetitionLeader(hotkey="competitor2", leader_since=datetime.now() - timedelta(days=30 + 6 * 7)),
        "competition3": CompetitionLeader(hotkey="competitor3", leader_since=datetime.now() - timedelta(days=30 + 9 * 7))
    }

    scores = {
        "competitor1": Score(score=0.0, reduction=0.0),
        "competitor2": Score(score=0.0, reduction=0.0),
        "competitor3": Score(score=0.0, reduction=0.0)
    }

    # Set up the configuration with multiple competitions and multiple competitors
    rewarder_config = RewarderConfig(
        competitionID_to_leader_hotkey_map=competition_leaders,
        hotkey_to_score_map=scores
    )

    rewarder = Rewarder(rewarder_config)
    rewarder.update_scores()

    # Check the updated scores and reductions for the multiple competitors
    updated_scores = {hotkey: score.score for hotkey, score in rewarder.scores.items()}
    updated_reductions = {hotkey: score.reduction for hotkey, score in rewarder.scores.items()}

    # With multiple competitors and reduced shares, they should receive different scores and reductions
    expected_reductions = {
        "competitor1": 0.1,
        "competitor2": 0.2,
        "competitor3": 0.3
    }

    expected_reductions_sum = sum(expected_reductions.values())
    expected_scores = {
        "competitor1": 1/3 - expected_reductions["competitor1"] + expected_reductions_sum/3,
        "competitor2": 1/3 - expected_reductions["competitor2"] + expected_reductions_sum/3,
        "competitor3": 1/3 - expected_reductions["competitor3"] + expected_reductions_sum/3,
    }

    for hotkey, score in updated_scores.items():
        assert score == expected_scores[hotkey], f"Expected score: {expected_scores[hotkey]}, got: {score}"

    for hotkey, reduction in updated_reductions.items():
        assert reduction == expected_reductions[hotkey], f"Expected reduction: {expected_reductions[hotkey]}, got: {reduction}"

def test_update_scores_more_competitions_then_competitors():
    # Set up initial data for multiple competitors
    competition_leaders = {
        "competition1": CompetitionLeader(hotkey="competitor1", leader_since=datetime.now() - timedelta(days=30 + 3 * 7)),
        "competition2": CompetitionLeader(hotkey="competitor2", leader_since=datetime.now() - timedelta(days=30)),
        "competition3": CompetitionLeader(hotkey="competitor1", leader_since=datetime.now() - timedelta(days=30)),
        "competition4": CompetitionLeader(hotkey="competitor3", leader_since=datetime.now() - timedelta(days=30)),
    }

    scores = {
        "competitor1": Score(score=0.0, reduction=0.0),
        "competitor2": Score(score=0.0, reduction=0.0),
        "competitor3": Score(score=0.0, reduction=0.0),
    }

    # Set up the configuration with multiple competitions and multiple competitors
    rewarder_config = RewarderConfig(
        competitionID_to_leader_hotkey_map=competition_leaders,
        hotkey_to_score_map=scores
    )

    rewarder = Rewarder(rewarder_config)
    rewarder.update_scores()

    # Check the updated scores and reductions for the multiple competitors
    updated_scores = {hotkey: score.score for hotkey, score in rewarder.scores.items()}
    updated_reductions = {hotkey: score.reduction for hotkey, score in rewarder.scores.items()}

    # With multiple competitors and some reduced shares, they should receive different scores and reductions
    expected_reductions = {
        "competitor1": 1/4 * 0.3,
        "competitor2": 0.0,
        "competitor3": 0.0,
    }

    expected_reductions_sum = sum(expected_reductions.values())
    expected_scores = {
        "competitor1": 2/4 - expected_reductions["competitor1"] + expected_reductions_sum/3,
        "competitor2": 1/4 + expected_reductions_sum/3,
        "competitor3": 1/4 + expected_reductions_sum/3,
    }

    for hotkey, score in updated_scores.items():
        assert score == pytest.approx(expected_scores[hotkey], rel=1e-9), f"Expected score: {expected_scores[hotkey]}, got: {score} for {hotkey}"

    for hotkey, reduction in updated_reductions.items():
        assert reduction == pytest.approx(expected_reductions[hotkey], rel=1e-9), f"Expected reduction: {expected_reductions[hotkey]}, got: {reduction} for {hotkey}"

def test_update_scores_6_competitions_3_competitors():
    # Set up initial data for multiple competitors
    competition_leaders = {
        "competition1": CompetitionLeader(hotkey="competitor1", leader_since=datetime.now() - timedelta(days=30 + 3 * 7)),
        "competition2": CompetitionLeader(hotkey="competitor2", leader_since=datetime.now() - timedelta(days=30 + 6 * 7)),
        "competition3": CompetitionLeader(hotkey="competitor3", leader_since=datetime.now() - timedelta(days=30 + 9 * 7)),
        "competition4": CompetitionLeader(hotkey="competitor4", leader_since=datetime.now() - timedelta(days=30)),
        "competition5": CompetitionLeader(hotkey="competitor1", leader_since=datetime.now() - timedelta(days=30)),
        "competition6": CompetitionLeader(hotkey="competitor2", leader_since=datetime.now() - timedelta(days=30 + 3 * 7)),
    }

    scores = {
        "competitor1": Score(score=0.0, reduction=0.0),
        "competitor2": Score(score=0.0, reduction=0.0),
        "competitor3": Score(score=0.0, reduction=0.0),
        "competitor4": Score(score=0.0, reduction=0.0),
    }

    # Set up the configuration with multiple competitions and multiple competitors
    rewarder_config = RewarderConfig(
        competitionID_to_leader_hotkey_map=competition_leaders,
        hotkey_to_score_map=scores
    )

    rewarder = Rewarder(rewarder_config)
    rewarder.update_scores()

    # Check the updated scores and reductions for the multiple competitors
    updated_scores = {hotkey: score.score for hotkey, score in rewarder.scores.items()}
    updated_reductions = {hotkey: score.reduction for hotkey, score in rewarder.scores.items()}

    # With multiple competitors and some reduced shares, they should receive different scores and reductions
    expected_reductions = {
        "competitor1": 1/6 * 0.3,
        "competitor2": (1/6 * 0.6) + (1/6 * 0.3),
        "competitor3": 1/6 * 0.9,
        "competitor4": 0.0,
    }

    expected_reductions_sum = sum(expected_reductions.values())
    expected_scores = {
        "competitor1": (2/6 - expected_reductions["competitor1"]) + expected_reductions_sum/2,
        "competitor2": (2/6 - expected_reductions["competitor2"]),
        "competitor3": 1/6 - expected_reductions["competitor3"],
        "competitor4": 1/6 + expected_reductions_sum/2,
    }

    for hotkey, score in updated_scores.items():
        assert score == pytest.approx(expected_scores[hotkey], rel=1e-9), f"Expected score: {expected_scores[hotkey]}, got: {score} for {hotkey}"

    for hotkey, reduction in updated_reductions.items():
        assert reduction == pytest.approx(expected_reductions[hotkey], rel=1e-9), f"Expected reduction: {expected_reductions[hotkey]}, got: {reduction} for {hotkey}"

if __name__ == "__main__":
    pytest.main()
