import pytest
from datetime import datetime, timedelta, timezone
from .rewarder import CompetitionLeader, Score, CompetitionWinnersStore, Rewarder
from cancer_ai.validator.competition_handlers.base_handler import ModelEvaluationResult
import numpy as np


@pytest.mark.asyncio
async def test_winner_results_model_improved():
    """
    Set new leader if winner's model has better scores
    """
    current_model_results = ModelEvaluationResult(
        score=0.90,
    )

    new_model_results = ModelEvaluationResult(
        score=0.99,
    )

    competition_leaders = {
        "competition1": CompetitionLeader(
            hotkey="player_1",
            leader_since=datetime.now() - timedelta(days=30 + 3 * 7),
            model_result=current_model_results,
        ),
    }

    scores = {
        "player_1": Score(score=1.0, reduction=0.0),
    }

    winners_store = CompetitionWinnersStore(
        competition_leader_map=competition_leaders, hotkey_score_map=scores
    )

    rewarder = Rewarder(winners_store)
    await rewarder.update_scores(
        winner_hotkey="player_2",
        competition_id="competition1",
        winner_model_result=new_model_results,
    )
    assert (
        winners_store.competition_leader_map["competition1"].model_result
        == new_model_results
    )
    assert winners_store.competition_leader_map["competition1"].hotkey == "player_2"


@pytest.mark.asyncio
async def test_winner_empty_store():
    """
    Test rewards if store is empty
    """
    model_results = ModelEvaluationResult(
        score=0.9,
    )
    competition_leaders = {}
    scores = {}

    winners_store = CompetitionWinnersStore(
        competition_leader_map=competition_leaders, hotkey_score_map=scores
    )
    rewarder = Rewarder(winners_store)
    await rewarder.update_scores(
        winner_hotkey="player_1",
        competition_id="competition1",
        winner_model_result=model_results,
    )
    assert (
        winners_store.competition_leader_map["competition1"].model_result
        == model_results
    )


@pytest.mark.asyncio
async def test_winner_results_model_copying():
    """
    Set new leader if winner's model has better scores
    """
    current_model_results = ModelEvaluationResult(
        score=0.9,
    )

    new_model_results = ModelEvaluationResult(
        score=0.9002,
    )

    competition_leaders = {
        "competition1": CompetitionLeader(
            hotkey="player_1",
            leader_since=datetime.now(timezone.utc) - timedelta(days=30 + 3 * 7),
            model_result=current_model_results,
        ),
    }

    scores = {
        "player_1": Score(score=1.0, reduction=0.0),
    }

    winners_store = CompetitionWinnersStore(
        competition_leader_map=competition_leaders, hotkey_score_map=scores
    )

    rewarder = Rewarder(winners_store)
    await rewarder.update_scores(
        winner_hotkey="player_2",
        competition_id="competition1",
        winner_model_result=new_model_results,
    )
    assert (
        winners_store.competition_leader_map["competition1"].model_result.score
        == current_model_results.score
    )
    assert winners_store.competition_leader_map["competition1"].hotkey == "player_1"

@pytest.mark.asyncio
async def test_update_scores_single_competitor():
    # Set up initial data for a single competitor
    competition_leaders = {
        "competition_1": CompetitionLeader(
            hotkey="competitor_1",
            leader_since=datetime.now(timezone.utc) - timedelta(days=10),
            model_result=ModelEvaluationResult(score=0.9),
        )
    }

    scores = {
        "competitor_1": Score(score=1.0, reduction=0.0),
    }

    # Set up the configuration with a single competition and a single competitor
    winners_store = CompetitionWinnersStore(
        competition_leader_map=competition_leaders, hotkey_score_map=scores)

    rewarder = Rewarder(winners_store)
    expected_winner_model_score = 0.95
    await rewarder.update_scores(winner_hotkey="competitor_1", competition_id="competition_1",
                            winner_model_result=ModelEvaluationResult(score=expected_winner_model_score))


    # Check the updated scores and reductions for the single competitor
    updated_score = rewarder.scores["competitor_1"].score
    updated_reduction = rewarder.scores["competitor_1"].reduction

    # # With only one competitor, they should receive the full score of 1.0
    expected_score = 1.0
    expected_reduction = 0.0

    assert (
        winners_store.competition_leader_map["competition_1"].model_result.score
        == expected_winner_model_score
    )
    assert winners_store.competition_leader_map["competition_1"].hotkey == "competitor_1"
    assert (
        updated_score == expected_score
    ), f"Expected score: {expected_score}, got: {updated_score}"
    assert (
        updated_reduction == expected_reduction
    ), f"Expected reduction: {expected_reduction}, got: {updated_reduction}"

