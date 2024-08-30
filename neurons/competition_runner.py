from cancer_ai.validator.competition_manager import CompetitionManager
from datetime import time, datetime

import asyncio
import json
import timeit
from types import SimpleNamespace
from datetime import datetime, timezone, timedelta
import bittensor as bt
from typing import List, Tuple, Dict

# from cancer_ai.utils.config import config


def config_for_scheduler(
    bt_config, hotkeys: List[str]
) -> Dict[str, CompetitionManager]:
    """Returns CompetitionManager instances arranged by competition time"""
    time_arranged_competitions = {}
    for competition_cfg in main_competitions_cfg:
        for competition_time in competition_cfg["evaluation_time"]:
            time_arranged_competitions[competition_time] = CompetitionManager(
                bt_config,
                hotkeys,
                competition_cfg["competition_id"],
                competition_cfg["category"],
                competition_cfg["dataset_hf_repo"],
                competition_cfg["dataset_hf_filename"],
                competition_cfg["dataset_hf_repo_type"],
            )
    return time_arranged_competitions


async def run_competitions_tick(
    competition_times: Dict[str, CompetitionManager],
) -> Tuple[str, str] | None:
    """Checks if time is right and launches competition, returns winning hotkey and Competition ID. Should be run each minute."""
    now_time = datetime.now()
    now_time = f"{now_time.hour}:{now_time.minute}"
    bt.logging.debug(now_time)
    if now_time not in competition_times:
        return None
    for time_competition in competition_times:
        if now_time == time_competition:
            bt.logging.info(
                f"Running {competition_times[time_competition].competition_id} at {now_time}"
            )
            winning_evaluation_hotkey = await competition_times[
                time_competition
            ].evaluate()
            return (
                winning_evaluation_hotkey,
                competition_times[time_competition].competition_id,
            )


async def competition_loop(scheduler_config: Dict[str, CompetitionManager]):
    """Example of scheduling coroutine"""
    while True:
        competition_result = await run_competitions_tick(scheduler_config)
        bt.logging.debug(f"Competition result: {competition_result}")
        await asyncio.sleep(60)


if __name__ == "__main__":
    # fetch from config
    competition_config_path = "neurons/competition_config.json"
    main_competitions_cfg = json.load(
        open(competition_config_path, "r")
    )  # TODO fetch from config
    hotkeys = []
    bt_config = {}  # get from bt config
    scheduler_config = config_for_scheduler(bt_config, hotkeys)
    asyncio.run(competition_loop(scheduler_config))
