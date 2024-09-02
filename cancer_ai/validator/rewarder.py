from pydantic import BaseModel
from datetime import datetime, timezone

class CompetitionLeader(BaseModel):
    hotkey: str
    leader_since: datetime
class Score(BaseModel):
    score: float
    reduction: float
class WinnersMapping(BaseModel):
    competition_leader_map: dict[str, CompetitionLeader] # competition_id -> CompetitionLeader
    hotkey_score_map: dict[str, Score] # hotkey -> Score

REWARD_REDUCTION_START_DAY = 30
REWARD_REDUCTION_STEP = 0.1
REWARD_REDUCTION_STEP_DAYS = 7

class Rewarder():
    def __init__(self, rewarder_config: WinnersMapping):
        self.competition_leader_mapping = rewarder_config.competition_leader_map
        self.scores = rewarder_config.hotkey_score_map

    async def get_miner_score_and_reduction(self, competition_id: str, hotkey: str) -> tuple[float, float]:
        # check if current hotkey is already a leader
        competition = self.competition_leader_mapping.get(competition_id)
        if competition and competition.hotkey == hotkey:
            days_as_leader = (datetime.now(timezone.utc) - self.competition_leader_mapping[competition_id].leader_since).days

        else:
            days_as_leader = 0
            self.competition_leader_mapping[competition_id] = CompetitionLeader(hotkey=hotkey,
                                                                           leader_since=datetime.now(timezone.utc))
            return
        
        # Score degradation starts on 3rd week of leadership 
        base_share = 1/len(self.competition_leader_mapping)
        if days_as_leader > REWARD_REDUCTION_START_DAY:
            periods = (days_as_leader - REWARD_REDUCTION_START_DAY) // REWARD_REDUCTION_STEP_DAYS
            reduction_factor = max(REWARD_REDUCTION_STEP, 1 - REWARD_REDUCTION_STEP * periods)
            final_share = base_share * reduction_factor
            reduced_share = base_share - final_share
            return final_share, reduced_share
        return base_share, 0
    
    async def update_scores(self, new_winner_hotkey: str, new_winner_comp_id: str):
        # reset the scores before updating them
        self.scores = {}
        
        # get score and reduced share for the new winner
        await self.get_miner_score_and_reduction(new_winner_comp_id, new_winner_hotkey)

        num_competitions = len(self.competition_leader_mapping)
        # If there is only one competition, the winner takes it all
        if num_competitions == 1:
            competition_id = next(iter(self.competition_leader_mapping))
            hotkey = self.competition_leader_mapping[competition_id].hotkey
            self.scores[hotkey] = Score(score=1.0, reduction=0.0)
            print("BRUNO WYGRAL", self.scores, self.competition_leader_mapping)
            return

        # gather reduced shares for all competitors
        competitions_without_reduction = []
        for curr_competition_id, comp_leader in self.competition_leader_mapping.items():
            score, reduced_share = await self.get_miner_score_and_reduction(curr_competition_id, comp_leader.hotkey)

            if comp_leader.hotkey in self.scores:
                self.scores[comp_leader.hotkey].score += score
                self.scores[comp_leader.hotkey].reduction += reduced_share
                if reduced_share == 0:
                    competitions_without_reduction.append(curr_competition_id)
            else:
                self.scores[comp_leader.hotkey] = Score(score=score, reduction=reduced_share)
                if reduced_share == 0:
                    competitions_without_reduction.append(curr_competition_id)
        
        total_reduced_share = sum([score.reduction for score in self.scores.values()])

        # if all competitions have reduced shares, distribute them among all competitors
        if len(competitions_without_reduction) == 0:
            # distribute the total reduced share among all competitors
            for hotkey, score in self.scores.items():
                self.scores[hotkey].score += total_reduced_share / num_competitions
            return
        
        # distribute the total reduced share among non-reduced competitons winners
        for comp_id in competitions_without_reduction:
            hotkey = self.competition_leader_mapping[comp_id].hotkey
            self.scores[hotkey].score += total_reduced_share / len(competitions_without_reduction)