@pytest.mark.asyncio
async def test_update_scores_multiple_competitors_no_reduction():
    # Set up initial data for a multiple competitors
    competition_leaders = {
        "competition_1": CompetitionLeader(
            hotkey="competitor_1",
            leader_since=datetime.now(timezone.utc) - timedelta(days=10),
            model_result=ModelEvaluationResult(score=0.9),
        ),
        "competition_2": CompetitionLeader(
            hotkey="competitor_2",
            leader_since=datetime.now(timezone.utc) - timedelta(days=10),
            model_result=ModelEvaluationResult(score=0.9),
        ),
        "competition_3": CompetitionLeader(
            hotkey="competitor_3",
            leader_since=datetime.now(timezone.utc) - timedelta(days=10),
            model_result=ModelEvaluationResult(score=0.9),
        ),
    }

    scores = {
        "competitor_1": Score(score=0.0, reduction=0.0),
        "competitor_2": Score(score=0.0, reduction=0.0),
        "competitor_3": Score(score=0.0, reduction=0.0),
    }

    # Set up the configuration with multiple competitions and multiple competitors
    winners_store = CompetitionWinnersStore(
        competition_leader_map=competition_leaders, hotkey_score_map=scores)

    rewarder = Rewarder(winners_store)
    await rewarder.update_scores(winner_hotkey="competitor_1", competition_id="competition_1",
                            winner_model_result=ModelEvaluationResult(score=0.9))


    # Check the updated scores and reductions for the multiple competitors
    updated_scores = {hotkey: score.score for hotkey, score in rewarder.scores.items()}
    updated_reductions = {
        hotkey: score.reduction for hotkey, score in rewarder.scores.items()
    }
    updated_model_scores = {competition_id: leader.model_result.score for competition_id, leader in winners_store.competition_leader_map.items()}

    # With multiple competitors and no reductions, they should all receive the same score of 1/3
    expected_score = 1 / 3
    expected_reduction = 0.0
    expected_model_score = 0.9


    for _, score in updated_model_scores.items():
        assert (
            score == expected_model_score
        ), f"Expected score: {expected_model_score}, got: {score}"

    for _, score in updated_scores.items():
        assert (
            score == expected_score
        ), f"Expected score: {expected_score}, got: {score}"

    for _, reduction in updated_reductions.items():
        assert (
            reduction == expected_reduction
        ), f"Expected reduction: {expected_reduction}, got: {reduction}"

