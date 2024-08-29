   
class Rewarder():
    def __init__(self, config=None):
        # competition_id to (hotkey_uid, days_as_leader)
        self.competitions_leaders = {
            1: (1, 1),
        }
        self.scores = {1:0}

    def calculate_score_for_winner(self, competition_id: int, hotkey_uid: int) -> tuple[float, float]:
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
            final_share = base_share * reduction_factor
            reduced_share = base_share - final_share
            return final_share, reduced_share
        return base_share, 0
    
    def update_scores(self):
        num_competitions = len(self.competitions_leaders)
        reduced_shares_poll = {uid: 0.0 for uid in self.scores}

        # If there is only one competition, the winner takes all
        if num_competitions == 1:
            for curr_competition_id, (current_uid, _) in self.competitions_leaders.items():
                self.scores[current_uid] = 1.0
            return
        
        for curr_competition_id, (current_uid, _) in self.competitions_leaders.items():
            score, reduced_share = self.calculate_score_for_winner(curr_competition_id, current_uid)
            self.scores[current_uid] += score

            if reduced_share > 0:
                # Distribute reduced share among all competitors (including the current winner if he wins another competition)
                distributed_share = reduced_share / (num_competitions - 1)
                for leader_competition_id, (uid, _) in self.competitions_leaders.items():
                    if uid != current_uid or leader_competition_id != curr_competition_id:
                        reduced_shares_poll[uid] += distributed_share
        
        for uid, score in self.scores.items():
            self.scores[uid] += reduced_shares_poll[uid]

rewarder = Rewarder()
rewarder.update_scores()
print(rewarder.scores)
print(rewarder.competitions_leaders)