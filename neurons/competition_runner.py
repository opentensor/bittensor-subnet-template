import json
from typing import List, Tuple
from datetime import datetime, timezone, timedelta, time
import asyncio


from pydantic import BaseModel
import bittensor as bt

from cancer_ai.validator.competition_manager import CompetitionManager
from cancer_ai.chain_models_store import ChainMinerModelStore
from cancer_ai.validator.competition_handlers.base_handler import ModelEvaluationResult


MINUTES_BACK = 15


class CompetitionRun(BaseModel):
    competition_id: str
    start_time: datetime
    end_time: datetime | None = None


class CompetitionRunStore(BaseModel):
    """
    The competition run store acts as a cache for competition runs and provides checks for competition execution states.
    """

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
            if run.competition_id != competition_id:
                continue
            if run.end_time and (now_time - run.end_time).seconds < last_minutes * 60:
                return True
        return False


class CompetitionSchedule(BaseModel):
    config: dict[datetime.time, CompetitionManager]

    class Config:
        arbitrary_types_allowed = True


def get_competitions_schedule(
    bt_config,
    subtensor: bt.subtensor,
    chain_models_store: ChainMinerModelStore,
    hotkeys: List[str],
    validator_hotkey: str,
    test_mode: bool = False,
) -> CompetitionSchedule:
    """Returns CompetitionManager instances arranged by competition time"""
    scheduler_config = {}
    main_competitions_cfg = json.load(open("config/competition_config.json", "r"))
    for competition_cfg in main_competitions_cfg:
        for competition_time in competition_cfg["evaluation_times"]:
            parsed_time = datetime.strptime(competition_time, "%H:%M").time()
            scheduler_config[parsed_time] = CompetitionManager(
                config=bt_config,
                subtensor=subtensor,
                hotkeys=hotkeys,
                validator_hotkey=validator_hotkey,
                chain_miners_store=chain_models_store,
                competition_id=competition_cfg["competition_id"],
                category=competition_cfg["category"],
                dataset_hf_repo=competition_cfg["dataset_hf_repo"],
                dataset_hf_id=competition_cfg["dataset_hf_filename"],
                dataset_hf_repo_type=competition_cfg["dataset_hf_repo_type"],
                test_mode=test_mode,
            )
    return scheduler_config


async def run_competitions_tick(
    competition_scheduler: CompetitionSchedule,
    run_log: CompetitionRunStore,
) -> Tuple[str, str, ModelEvaluationResult] | Tuple[None, None, None]:
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
        competition_manager = competition_scheduler.get(check_time)
        if not competition_manager:
            continue

        bt.logging.debug(
            f"Found competition {competition_manager.competition_id} at {check_time}"
        )
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
        winning_evaluation_hotkey, winning_model_result = (
            await competition_manager.evaluate()
        )
        run_log.finish_run(competition_manager.competition_id)
        return (
            winning_evaluation_hotkey,
            competition_manager.competition_id,
            winning_model_result,
        )

    bt.logging.debug(
        f"Did not find any competitions to run for past {MINUTES_BACK} minutes"
    )
    await asyncio.sleep(20)
    return (None, None, None)
