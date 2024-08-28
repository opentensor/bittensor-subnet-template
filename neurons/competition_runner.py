from cancer_ai.validator.competition_manager import CompetitionManager
from datetime import time, datetime

import asyncio
import json
import timeit
from types import SimpleNamespace
from datetime import datetime, timezone, timedelta
import bittensor as bt
from typing import List, Tuple

# from cancer_ai.utils.config import config

# TODO integrate with bt config
path_config = SimpleNamespace(
    **{
        "model_dir": "/tmp/models",
        "dataset_dir": "/tmp/datasets",
        "wandb_entity": "testnet",
        "wandb_project_name": "melanoma-1",
    }
)

competitions_cfg = json.load(open("neurons/competition_config.json", "r"))


def run_all_competitions(path_config: str, competitions_cfg: List[dict]) -> None:
    for competition_cfg in competitions_cfg:
        print("Starting competition: ", competition_cfg)
        competition_manager = CompetitionManager(
            path_config,
            None,
            7,
            competition_cfg["competition_id"],
            competition_cfg["category"],
            competition_cfg["dataset_hf_repo"],
            competition_cfg["dataset_hf_filename"],
            competition_cfg["dataset_hf_repo_type"],
        )
        print(asyncio.run(competition_manager.evaluate()))


def get_competitions_time_arranged(path_config: str) -> List[CompetitionManager]:
    """Return list of competitions arranged by launching time."""
    competitions_by_launching_time = []

    for competition_config in competitions_cfg:
        competition_manager = CompetitionManager(
            path_config,
            None,
            7,
            competition_config["competition_id"],
            competition_config["category"],
            competition_config["dataset_hf_repo"],
            competition_config["dataset_hf_filename"],
            competition_config["dataset_hf_repo_type"],
        )
        competitions_by_launching_time.append(competition_manager)

    return competitions_by_launching_time


def config_for_scheduler() -> dict:
    scheduler_config = {}
    for competition_cfg in competitions_cfg:
        for competition_time in competition_cfg["evaluation_time"]:
            scheduler_config[competition_time] = CompetitionManager(
                path_config,  # TODO fetch bt config Konrad
                None,
                7,
                competition_cfg["competition_id"],
                competition_cfg["category"],
                competition_cfg["dataset_hf_repo"],
                competition_cfg["dataset_hf_filename"],
                competition_cfg["dataset_hf_repo_type"],
            )
    return scheduler_config


async def run_competitions_if_time_is_right(
    competition_times: List[CompetitionManager],
) -> Tuple[str, str] | None:
    """Checks if time is right and launches competition, returns winning hotkey and Competition ID"""
    now_time = datetime.now()
    now_time = f"{now_time.hour}:{now_time.minute}"
    if now_time not in competition_times:
        return None
    for competition in competition_times:
        if now_time == competition:
            print(f"Running {competition.competition_id} at {now_time}")
            return await (competition.evaluate(), competition.competition_id)


if __name__ == "__main__":
    if True:  # run them right away
        run_all_competitions(path_config, competitions_cfg)

    else:  # Run the scheduling coroutine
        scheduler_config = config_for_scheduler()
        asyncio.run(schedule_competitions(competitions, path_config))