@pytest.mark.asyncio
async def test_update_scores_multiple_competitors_with_some_reduced_shares():
    # Set up initial data for a multiple competitors
    competition_leaders = {
        "competition_1": CompetitionLeader(
            hotkey="competitor_1",
            leader_since=datetime.now(timezone.utc) - timedelta(days=30 + 3 * 7),
            model_result=ModelEvaluationResult(score=0.9),
        ),
        "competition_2": CompetitionLeader(
            hotkey="competitor_2",
            leader_since=datetime.now(timezone.utc) - timedelta(days=30 + 6 * 7),
            model_result=ModelEvaluationResult(score=0.9),
        ),
        "competition_3": CompetitionLeader(
            hotkey="competitor_3",
            leader_since=datetime.now(timezone.utc) - timedelta(days=30),
            model_result=ModelEvaluationResult(score=0.9),
        ),
        "competition_4": CompetitionLeader(
            hotkey="competitor_4",
            leader_since=datetime.now(timezone.utc) - timedelta(days=30),
            model_result=ModelEvaluationResult(score=0.9),
        ),
    }

    scores = {
        "competitor_1": Score(score=0.0, reduction=0.0),
        "competitor_2": Score(score=0.0, reduction=0.0),
        "competitor_3": Score(score=0.0, reduction=0.0),
        "competitor_4": Score(score=0.0, reduction=0.0),
    }

    # Set up the configuration with multiple competitions and multiple competitors
    winners_store = CompetitionWinnersStore(
        competition_leader_map=competition_leaders, hotkey_score_map=scores)

    rewarder = Rewarder(winners_store)
    await rewarder.update_scores(winner_hotkey="competitor_1", competition_id="competition_1",
                            winner_model_result=ModelEvaluationResult(score=0.9))


    # Check the updated scores and reductions for the multiple competitors
    updated_scores = {hotkey: score.score for hotkey, score in rewarder.scores.items()}
    updated_reductions = {
        hotkey: score.reduction for hotkey, score in rewarder.scores.items()
    }
    updated_model_scores = {competition_id: leader.model_result.score for competition_id, leader in winners_store.competition_leader_map.items()}

    # With multiple competitors and some reduced shares, they should receive different scores and reductions
    expected_reductions = {
        "competitor_1": 1 / 4 * 0.3,
        "competitor_2": 1 / 4 * 0.6,
        "competitor_3": 0.0,
        "competitor_4": 0.0,
    }

    expected_reductions_sum = sum(expected_reductions.values())
    expected_scores = {
        "competitor_1": 1 / 4 - expected_reductions["competitor_1"],
        "competitor_2": 1 / 4 - expected_reductions["competitor_2"],
        "competitor_3": 1 / 4 + expected_reductions_sum / 2,
        "competitor_4": 1 / 4 + expected_reductions_sum / 2,
    }
    expected_model_score = 0.9


    for _, score in updated_model_scores.items():
        assert (
            score == expected_model_score
        ), f"Expected score: {expected_model_score}, got: {score}"

    for hotkey, score in updated_scores.items():
        assert score == pytest.approx(
            expected_scores[hotkey], rel=1e-9
        ), f"Expected score: {expected_scores[hotkey]}, got: {score}"

    for hotkey, reduction in updated_reductions.items():
        assert reduction == pytest.approx(
            expected_reductions[hotkey], rel=1e-9
        ), f"Expected reduction: {expected_reductions[hotkey]}, got: {reduction}"

@pytest.mark.asyncio
async def test_update_scores_all_competitors_with_reduced_shares():
    # Set up initial data for a multiple competitors
    competition_leaders = {
        "competition_1": CompetitionLeader(
            hotkey="competitor_1",
            leader_since=datetime.now(timezone.utc) - timedelta(days=30 + 3 * 7),
            model_result=ModelEvaluationResult(score=0.9),
        ),
        "competition_2": CompetitionLeader(
            hotkey="competitor_2",
            leader_since=datetime.now(timezone.utc) - timedelta(days=30 + 6 * 7),
            model_result=ModelEvaluationResult(score=0.9),
        ),
        "competition_3": CompetitionLeader(
            hotkey="competitor_3",
            leader_since=datetime.now(timezone.utc) - timedelta(days=30 + 9 * 7),
            model_result=ModelEvaluationResult(score=0.9),
        ),
    }

    scores = {
        "competitor_1": Score(score=0.0, reduction=0.0),
        "competitor_2": Score(score=0.0, reduction=0.0),
        "competitor_3": Score(score=0.0, reduction=0.0),
    }

    # Set up the configuration with multiple competitions and multiple competitors
    winners_store = CompetitionWinnersStore(
        competition_leader_map=competition_leaders, hotkey_score_map=scores)

    rewarder = Rewarder(winners_store)
    await rewarder.update_scores(winner_hotkey="competitor_1", competition_id="competition_1",
                            winner_model_result=ModelEvaluationResult(score=0.9))


    # Check the updated scores and reductions for the multiple competitors
    updated_scores = {hotkey: score.score for hotkey, score in rewarder.scores.items()}
    updated_reductions = {
        hotkey: score.reduction for hotkey, score in rewarder.scores.items()
    }
    updated_model_scores = {competition_id: leader.model_result.score for competition_id, leader in winners_store.competition_leader_map.items()}

    # With multiple competitors and some reduced shares, they should receive different scores and reductions
    expected_reductions = {"competitor_1": 0.1, "competitor_2": 0.2, "competitor_3": 0.3}

    expected_reductions_sum = sum(expected_reductions.values())
    expected_scores = {
        "competitor_1": 1 / 3
        - expected_reductions["competitor_1"]
        + expected_reductions_sum / 3,
        "competitor_2": 1 / 3
        - expected_reductions["competitor_2"]
        + expected_reductions_sum / 3,
        "competitor_3": 1 / 3
        - expected_reductions["competitor_3"]
        + expected_reductions_sum / 3,
    }
    expected_model_score = 0.9


    for _, score in updated_model_scores.items():
        assert (
            score == expected_model_score
        ), f"Expected score: {expected_model_score}, got: {score}"

    for hotkey, score in updated_scores.items():
        assert score == pytest.approx(
            expected_scores[hotkey], rel=1e-9
        ), f"Expected score: {expected_scores[hotkey]}, got: {score}"

    for hotkey, reduction in updated_reductions.items():
        assert reduction == pytest.approx(
            expected_reductions[hotkey], rel=1e-9
        ), f"Expected reduction: {expected_reductions[hotkey]}, got: {reduction}"

