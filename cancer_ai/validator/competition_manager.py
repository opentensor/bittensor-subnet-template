from .manager import SerializableManager
from .model_manager import ModelManager

class CompetitionManager(SerializableManager):
    def __init__(self, config, competition_id: str) -> None:
        self.config = config
        self.competition_id = competition_i
        self.model_manager = ModelManager(config)

    def download_metadata(self, hotkeys) -> None:
        for hotkey in hotkeys:
            hotkey_model_info = "" # download from chain
            self.model_manager.add_model(hotkey, hotkey_model_info.repo_id, hotkey_model_info.filename)
            self.model_manager.download_miner_model(hotkey)

    def get_next_model(self):
        return self.model_manager.get_next_model()
        # return self.model_manager.get_state()



