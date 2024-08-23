from cancer_ai.validator.competition_manager import CompetitionManager
from datetime import time, datetime

import asyncio
import json
import timeit
from types import SimpleNamespace
from datetime import datetime, timezone, timedelta
import bittensor as bt
from typing import List

from competition_config import competitions

# from cancer_ai.utils.config import config

# TODO integrate with bt config
path_config = SimpleNamespace(
    **{"model_dir": "/tmp/models", "models_dataset_dir": "/tmp/datasets"}
)


def calculate_next_evaluation_times(evaluation_times) -> List[datetime]:
    """Calculate the next evaluation times for a given list of times in UTC."""
    now_utc = datetime.now(timezone.utc)
    next_times = []

    for time_str in evaluation_times:
        # Parse the evaluation time to a datetime object in UTC
        evaluation_time_utc = datetime.strptime(time_str, "%H:%M").replace(
            tzinfo=timezone.utc, year=now_utc.year, month=now_utc.month, day=now_utc.day
        )

        # If the evaluation time has already passed today, schedule it for tomorrow
        if evaluation_time_utc < now_utc:
            evaluation_time_utc += timedelta(days=1)

        next_times.append(evaluation_time_utc)

    return next_times


async def schedule_competitions(
    competitions: CompetitionManager, path_config: str
) -> None:
    # Cache the next evaluation times for each competition
    print("Initializing competitions")
    next_evaluation_times = {}

    # Calculate initial evaluation times
    for competition_config in competitions:
        competition_id = competition_config["competition_id"]
        evaluation_times = competition_config["evaluation_time"]
        next_evaluation_times[competition_id] = calculate_next_evaluation_times(
            evaluation_times
        )
        print(
            f"Next evaluation times for competition {competition_id}: {next_evaluation_times[competition_id]}"
        )

    while True:
        now_utc = datetime.now(timezone.utc)

        for competition_config in competitions:
            competition_id = competition_config["competition_id"]
            # Get the cached next evaluation times
            next_times = next_evaluation_times[competition_id]

            for next_time in next_times:
                if now_utc >= next_time:
                    print(
                        f"Next evaluation time for competition {competition_id} is {next_time}"
                    )
                    # If it's time to run the competition
                    competition_manager = CompetitionManager(
                        path_config,
                        competition_config["competition_id"],
                        competition_config["category"],
                        competition_config["dataset_hf_id"],
                        competition_config["file_hf_id"],
                    )
                    print(f"Evaluating competition {competition_id} at {now_utc}")
                    await competition_manager.evaluate()
                    print(
                        f"Results for competition {competition_id}: {competition_manager.results}"
                    )

                    # Calculate the next evaluation time for this specific time
                    next_times.remove(next_time)
                    next_times.append(next_time + timedelta(days=1))

            # Update the cache with the next evaluation times
            next_evaluation_times[competition_id] = next_times
        if now_utc.minute % 5 == 0:
            print("Waiting for next scheduled competition")
        await asyncio.sleep(60) 

def run_all_competitions(path_config: str, competitions: List[dict]) -> None:
    for competition_config in competitions:
            print("Starting competition: ", competition_config)
            competition_manager = CompetitionManager(
                path_config,
                competition_config["competition_id"],
                competition_config["category"],
                competition_config["dataset_hf_id"],
                competition_config["file_hf_id"],
            )
            asyncio.run(competition_manager.evaluate())

if __name__ == "__main__":
    if True:  # run them right away
        run_all_competitions(path_config, competitions)
    
    else: # Run the scheduling coroutine
        asyncio.run(schedule_competitions(competitions, path_config))