@pytest.mark.asyncio
async def test_update_scores_more_competitions_then_competitors():
    # Set up initial data for a multiple competitors
    competition_leaders = {
        "competition_1": CompetitionLeader(
            hotkey="competitor_1",
            leader_since=datetime.now(timezone.utc) - timedelta(days=30 + 3 * 7),
            model_result=ModelEvaluationResult(score=0.9),
        ),
        "competition_2": CompetitionLeader(
            hotkey="competitor_2",
            leader_since=datetime.now(timezone.utc) - timedelta(days=30),
            model_result=ModelEvaluationResult(score=0.9),
        ),
        "competition_3": CompetitionLeader(
            hotkey="competitor_1",
            leader_since=datetime.now(timezone.utc) - timedelta(days=30),
            model_result=ModelEvaluationResult(score=0.9),
        ),
        "competition_4": CompetitionLeader(
            hotkey="competitor_3",
            leader_since=datetime.now(timezone.utc) - timedelta(days=30),
            model_result=ModelEvaluationResult(score=0.9),
        ),
    }

    scores = {
        "competitor_1": Score(score=0.0, reduction=0.0),
        "competitor_2": Score(score=0.0, reduction=0.0),
        "competitor_3": Score(score=0.0, reduction=0.0),
    }

    # Set up the configuration with multiple competitions and multiple competitors
    winners_store = CompetitionWinnersStore(
        competition_leader_map=competition_leaders, hotkey_score_map=scores)

    rewarder = Rewarder(winners_store)
    await rewarder.update_scores(winner_hotkey="competitor_1", competition_id="competition_1",
                            winner_model_result=ModelEvaluationResult(score=0.9))


    # Check the updated scores and reductions for the multiple competitors
    updated_scores = {hotkey: score.score for hotkey, score in rewarder.scores.items()}
    updated_reductions = {
        hotkey: score.reduction for hotkey, score in rewarder.scores.items()
    }
    updated_model_scores = {competition_id: leader.model_result.score for competition_id, leader in winners_store.competition_leader_map.items()}

    # With multiple competitors and some reduced shares, they should receive different scores and reductions
    expected_reductions = {
        "competitor_1": 1 / 4 * 0.3,
        "competitor_2": 0.0,
        "competitor_3": 0.0,
    }

    expected_reductions_sum = sum(expected_reductions.values())
    expected_scores = {
        "competitor_1": 2 / 4
        - expected_reductions["competitor_1"]
        + expected_reductions_sum / 3,
        "competitor_2": 1 / 4 + expected_reductions_sum / 3,
        "competitor_3": 1 / 4 + expected_reductions_sum / 3,
    }
    expected_model_score = 0.9


    for _, score in updated_model_scores.items():
        assert (
            score == expected_model_score
        ), f"Expected score: {expected_model_score}, got: {score}"

    for hotkey, score in updated_scores.items():
        assert score == pytest.approx(
            expected_scores[hotkey], rel=1e-9
        ), f"Expected score: {expected_scores[hotkey]}, got: {score}"

    for hotkey, reduction in updated_reductions.items():
        assert reduction == pytest.approx(
            expected_reductions[hotkey], rel=1e-9
        ), f"Expected reduction: {expected_reductions[hotkey]}, got: {reduction}"

