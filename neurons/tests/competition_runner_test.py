import asyncio
import json
from types import SimpleNamespace
from typing import List, Dict
import pytest

import bittensor as bt


from cancer_ai.validator.competition_manager import CompetitionManager
from cancer_ai.validator.rewarder import CompetitionWinnersStore, Rewarder
from cancer_ai.base.base_miner import BaseNeuron
from cancer_ai.utils.config import path_config
from cancer_ai.mock import MockSubtensor


COMPETITION_FILEPATH = "config/competition_config_testnet.json"

# TODO integrate with bt config
test_config = SimpleNamespace(
    **{
        "wandb_entity": "testnet",
        "wandb_project_name": "melanoma-1",
        "competition_id": "melaonoma-1",
        "hotkeys": [],
        "subtensor": SimpleNamespace(**{"network": "test"}),
        "netuid": 163,
        "models": SimpleNamespace(
            **{
                "model_dir": "/tmp/models",
                "dataset_dir": "/tmp/datasets",
            }
        ),
        "hf_token": "HF_TOKEN",
    }
)

main_competitions_cfg = json.load(open(COMPETITION_FILEPATH, "r"))


async def run_competitions(
    config: str,
    subtensor: bt.subtensor,
    hotkeys: List[str],
    competitions_cfg: List[dict],
) -> Dict[str, str]:
    """Run all competitions, return the winning hotkey for each competition"""
    results = {}
    for competition_cfg in competitions_cfg:
        bt.logging.info("Starting competition: ", competition_cfg)

        competition_manager = CompetitionManager(
            config,
            subtensor,
            hotkeys,
            {},
            competition_cfg["competition_id"],
            competition_cfg["category"],
            competition_cfg["dataset_hf_repo"],
            competition_cfg["dataset_hf_filename"],
            competition_cfg["dataset_hf_repo_type"],
            test_mode=True,
        )
        results[competition_cfg["competition_id"]] = (
            await competition_manager.evaluate()
        )

        bt.logging.info(await competition_manager.evaluate())

    return results


def config_for_scheduler(subtensor: bt.subtensor) -> Dict[str, CompetitionManager]:
    """Returns CompetitionManager instances arranged by competition time"""
    time_arranged_competitions = {}
    for competition_cfg in main_competitions_cfg:
        for competition_time in competition_cfg["evaluation_time"]:
            time_arranged_competitions[competition_time] = CompetitionManager(
                {},
                subtensor,
                [],
                {},
                competition_cfg["competition_id"],
                competition_cfg["category"],
                competition_cfg["dataset_hf_repo"],
                competition_cfg["dataset_hf_filename"],
                competition_cfg["dataset_hf_repo_type"],
                test_mode=True,
            )
    return time_arranged_competitions


async def competition_loop():
    """Example of scheduling coroutine"""
    while True:
        test_cases = [
            ("hotkey1", "melanoma-1"),
            ("hotkey2", "melanoma-1"),
            ("hotkey1", "melanoma-2"),
            ("hotkey1", "melanoma-1"),
            ("hotkey2", "melanoma-3"),
        ]

        rewarder_config = CompetitionWinnersStore(
            competition_leader_map={}, hotkey_score_map={}
        )
        rewarder = Rewarder(rewarder_config)

        for winning_evaluation_hotkey, competition_id in test_cases:
            await rewarder.update_scores(winning_evaluation_hotkey, competition_id)
            print(
                "Updated rewarder competition leader map:",
                rewarder.competition_leader_mapping,
            )
            print("Updated rewarder scores:", rewarder.scores)
        await asyncio.sleep(10)


@pytest.fixture
def competition_config():
    with open(COMPETITION_FILEPATH, "r") as f:
        return json.load(f)


if __name__ == "__main__":
    config = BaseNeuron.config()
    bt.logging.set_config(config=config)
    # if True:  # run them right away
    path_config = path_config(None)
    # config = config.merge(path_config)
    # BaseNeuron.check_config(config)
    bt.logging.set_config(config=config.logging)
    bt.logging.info(config)
    asyncio.run(
        run_competitions(test_config, MockSubtensor("123"), [], main_competitions_cfg)
    )
