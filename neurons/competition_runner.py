from cancer_ai.validator.competition_manager import CompetitionManager
from cancer_ai.validator.competition_handlers.base_handler import ModelEvaluationResult
from datetime import time, datetime

import asyncio
import json
import timeit
from types import SimpleNamespace
from datetime import datetime, timezone, timedelta
import bittensor as bt
from typing import List

from competition_config import competitions as competitions_cfg

import wandb

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

def log_results_to_wandb(project, entity, hotkey, evaluation_result: ModelEvaluationResult):
    wandb.init(project=project, entity=entity)  # TODO: Update this line as needed

    wandb.log({
        "hotkey": hotkey,
        "tested_entries": evaluation_result.tested_entries,
        "model_test_run_time": evaluation_result.run_time,
        "accuracy": evaluation_result.accuracy,
        "precision": evaluation_result.precision,
        "recall": evaluation_result.recall,
        "confusion_matrix": evaluation_result.confusion_matrix.tolist(),
        "roc_curve": {
            "fpr": evaluation_result.fpr.tolist(),
            "tpr": evaluation_result.tpr.tolist()
        },
        "roc_auc": evaluation_result.roc_auc
    })

    wandb.finish()
    return


async def schedule_competitions(
    competitions: List[CompetitionManager], path_config: str
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
                        None,
                        7,
                        competition_config["competition_id"],
                        competition_config["category"],
                        competition_config["dataset_hf_repo"],
                        competition_config["dataset_hf_filename"],
                        competition_config["dataset_hf_repo_type"],
                    )
                    print(f"Evaluating competition {competition_id} at {now_utc}")
                    results = await competition_manager.evaluate()
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
            asyncio.run(competition_manager.evaluate())

if __name__ == "__main__":
    if True:  # run them right away
        run_all_competitions(path_config, competitions_cfg)
    
    else: # Run the scheduling coroutine
        asyncio.run(schedule_competitions(competitions, path_config))
