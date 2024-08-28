   
class Rewarder():
    def __init__(self, config=None):
        # competition_id to (hotkey_uid, days_as_leader)
        self.competitions_leaders = {
            1: (1, 21),
            2: (2, 3),
            3: (3, 28),
        }
        self.scores = {}

    def calculate_score_for_winner(self, competition_id: int, hotkey_uid: int) -> tuple[float, bool]:
        num_competitions = len(self.competitions_leaders)
        base_share = 1/num_competitions

        # check if current hotkey is already a leader
        if self.competitions_leaders[competition_id][0] == hotkey_uid:
            days_as_leader = self.competitions_leaders[competition_id][1]
        else:
            days_as_leader = 0
            self.competitions_leaders[competition_id] = (hotkey_uid, days_as_leader)

        if days_as_leader > 14:
            periods = (days_as_leader - 14) // 7
            reduction_factor = max(0.1, 1 - 0.1 * periods)
            return base_share * reduction_factor, periods > 0
        return base_share, False
    
    def update_scores(self):
        scores = {}
        for competition_id, (hotkey_uid, _) in self.competitions_leaders.items():
            score, is_reduced = self.calculate_score_for_winner(competition_id, hotkey_uid)
            print(score, is_reduced)
            scores[hotkey_uid] = (score, is_reduced)
        
        total_score_sum = sum(score for score, _ in scores.values())
        remaining_reward = 1 - total_score_sum
        non_reduced_scores = [hotkey_uid for hotkey_uid, (_, is_reduced) in scores.items() if not is_reduced]

        if non_reduced_scores:
            additional_reward_per_non_reduced = remaining_reward / len(non_reduced_scores)
            for hotkey_uid in non_reduced_scores:
                scores[hotkey_uid] = (scores[hotkey_uid][0] + additional_reward_per_non_reduced, scores[hotkey_uid][1])
            
        self.scores = {uid: score for uid, (score, _) in scores.items()}  

rewarder = Rewarder()
rewarder.update_scores()
print(rewarder.scores)
print(rewarder.competitions_leaders)