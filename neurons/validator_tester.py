from cancer_ai.validator.competition_manager import CompetitionManager
from datetime import time, datetime

import asyncio
import json
import timeit
from types import SimpleNamespace

from competition_config import competitions

# from cancer_ai.utils.config import config

path_config = {"model_dir": "/tmp/models", "models_dataset_dir": "/tmp/datasets"}
# path_config = {
#     "models": SimpleNamespace(
#         **{"model_dir": "/tmp/models", "models_dataset_dir": "/tmp/datasets"}
#     ),
# }
path_config = SimpleNamespace(**path_config)

# open competition config file
# def get_competition_config():
#     with open(config.validator.competition_config_path) as f:
#         return json.load(f)

# async def main_loop():
#     competitions = get_competition_config()
#     for competition_config in competitions:
#         # get list of competition_config["evaluation_time"] and time it to run during specific time of day
#         eval_times = [
#                       competition_config["evaluation_time"]]
#         while True:
#             now = time.localtime()
#             for eval_time in eval_times:
#                 if now.tm_hour == eval_time.hour and now.tm_min == eval_time.minute:
#                     competition = CompetitionManager(
#                         path_config,
#                         competition_config["competition_id"],
#                         competition_config["category"],
#                         competition_config["evaluation_time"],
#                         competition_config["dataset_hf_id"],
#                         competition_config["file_hf_id"],
#                     )
#                     await competition.evaluate()
#                     print(competition.results)
#                     break
#             await asyncio.sleep(60)


# def run():
# asyncio.run(main_loop())

if __name__ == "__main__":
    competition_managers_async = []
    for competition_config in competitions:
        competition_manager = CompetitionManager(
            path_config,
            competition_config["competition_id"],
            competition_config["category"],
            competition_config["evaluation_time"],
            competition_config["dataset_hf_id"],
            competition_config["file_hf_id"],
        )
        competition_managers_async.append(competition_manager)
    competition_managers_async_gathered = asyncio.gather(
        [
            competition_manager.evaluate()
            for competition_manager in competition_managers_async
        ]
    )
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(competition_managers_async_gathered)
    finally:
        loop.close()
    for competition_manager in competition_managers_async:
        print(
            f"Results of competition {competition_manager.competition_id}: {competition_manager.results}"
        )
