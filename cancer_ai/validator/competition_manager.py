from .manager import SerializableManager


class CompetitionManager(SerializableManager):
    def __init__(self, config, competition_id: str) -> None:
        self.config = config
        self.competition_id = competition_id
