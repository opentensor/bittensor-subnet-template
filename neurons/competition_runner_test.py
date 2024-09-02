from cancer_ai.validator.competition_manager import CompetitionManager
import asyncio
import json
from types import SimpleNamespace
import bittensor as bt
from typing import List, Dict
from competition_runner import run_competitions_tick, competition_loop
from rewarder import WinnersMapping, Rewarder
import time

# TODO integrate with bt config
test_config = SimpleNamespace(
    **{
        "model_dir": "/tmp/models",
        "dataset_dir": "/tmp/datasets",
        "wandb_entity": "testnet",
        "wandb_project_name": "melanoma-1",
        "competition_id": "melaonoma-1",
        "hotkeys": [],
        "subtensor": SimpleNamespace(**{"network": "test"}),
        "netuid": 163,
    }
)

main_competitions_cfg = json.load(open("neurons/competition_config.json", "r"))


def run_all_competitions(path_config: str, hotkeys: List[str], competitions_cfg: List[dict]) -> None:
    """Run all competitions, for debug purposes"""
    for competition_cfg in competitions_cfg:
        bt.logging.info("Starting competition: ", competition_cfg)
        competition_manager = CompetitionManager(
            path_config,
            hotkeys,
            competition_cfg["competition_id"],
            competition_cfg["category"],
            competition_cfg["dataset_hf_repo"],
            competition_cfg["dataset_hf_filename"],
            competition_cfg["dataset_hf_repo_type"],
            test_mode=True,
        )
        bt.logging.info(asyncio.run(competition_manager.evaluate()))


def config_for_scheduler() -> Dict[str, CompetitionManager]:
    """Returns CompetitionManager instances arranged by competition time"""
    time_arranged_competitions = {}
    for competition_cfg in main_competitions_cfg:
        for competition_time in competition_cfg["evaluation_time"]:
            time_arranged_competitions[competition_time] = CompetitionManager(
                {},  # TODO fetch bt config Konrad
                [],
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

        rewarder_config = WinnersMapping(competition_leader_map={}, hotkey_score_map={})
        rewarder = Rewarder(rewarder_config)

        for winning_evaluation_hotkey, competition_id in test_cases:
            rewarder.update_scores(winning_evaluation_hotkey, competition_id)
            print("Updated rewarder competition leader map:", rewarder.competition_leader_mapping)
            print("Updated rewarder scores:", rewarder.scores)
        await asyncio.sleep(10)

if __name__ == "__main__":
    # if True:  # run them right away
    #     run_all_competitions(test_config, [],main_competitions_cfg)

    # else:  # Run the scheduling coroutine
        # scheduler_config = config_for_scheduler()
    asyncio.run(competition_loop())
