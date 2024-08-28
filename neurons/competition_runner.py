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

import wandb

# from cancer_ai.utils.config import config

# TODO integrate with bt config
path_config = SimpleNamespace(
    **{"model_dir": "/tmp/models", "dataset_dir": "/tmp/datasets"}
)

competitions_cfg = json.load(open("neurons/competition_config.json", "r"))

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
                path_config, # TODO fetch bt config Konrad
                None,
                7,
                competition_cfg["competition_id"],
                competition_cfg["category"],
                competition_cfg["dataset_hf_repo"],
                competition_cfg["dataset_hf_filename"],
                competition_cfg["dataset_hf_repo_type"],
            )
    return scheduler_config

async def run_competitions(competition_times: List[CompetitionManager]) -> str | None:
    """Checks if time is right and launches competition, returns winning hotkey"""
    now_time = datetime.now()
    now_time = f"{now_time.hour}:{now_time.minute}"
    if now_time not in competition_times:
        return None
    for competition_time in competition_times:
        if now_time == competition_time:
            print(f"Running {competition_time.competition_id} at {now_time}")
            return await competition_time.evaluate()



if __name__ == "__main__":
    if True:  # run them right away
        run_all_competitions(path_config, competitions_cfg)
    
    else: # Run the scheduling coroutine
        scheduler_config = config_for_scheduler()
        asyncio.run(schedule_competitions(competitions, path_config))
