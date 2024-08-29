from pydantic import BaseModel
from datetime import datetime

class CompetitionLeader(BaseModel):
    hotkey: str
    leader_since: datetime

class RewarderConfig(BaseModel):
    competition_leader_mapping: dict[str, CompetitionLeader]
    scores: dict[str, float] # hotkey -> score

class Rewarder():
    def __init__(self, config: RewarderConfig):
        self.competition_leader_mapping = config.competition_leader_mapping
        self.scores = config.scores

    def calculate_score_for_winner(self, competition_id: str, hotkey: str) -> tuple[float, float]:
        num_competitions = len(self.competition_leader_mapping)
        base_share = 1/num_competitions

        # check if current hotkey is already a leader
        if self.competition_leader_mapping[competition_id].hotkey == hotkey:
            days_as_leader = (datetime.now() - self.competition_leader_mapping[competition_id].leader_since).days
        else:
            days_as_leader = 0
            self.competition_leader_mapping[competition_id] = CompetitionLeader(hotkey=hotkey,
                                                                           leader_since=datetime.now())

        if days_as_leader > 14:
            periods = (days_as_leader - 14) // 7
            reduction_factor = max(0.1, 1 - 0.1 * periods)
            final_share = base_share * reduction_factor
            reduced_share = base_share - final_share
            return final_share, reduced_share
        return base_share, 0
    
    def update_scores(self):
        num_competitions = len(self.competition_leader_mapping)
        reduced_shares_poll = {hotkey: 0.0 for hotkey in self.scores}

        # If there is only one competition, the winner takes it all
        if num_competitions == 1:
            single_key = next(iter(self.competition_leader_mapping))
            single_hotkey = self.competition_leader_mapping[single_key].hotkey
            self.scores[single_hotkey] = 1.0
            return
        
        for curr_competition_id, comp_leader in self.competition_leader_mapping.items():
            score, reduced_share = self.calculate_score_for_winner(curr_competition_id, comp_leader.hotkey)
            self.scores[comp_leader.hotkey] += score

            if reduced_share > 0:
                # Distribute reduced share among all competitors (including the current winner if he wins another competition)
                distributed_share = reduced_share / (num_competitions - 1)
                for leader_competition_id, leader in self.competition_leader_mapping.items():
                    if leader.hotkey != comp_leader.hotkey or leader_competition_id != curr_competition_id:
                        reduced_shares_poll[leader.hotkey] += distributed_share
        
        for hotkey, score in self.scores.items():
            self.scores[hotkey] += reduced_shares_poll[hotkey]