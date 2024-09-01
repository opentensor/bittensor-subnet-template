from cancer_ai.validator.competition_manager import CompetitionManager
from datetime import datetime

import asyncio
import json
from datetime import datetime, timezone
import bittensor as bt
from typing import List, Tuple, Dict
from rewarder import Rewarder, RewarderConfig, CompetitionLeader

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
    now_time = datetime.now(timezone.utc)
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


async def competition_loop(scheduler_config: Dict[str, CompetitionManager], rewarder_config: RewarderConfig):
    """Example of scheduling coroutine"""
    while True:
        competition_result = await run_competitions_tick(scheduler_config)
        bt.logging.debug(f"Competition result: {competition_result}")
        if competition_result:
            winning_evaluation_hotkey, competition_id = competition_result
            rewarder = Rewarder(rewarder_config)
            updated_rewarder_config = await rewarder.update_scores(winning_evaluation_hotkey, competition_id)
            # save state of self.rewarder_config
            # save state of self.score (map rewarder config to scores)
            print(".....................Updated rewarder config:")
            print(updated_rewarder_config)
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
    rewarder_config = RewarderConfig({},{})
    asyncio.run(competition_loop(scheduler_config, rewarder_config))