@pytest.mark.asyncio
async def test_update_scores_6_competitions_4_competitors():
    # Set up initial data for a multiple competitors
    competition_leaders = {
        "competition_1": CompetitionLeader(
            hotkey="competitor_1",
            leader_since=datetime.now(timezone.utc) - timedelta(days=30 + 3 * 7),
            model_result=ModelEvaluationResult(score=0.9),
        ),
        "competition_2": CompetitionLeader(
            hotkey="competitor_2",
            leader_since=datetime.now(timezone.utc) - timedelta(days=30 + 6 * 7),
            model_result=ModelEvaluationResult(score=0.9),
        ),
        "competition_3": CompetitionLeader(
            hotkey="competitor_3",
            leader_since=datetime.now(timezone.utc) - timedelta(days=30 + 9 * 7),
            model_result=ModelEvaluationResult(score=0.9),
        ),
        "competition_4": CompetitionLeader(
            hotkey="competitor_4",
            leader_since=datetime.now(timezone.utc) - timedelta(days=30),
            model_result=ModelEvaluationResult(score=0.9),
        ),
        "competition_5": CompetitionLeader(
            hotkey="competitor_1",
            leader_since=datetime.now(timezone.utc) - timedelta(days=30),
            model_result=ModelEvaluationResult(score=0.9),
        ),
        "competition_6": CompetitionLeader(
            hotkey="competitor_2",
            leader_since=datetime.now(timezone.utc) - timedelta(days=30 + 3 * 7),
            model_result=ModelEvaluationResult(score=0.9),
        ),
    }

    scores = {
        "competitor_1": Score(score=0.0, reduction=0.0),
        "competitor_2": Score(score=0.0, reduction=0.0),
        "competitor_3": Score(score=0.0, reduction=0.0),
        "competitor_4": Score(score=0.0, reduction=0.0),
    }

    # Set up the configuration with multiple competitions and multiple competitors
    winners_store = CompetitionWinnersStore(
        competition_leader_map=competition_leaders, hotkey_score_map=scores)

    rewarder = Rewarder(winners_store)
    await rewarder.update_scores(winner_hotkey="competitor_1", competition_id="competition_1",
                            winner_model_result=ModelEvaluationResult(score=0.9))


    # Check the updated scores and reductions for the multiple competitors
    updated_scores = {hotkey: score.score for hotkey, score in rewarder.scores.items()}
    updated_reductions = {
        hotkey: score.reduction for hotkey, score in rewarder.scores.items()
    }
    updated_model_scores = {competition_id: leader.model_result.score for competition_id, leader in winners_store.competition_leader_map.items()}

    # With multiple competitors and some reduced shares, they should receive different scores and reductions
    expected_reductions = {
        "competitor_1": 1 / 6 * 0.3,
        "competitor_2": (1 / 6 * 0.6) + (1 / 6 * 0.3),
        "competitor_3": 1 / 6 * 0.9,
        "competitor_4": 0.0,
    }

    expected_reductions_sum = sum(expected_reductions.values())
    expected_scores = {
        "competitor_1": (2 / 6 - expected_reductions["competitor_1"])
        + expected_reductions_sum / 2,
        "competitor_2": (2 / 6 - expected_reductions["competitor_2"]),
        "competitor_3": 1 / 6 - expected_reductions["competitor_3"],
        "competitor_4": 1 / 6 + expected_reductions_sum / 2,
    }
    expected_model_score = 0.9


    for _, score in updated_model_scores.items():
        assert (
            score == expected_model_score
        ), f"Expected score: {expected_model_score}, got: {score}"

    for hotkey, score in updated_scores.items():
        assert score == pytest.approx(
            expected_scores[hotkey], rel=1e-9
        ), f"Expected score: {expected_scores[hotkey]}, got: {score}"

    for hotkey, reduction in updated_reductions.items():
        assert reduction == pytest.approx(
            expected_reductions[hotkey], rel=1e-9
        ), f"Expected reduction: {expected_reductions[hotkey]}, got: {reduction}"


if __name__ == "__main__":
    pytest.main()
