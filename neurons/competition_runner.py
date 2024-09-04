from cancer_ai.validator.competition_manager import CompetitionManager
from datetime import datetime, time, timedelta
from pydantic import BaseModel
import asyncio
import json
from datetime import datetime, timezone, timedelta
import bittensor as bt
from typing import List, Tuple, Dict
from cancer_ai.validator.rewarder import Rewarder, WinnersMapping, CompetitionLeader

# from cancer_ai.utils.config import config

# TODO MOVE SOMEWHERE
main_competitions_cfg = json.load(open("neurons/competition_config.json", "r"))

MINUTES_BACK = 15


class CompetitionRun(BaseModel):
    competition_id: str
    start_time: datetime
    end_time: datetime | None = None


class CompetitionRunLog(BaseModel):
    runs: list[CompetitionRun]

    def add_run(self, new_run: CompetitionRun):
        """Add a new run and rotate the list if it exceeds 20 entries."""
        self.runs.append(new_run)
        if len(self.runs) > 20:
            self.runs = self.runs[-20:]

    def finish_run(self, competition_id: str):
        """Finish the run with the given competition_id"""
        for run in self.runs:
            if run.competition_id == competition_id:
                run.end_time = datetime.now(timezone.utc)

    def was_competition_already_executed(
        self, competition_id: str, last_minutes: int = 15
    ):
        """Check if competition was executed in last minutes"""
        now_time = datetime.now(timezone.utc)
        for run in self.runs:
            if competition_id and run.competition_id != competition_id:
                continue
            if run.end_time and (now_time - run.end_time).seconds < last_minutes * 60:
                return True
        return False


class CompetitionSchedulerConfig(BaseModel):
    config: dict[datetime.time, CompetitionManager]

    class Config:
        arbitrary_types_allowed = True


def config_for_scheduler(
    bt_config, hotkeys: List[str], test_mode: bool = False
) -> CompetitionSchedulerConfig:
    """Returns CompetitionManager instances arranged by competition time"""
    scheduler_config = {}
    for competition_cfg in main_competitions_cfg:
        for competition_time in competition_cfg["evaluation_times"]:
            parsed_time = datetime.strptime(competition_time, "%H:%M").time()
            scheduler_config[parsed_time] = CompetitionManager(
                bt_config,
                hotkeys,
                competition_cfg["competition_id"],
                competition_cfg["category"],
                competition_cfg["dataset_hf_repo"],
                competition_cfg["dataset_hf_filename"],
                competition_cfg["dataset_hf_repo_type"],
                test_mode=test_mode,
            )

    return scheduler_config


async def run_competitions_tick(
    competition_times: CompetitionSchedulerConfig,
    run_log: CompetitionRunLog,
) -> Tuple[str, str] | None:
    """Checks if time is right and launches competition, returns winning hotkey and Competition ID. Should be run each minute."""

    # getting current time
    now = datetime.now(timezone.utc)
    now_time = time(now.hour, now.minute)
    bt.logging.info(f"Checking competitions at {now_time}")

    for i in range(0, MINUTES_BACK):
        # getting current time minus X minutes
        check_time = (
            datetime.combine(datetime.today(), now_time) - timedelta(minutes=i)
        ).time()

        # bt.logging.debug(f"Checking competitions at {check_time}")
        if competition_manager := competition_times.get(check_time):
            bt.logging.debug(
                f"Found competition {competition_manager.competition_id} at {check_time}"
            )
        else:
            continue

        if run_log.was_competition_already_executed(
            competition_id=competition_manager.competition_id, last_minutes=MINUTES_BACK
        ):
            bt.logging.info(
                f"Competition {competition_manager.competition_id} already executed, skipping"
            )
            continue

        bt.logging.info(f"Running {competition_manager.competition_id} at {now_time}")
        run_log.add_run(
            CompetitionRun(
                competition_id=competition_manager.competition_id,
                start_time=datetime.now(timezone.utc),
            )
        )
        winning_evaluation_hotkey = await competition_manager.evaluate()
        run_log.finish_run(competition_manager.competition_id)
        # TODO log last run to WANDB
        return (
            winning_evaluation_hotkey,
            competition_manager.competition_id,
        )

    bt.logging.debug(
        f"Did not find any competitions to run for past {MINUTES_BACK} minutes"
    )
    asyncio.sleep(60)


async def competition_loop_not_used(
    scheduler_config: CompetitionSchedulerConfig, rewarder_config: WinnersMapping
):
    """Example of scheduling coroutine"""
    while True:
        competition_result = await run_competitions_tick(scheduler_config)
        bt.logging.debug(f"Competition result: {competition_result}")
        if competition_result:
            winning_evaluation_hotkey, competition_id = competition_result
            rewarder = Rewarder(rewarder_config)
            updated_rewarder_config = await rewarder.update_scores(
                winning_evaluation_hotkey, competition_id
            )
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
    rewarder_config = WinnersMapping(competition_leader_map={}, hotkey_score_map={})
    asyncio.run(competition_loop_not_used(scheduler_config, rewarder_config))
