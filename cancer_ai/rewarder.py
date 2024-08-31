from pydantic import BaseModel
from datetime import datetime, timedelta

class CompetitionLeader(BaseModel):
    hotkey: str
    leader_since: datetime
class Score(BaseModel):
    score: float
    reduction: float
class RewarderConfig(BaseModel):
    competitionID_to_leader_hotkey_map: dict[str, CompetitionLeader] # competition_id -> CompetitionLeader
    hotkey_to_score_map: dict[str, Score] # hotkey -> Score

class Rewarder():
    def __init__(self, rewarder_config: RewarderConfig):
        self.competition_leader_mapping = rewarder_config.competitionID_to_leader_hotkey_map
        self.scores = rewarder_config.hotkey_to_score_map

    def get_scores_and_reduction(self, competition_id: str, hotkey: str) -> tuple[float, float]:
        num_competitions = len(self.competition_leader_mapping)
        base_share = 1/num_competitions

        # check if current hotkey is already a leader
        if self.competition_leader_mapping[competition_id].hotkey == hotkey:
            days_as_leader = (datetime.now() - self.competition_leader_mapping[competition_id].leader_since).days
        else:
            days_as_leader = 0
            self.competition_leader_mapping[competition_id] = CompetitionLeader(hotkey=hotkey,
                                                                           leader_since=datetime.now())
        
        # Score degradation starts on 3rd week of leadership 
        if days_as_leader > 14:
            periods = (days_as_leader - 14) // 7
            reduction_factor = max(0.1, 1 - 0.1 * periods)
            final_share = base_share * reduction_factor
            reduced_share = base_share - final_share
            return final_share, reduced_share
        return base_share, 0
    
    def update_scores(self):
        num_competitions = len(self.competition_leader_mapping)

        # If there is only one competition, the winner takes it all
        if num_competitions == 1:
            competition_id = next(iter(self.competition_leader_mapping))
            hotkey = self.competition_leader_mapping[competition_id].hotkey
            self.scores[hotkey] = Score(score=1.0, reduction=0.0)
            return

        # gather reduced shares for all competitors
        competitions_without_reduction = []
        for curr_competition_id, comp_leader in self.competition_leader_mapping.items():
            score, reduced_share = self.get_scores_and_reduction(curr_competition_id, comp_leader.hotkey)
            self.scores[comp_leader.hotkey].score += score
            self.scores[comp_leader.hotkey].reduction += reduced_share
            if reduced_share == 0:
                competitions_without_reduction.append(curr_competition_id)
        
        total_reduced_share = sum([score.reduction for score in self.scores.values()])

        # if all competitions have reduced shares, distribute them among all competitors
        if len(competitions_without_reduction) == 0:
            # distribute the total reduced share among all competitors
            for hotkey, score in self.scores.items():
                self.scores[hotkey].score += total_reduced_share / num_competitions
            return
        else:
            # distribute the total reduced share among non-reduced competitons winners
            for comp_id in competitions_without_reduction:
                hotkey = self.competition_leader_mapping[comp_id].hotkey
                self.scores[hotkey].score += total_reduced_share / len(competitions_without_reduction)