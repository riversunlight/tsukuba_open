import random
import copy
import time
class Matcher: 
    def comp(self, player1, player2):
        score1 = player1['win']
        score2 = player2['win']
        if score1 > score2:
            return -1
        elif score1 < score2:
            return 1
        else:
            if player1['stone_diff'] > player2['stone_diff']:
                return -1
            elif player1['stone_diff'] < player2['stone_diff']:
                return 1
        return 1 - 2 * random.randint(0, 1)
    
    def c2(self, a, b):
        if a[0] < b[0]:
            return -1
        else:
            return 1
    
    def matching_cost(self, matches, already_battle):
        res = 0
        C_REMATCH = 10000000
        C_RANK = 1
        # 不戦勝: そういう人物がいることにする!!(順位は最下位)
        # 不戦勝っていう対戦相手と再戦するのもペナルティ
        for i in range(0, len(matches)):
            p1 = matches[i][0]
            p2 = matches[i][1]
            res += (p1 - p2) * (p1 - p2) * C_RANK
            res += already_battle[p1][p2] * C_REMATCH
        return res
    
    
    # タブーサーチが相性よさそう!
    # 同じ組み合わせが存在するのを部分的にでも防ぐ!!
    def concider_match(self, players, already_battle):
        matches = [[2 * i + j for j in range(0, 2)] for i in range(0, len(players) // 2)]
        best_cost = self.matching_cost(matches, already_battle)
        best_matches = copy.deepcopy(matches)
        tabu_span = 10
        tabu_list = [[- tabu_span - 10 for i in range(0, len(players))] for j in range(0, len(players))]
        exe_time = 1000
        start_time = time.time()
        search_cnt = 10000
        # 局所最適化
        for _ in range(0, search_cnt):
            if time.time() - start_time > exe_time:
                break
            next_cost = 1000000000
            next_matches = matches
            # 近傍解
            next_i = -1
            for i in range(0, len(matches) - 1):
                for j in range(0, 2):
                    new_match = copy.deepcopy(matches)
                    new_match[i][1], new_match[i + 1][j] = new_match[i + 1][j], new_match[i][1]
                    new_cost = self.matching_cost(new_match, already_battle)
    
                    if new_cost < best_cost:
                        best_matches = new_match
                        best_cost = new_cost
                    
                    prev_turn = max(tabu_list[new_match[i][0]][new_match[i][1]], tabu_list[new_match[i + 1][0]][new_match[i + 1][1]])
                    if _ - prev_turn < tabu_span:
                        continue
    
                    if new_cost < next_cost:
                        next_cost = new_cost
                        next_matches = new_match
                        next_i = i
            if next_i != -1:
                tabu_list[matches[next_i][0]][matches[next_i][1]] = _
                tabu_list[matches[next_i][1]][matches[next_i][0]] = _
                tabu_list[matches[next_i + 1][0]][matches[next_i + 1][1]] = _
                tabu_list[matches[next_i + 1][1]][matches[next_i + 1][0]] = _
            matches = copy.deepcopy(next_matches)
            
        return best_matches