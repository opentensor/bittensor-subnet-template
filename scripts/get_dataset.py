from cancer_ai.validator.dataset_manager import DatasetManager
from types import SimpleNamespace, Tuple, List
config = {
    "dataset_dir": "./data",
}
config = SimpleNamespace( **config)

NAME_OF_COMPETITION="melanoma-1"
HUGGINFACE_DATASET_ID="safescanai/test_dataset"
HUGGINFACE_FILEPATH="skin_melanoma.zip"
HUGINGFACE_REPO_TYPE="dataset"

# can be also taken from competition_config.py



async def get_training_data() -> Tuple[List, List]:

    dataset_manager = DatasetManager(
        config,    
        NAME_OF_COMPETITION,
        HUGGINFACE_DATASET_ID,
        HUGGINFACE_FILEPATH,
        HUGINGFACE_REPO_TYPE
    )
    await dataset_manager.prepare_dataset()

    return await dataset_manager.get_data()

if __name__ == "__main__":
    import asyncio
    pred_x, pred_y = asyncio.run(get_training_data())
