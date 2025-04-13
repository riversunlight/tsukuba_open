# 大会情報の管理
import sqlite3
import csv
from functools import cmp_to_key
from othello_matching.model.player import PlayerModel
from othello_matching.model.result import ResultModel
from othello_matching.model.now_matche import NowMatchModel
from othello_matching.model.game_result import GameResultModel
from .matcher import Matcher

class GameManager():
    matcher = Matcher()
    player_model = PlayerModel()
    result_model = ResultModel()
    now_match_model = NowMatchModel()
    game_result_model = GameResultModel()

    DATABASE = 'database.db'


    def register(self, name, short, block, grade):
        self.player_model.add(name, short, block, grade)

    def delete_player(self, name):
        self.player_model.add(name)

    def game_data_no_battle(self, player1, player2):
        return self.game_result_model.game_no_battle(player1, player2)
    
    def person_result(self, name):
        person_result_data = self.game_result_model.person_game_result(name)

        person_results = []
        result_data = self.result_model.person_data(name)
        for row in person_result_data:
            my_id = 1
            tmp = {}
            if row[2]==name:
                my_id = 2
            tmp["round"] = row[0]
            tmp["opponent"] = row[((my_id - 1) ^ 1) + 1]
            tmp["stone"] = row[3]
            tmp["win"] = "O" if my_id == 1 else "X"
            person_results.append(tmp)
        total_win = result_data["win"]
        total_lose = result_data["lose"]
        total_stone = result_data["stone_diff"]
        
        return person_results, total_win, total_lose, total_stone
    
    def data_for_index(self):
        players = self.player_model.all()
        con = sqlite3.connect(self.DATABASE)
        db_player = con.execute("SELECT results.name, results.win, results.lose, results.stone_diff, players.status FROM results JOIN players ON results.name = players.name").fetchall()
        con.close()
        _match_data = self.now_match_model.all()
        matches_result = self.game_result_model.now_games(self.round)

        ranks = []
        now_matches = []
        no_matches = []
        end_game = 0

        winners = {}
        losers = {}
        for row in matches_result:
            winner = row[1]
            loser = row[2]
            stone_diff = row[3]
            winners[winner] = stone_diff
            losers[loser] = stone_diff
        
        for row in db_player:
            name = row[0]
            win = row[1]
            lose = row[2]
            stone_diff = row[3]
            status = row[4]
            finish_game = 0
            if name in winners:
                win += 1
                stone_diff += winners[name]
                finish_game = 1
            if name in losers:
                lose += 1
                stone_diff -= losers[name]
                finish_game = 1

            ranks.append({'name': name, 'win': win, 'lose': lose, 'stone_diff': stone_diff, 'status': status, 'end_game': finish_game})

        ranks = sorted(ranks, key=cmp_to_key(self.matcher.comp))

        game_data = [{'round': self.round, 'during_game': self.during_game}]
        for row in _match_data:
            if row[2] == "不戦勝" or row[2] == "不戦敗":
                no_matches.append({'player1': row[0], 'player2': row[1], 'winner': row[2]})
            else:
                now_matches.append({'player1': row[0], 'player2': row[1], 'winner': row[2]})
                if row[2] != "PLAYING":
                    end_game += 1
        return players, ranks, game_data, now_matches, end_game, no_matches
    
    def data_for_hand(self):
        now_matches = []
        players = []
        _match_data = self.now_match_model.all()
        _players = self.player_model.all()
        
        for row in _match_data:
            now_matches.append({'player1': row[0], 'player2': row[1], 'winner': row[2]})
        for player in _players:
            players.append({'name': player.name})
        
        return now_matches, players
    
    def update_grades(self):
        if self.round == 0:
            players = self.player_model.all()
            for player in players:
                self.result_model.add(player["name"])
        else:
            round = self.round
            now_games = self.game_result_model.now_games(round)
            for row in now_games:
                winner = row[1]
                loser = row[2]
                stone_diff = row[3]
                if winner != "不戦敗":
                    self.result_model.update_data(winner, True, stone_diff)
                if loser != "不戦勝":
                    self.result_model.update_data(loser, False, stone_diff)

    def is_game_end(self):
        round = self.round
        if self.round == 0:
            return True
        now_matches = self.game_result_model.now_games(round)
        res = True
        cnt = 0
        for row in now_matches:
            if not (row[1] == "不戦勝" or row[1] == "不戦敗" or row[2] == "不戦勝" or row[3] == "不戦敗"):
                cnt += 1

        if cnt == 0:
            res = False
        return res
    
    def matching(self):
        if self.is_game_end():
            self.update_grades()
        else:
            self.game_result_model.delete_now_games(self.round)

        # DBからデータを持ってきて保存
        players = []
        no_players = []
        con = sqlite3.connect(self.DATABASE)
        ranks_data = con.execute('SELECT results.name, results.win, results.lose, results.stone_diff, players.status FROM results JOIN players ON results.name = players.name').fetchall()
        con.close()
        for row in ranks_data:
            name, win, lose, stone_diff, status = row
            if status == "参加":
                players.append({'name': name, 'win': win, 'lose': lose, 'stone_diff': stone_diff})
            else:
                no_players.append(name)
        
        # 順位順にsort(比較関数作ってやる)
        players = sorted(players, key=cmp_to_key(self.matcher.comp))
        if len(players) % 2 == 1:
            players.append({'name': "不戦勝", 'win': 0, 'lose': 100, 'stone_diff': -1000})
    
        players_id = [0 for i in range(0, (len(players)))]
        #ここまでの工夫で遅刻早退対応!!(入力受け取り)
    
        already_battle = [[0 for i in range(0, len(players_id))] for j in range(0, len(players_id))]
        for i in range(0, len(players)):
            for j in range(0, len(players)):
                if players[i]['name'] == players[j]['name']:
                    continue
                befo_game = self.game_result_model.get_game(players[i]['name'], players[j]['name'])
                if len(befo_game) != 0:
                    already_battle[i][j] = 1
                    already_battle[j][i] = 1
        pairs = self.matcher.concider_match(players_id, already_battle)

        round = self.round
        self.now_match_model.reset()
        no_game_player = -1
        for pair in pairs:
            player1 = players[pair[0]]['name']
            player2 = players[pair[1]]['name']
            if player1 == "不戦勝":
                no_game_player = pair[1]
                continue
            if player2 == "不戦勝":
                no_game_player = pair[0]
                continue
            self.now_match_model.add(player1, player2, "PLAYING")

        if no_game_player != -1:
            player1 = players[no_game_player]['name']
            self.game_result_model.add(round, player1, "不戦勝", 2)
            self.now_match_model.add(player1, "-", "不戦勝")            

        for name in no_players:
            self.game_result_model.add(round, "不戦敗", name, 64)
            self.now_match_model.add(player1, "-", "不戦敗")
        
        
        
    def fix_prev_game(self, win_name, round, stone_diff):
        lose_name = "?"
        game_data = self.game_result_model.get_now_game(round, win_name)
        for row in game_data:
            if row[1]==win_name:
                lose_name=row[2]
            else:
                lose_name=row[1]
    
        # 訂正時
        data = self.game_result_model.get_game(win_name, lose_name)
        if len(data) == 1:
          prev_win = data[0][1]
          prev_lose = data[0][2]
          prev_stone_diff = data[0][3]
          self.game_result_model.delete_game(prev_win, prev_lose)
          if round != self.round:
              self.result_model.fix_data(prev_win, True, prev_stone_diff)
              self.result_model.fix_data(prev_lose, False, prev_stone_diff)
        self.game_result_model.add(round, win_name, lose_name, stone_diff)
        if round != self.round:
            self.result_model.update_data(win_name, True, stone_diff)
            self.result_model.update_data(lose_name, False, stone_diff)
        

    def fix_no_game(self, player, kind, stone_diff):
        self.game_result_model.delete_now_game(self.round, player)
        self.now_match_model.delete(player)
    
        if kind == "不戦勝":
            self.game_result_model.add(self.round, player, "不戦勝", stone_diff)
            self.now_match_model.add(player, "-", "不戦勝")
        else:
            self.game_result_model.add(self.round, "不戦敗", player, stone_diff)
            self.now_match_model.add(player, "-", "不戦敗")

    def get_game_result(self, player1, player2):
        data = self.game_result_model.get_game(player1, player2)
        round = data[0][0]
        prev_win = data[0][1]
        prev_lose = data[0][2]
        stone_diff = data[0][3]

        return round, {'winner': prev_win, 'loser': prev_lose, 'stone_diff': stone_diff}

    def delete_match(self, name1, name2):
        data = self.game_result_model.get_game(name1, name2)
        if len(data) == 1:
            prev_win = data[0][1]
            prev_lose = data[0][2]
            self.game_result_model.delete_game(prev_win, prev_lose)
            self.now_match_model.reset_match(name1, name2)

    def get_status(self, name):
        return self.player_model.get_player_data(name)['status']

    def change_status_exe(self, name, status):
        self.player_model.change_status(name, status)
    
    def reset_database(self):
        con = sqlite3.connect(self.DATABASE)
        con.execute('DELETE FROM players')
        con.execute('DELETE FROM results')
        con.execute("DELETE FROM now_matches")
        con.execute("DELETE FROM game_result")
        con.commit()
        con.close()
        
    
    def outcsv(self):
        datas = []
        players = []
        ranks_data = self.result_model.all()
        for row in ranks_data:
            players.append(row)
        
        players = sorted(players, key=cmp_to_key(self.matcher.comp))
    
        for player in players:
            name = player['name']
            player_info = self.player_model.get_player_data(name)
            result_info = self.result_model.person_data(name)
            battle_info = self.game_result_model.person_game_result(name)
            battle = []
            battles = []
            for row in battle_info:
                tmp = []
                tmp.append(row[0])
                tmp.append(row[1])
                tmp.append(row[2])
                tmp.append(row[3])
                battles.append(tmp)
            battles = sorted(battles, key=cmp_to_key(self.matcher.c2))
    
            for row in battles:
                win = True if row[1] == name else False
                tmp = {}
                opponent=""
                if win:
                    tmp['result'] = "〇"
                    opponent=row[2]
                else:
                    tmp['result'] = "×"
                    opponent=row[1]
                tmp['stone_diff'] = row[3]
                if not win:
                    tmp['stone_diff'] *= -1
                opponent_info = self.player_model.get_player_data(opponent)
                tmp['opponent'] = opponent_info['name']
                battle.append(tmp)

            datas.append({'name': player['name'], 'short': player_info['short'], 'block':player_info['block'], 'grade': player_info['grade'], 'win': result_info['win'], 'lose': result_info['lose'], 'stone_diff': result_info['stone_diff'], 'battle': battle })
    
        with open('result.csv', 'w', newline="") as f:
            writer = csv.writer(f)
            prev_win = 100
            prev_stone = 600
            rank = 0
            id = 0
            for data in datas:
                id += 1
                if prev_win != data['win'] or (prev_win == data['win'] and prev_stone != data['stone_diff']):
                    rank = id
                prev_win = data['win']
                prev_stone = data['stone_diff']
                write_row1 = [str(rank) + ".", data['name'], data['short']]
                write_row2 = ['', data['block'], data['grade']]
                stone_tot = 0
                for row in data['battle']:
                    stone_tot += row['stone_diff']
                    write_row1.append(row['result'] + str(row['stone_diff']))
                    write_row2.append(row['opponent'])
    
                write_row1.append(str(data['win']) + "勝" + str(data['lose']) +  "敗")
                write_row2.append(str(stone_tot))
                writer.writerow(write_row1)
                writer.writerow(write_row2)
    
    @property
    def round(self):
        game_result = self.result_model.all()
        now_matches = self.now_match_model.all()
        
        res = 0 if len(now_matches) == 0 else 1
        if len(game_result) >= 1:
            res = game_result[0]['win'] + game_result[0]['lose'] + 1
        return res
    
    def now_match(self, names):
        return self.now_match_model.now_match(names)
        

    def game_input(self, win_name, stone_diff):
        lose_name = "?"
        round = self.round
        game_data = self.now_match_model.get_data(win_name)
        for row in game_data:
            if row[0]==win_name:
                lose_name=row[1]
            else:
                lose_name=row[0]
        # 訂正時
        data = self.game_result_model.get_game(win_name, lose_name)
        if len(data) == 1:
            prev_win = data[0][1]
            prev_lose = data[0][2]
            prev_stone_diff = data[0][3]
            self.game_result_model.delete_game(self, prev_win, lose_name)

        self.game_result_model.add(round, win_name, lose_name, stone_diff)
        self.now_match_model.set_winner(win_name)

    def swap_matches(self, names):
        self.now_match_model.swap_matches(names)
        

    @property
    def during_game(self):
        return self.now_match_model.during_game()