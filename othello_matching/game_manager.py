# 大会情報の管理
import sqlite3
import csv
from functools import cmp_to_key
from othello_matching.player import PlayerModel
from .matcher import Matcher

class GameManager():
    matcher = Matcher()
    player_model = PlayerModel()
    DATABASE = 'database.db'


    def register(self, name, short, block, grade):
        self.player_model.add(name, short, block, grade)

    def delete_player(self, name):
        self.player_model.add(name)

    def game_data_no_battle(self, player1, player2):
        con = sqlite3.connect(self.DATABASE)
        player = player1 if player2 == '-' else player2

        data = con.execute('SELECT * FROM game_result WHERE round = ? AND (win_player = ? OR lose_player = ?)', [self.round, player, player]).fetchall()
        prev_stone = data[0][3]
        win_lose = "不戦勝" if data[0][1] == player else "不戦敗"
        return win_lose, prev_stone
    
    def person_result(self, name):
        con = sqlite3.connect(self.DATABASE)
        person_result_data = con.execute('SELECT * FROM game_result WHERE (win_player=? OR lose_player=?)', [name, name]).fetchall()
        person_results = []
        result_data = con.execute('SELECT * FROM results WHERE name=?', [name]).fetchall()
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
        for row in result_data:
            total_win = row[1]
            total_lose = row[2]
            total_stone = row[3]
        con.close()
        return person_results, total_win, total_lose, total_stone
    
    def data_for_index(self):
        con = sqlite3.connect(self.DATABASE)
        players = self.player_model.all()
        db_player = con.execute("SELECT results.name, results.win, results.lose, results.stone_diff, players.status FROM results JOIN players ON results.name = players.name").fetchall()
        _match_data = con.execute("SELECT * FROM now_matches").fetchall()
        matches_result = con.execute("SELECT * FROM game_result WHERE round = ?", [self.round]).fetchall()

        con.close()
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
        con = sqlite3.connect(self.DATABASE)
        _match_data = con.execute("SELECT * FROM now_matches").fetchall()
        _players = self.player_model.all()
        for row in _match_data:
            now_matches.append({'player1': row[0], 'player2': row[1], 'winner': row[2]})
        for player in _players:
            players.append({'name': player.name})
        con.close()
        return now_matches, players
    
    def update_grades(self):
        con = sqlite3.connect(self.DATABASE)
        if self.round == 0:
            players = self.player_model.all()
            for player in players:
                con.execute("INSERT INTO results VALUES(?, ?, ?, ?)", [player.name, 0, 0, 0])
        else:
            round = self.round
            now_games = con.execute("SELECT * FROM game_result WHERE round = ?", [round]).fetchall()
            for row in now_games:
                winner = row[1]
                loser = row[2]
                stone_diff = row[3]
                if winner != "不戦敗":
                    con.execute('UPDATE results SET win = win + 1 WHERE name = ?', [winner])
                    con.execute('UPDATE results SET stone_diff = stone_diff + ? WHERE name = ?', [stone_diff, winner])
                if winner != "不戦勝":
                    con.execute('UPDATE results SET lose = lose + 1 WHERE name = ?', [loser])
                    con.execute('UPDATE results SET stone_diff = stone_diff - ? WHERE name = ?', [stone_diff, loser])
        con.commit()
        con.close()

    def is_game_end(self):
        con = sqlite3.connect(self.DATABASE)
        round = self.round
        if self.round == 0:
            return True
        now_matches = con.execute("SELECT * FROM game_result WHERE round = ?", [round]).fetchall()
        res = True
        cnt = 0
        for row in now_matches:
            if not (row[1] == "不戦勝" or row[1] == "不戦敗" or row[2] == "不戦勝" or row[3] == "不戦敗"):
                cnt += 1

        if cnt == 0:
            res = False
        con.close()
        return res
    
    def matching(self):
        if self.is_game_end():
            self.update_grades()
        else:
            con = sqlite3.connect(self.DATABASE)
            con.execute('DELETE FROM game_result WHERE round = ?', [self.round])
            con.commit()
            con.close()

        # DBからデータを持ってきて保存
        players = []
        no_players = []
        con = sqlite3.connect(self.DATABASE)
        ranks_data = con.execute('SELECT results.name, results.win, results.lose, results.stone_diff, players.status FROM results JOIN players ON results.name = players.name').fetchall()
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
                befo_game = con.execute("SELECT * FROM game_result WHERE (win_player=? AND lose_player=?) OR (win_player=? AND lose_player=?)", [players[i]['name'], players[j]['name'], players[j]['name'], players[i]['name']]).fetchall()
                if len(befo_game) != 0:
                    already_battle[i][j] = 1
                    already_battle[j][i] = 1
        con.close()
        pairs = self.matcher.concider_match(players_id, already_battle)

        con = sqlite3.connect(self.DATABASE)
        round = self.round
        con.execute("DELETE FROM now_matches")
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
            con.execute("INSERT INTO now_matches VALUES(?, ?, ?)", [player1, player2, "PLAYING"])

        if (no_game_player != -1):
            player1 = players[no_game_player]['name']
            con.execute('INSERT INTO game_result VALUES (?, ?, ?, ?)', [round, player1, "不戦勝", 2])
            con.execute("INSERT INTO now_matches VALUES (?, ?, ?)", [player1, "-", "不戦勝"])

        for name in no_players:
            con.execute('INSERT INTO game_result VALUES (?, ?, ?, ?)', [round, "不戦敗", name, 64])
            con.execute("INSERT INTO now_matches VALUES(?, ?, ?)", [player1, "-", "不戦敗"])
    
        con.commit()
        con.close()
        
    def fix_prev_game(self, win_name, round, stone_diff):
        lose_name = "?"
        con = sqlite3.connect(self.DATABASE)
        game_data = con.execute('SELECT * FROM game_result WHERE (win_player = ? OR lose_player = ?) AND round = ?', [win_name, win_name, round]).fetchall()
        for row in game_data:
            if row[1]==win_name:
                lose_name=row[2]
            else:
                lose_name=row[1]
    
        # 訂正時
        data = con.execute('SELECT * FROM game_result WHERE (win_player = ? AND lose_player=?) OR (win_player = ? AND lose_player=?)', [win_name, lose_name, lose_name, win_name]).fetchall()
        if len(data) == 1:
          prev_win = data[0][1]
          prev_lose = data[0][2]
          prev_stone_diff = data[0][3]
          con.execute('DELETE FROM game_result WHERE win_player = ? AND lose_player=?', [prev_win, prev_lose])
          if round != self.round:
              con.execute('UPDATE results SET win = win - 1 WHERE name = ?', [prev_win])
              con.execute('UPDATE results SET stone_diff = stone_diff - ? WHERE name = ?', [prev_stone_diff, prev_win])
              con.execute('UPDATE results SET lose = lose - 1 WHERE name = ?', [prev_lose])
              con.execute('UPDATE results SET stone_diff = stone_diff + ? WHERE name = ?', [prev_stone_diff, prev_lose])
    
        con.execute('INSERT INTO game_result VALUES(?, ?, ?, ?)', [round, win_name, lose_name, stone_diff])
        
        if round != self.round:
            con.execute('UPDATE results SET win = win + 1 WHERE name = ?', [win_name])
            con.execute('UPDATE results SET stone_diff = stone_diff + ? WHERE name = ?', [stone_diff, win_name])
            con.execute('UPDATE results SET lose = lose + 1 WHERE name = ?', [lose_name])
            con.execute('UPDATE results SET stone_diff = stone_diff - ? WHERE name = ?', [stone_diff, lose_name])
        
        con.commit()
        con.close()

    def fix_no_game(self, player, kind, stone_diff):
        con = sqlite3.connect(self.DATABASE)
        con.execute('DELETE FROM game_result WHERE round = ? AND (win_player = ? OR lose_player = ?)', [self.round, player, player]).fetchall()
        con.execute('DELETE FROM now_matches WHERE player1 = ? OR player2 = ?', [player, player]).fetchall()
    
        if kind == "不戦勝":
            con.execute('INSERT INTO game_result VALUES(?, ?, ?, ?)', [self.round, player, "不戦勝", stone_diff])
            con.execute('INSERT INTO now_matches VALUES(?, ?, ?)', [player, "-", "不戦勝"])
        else:
            con.execute('INSERT INTO game_result VALUES(?, ?, ?, ?)', [self.round, "不戦敗", player, stone_diff])
            con.execute('INSERT INTO now_matches VALUES(?, ?, ?)', [player, "-", "不戦敗"])
        
        con.commit()
        con.close()

    def get_game_result(self, player1, player2):
        con = sqlite3.connect(self.DATABASE)
        data = con.execute('SELECT * FROM game_result WHERE (win_player = ? AND lose_player=?) OR (win_player=? AND lose_player=?)', [player1, player2, player2, player1]).fetchall()
        round = data[0][0]
        prev_win = data[0][1]
        prev_lose = data[0][2]
        stone_diff = data[0][3]
        con.close()
        return round, {'winner': prev_win, 'loser': prev_lose, 'stone_diff': stone_diff}

    def delete_match(self, name1, name2):
        con = sqlite3.connect(self.DATABASE)
        data = con.execute('SELECT * FROM game_result WHERE (win_player = ? AND lose_player=?) OR (win_player = ? AND lose_player=?)', [name1, name2, name2, name1]).fetchall()
        if len(data) == 1:
            prev_win = data[0][1]
            prev_lose = data[0][2]
            prev_stone_diff = data[0][3]
            con.execute('DELETE FROM game_result WHERE win_player = ? AND lose_player=?', [prev_win, prev_lose])
            con.execute('UPDATE now_matches SET winner = ? WHERE (player1=? AND player2 = ?) OR (player1=? AND player2 = ?)', ["PLAYING", name1, name2, name2, name1])
        con.commit()
        con.close()

    def get_status(self, name):
        con = sqlite3.connect(self.DATABASE)
        player = con.execute('SELECT * FROM players WHERE name=?', [name]).fetchall()
        status = player[0][4]
        con.close()
        return status

    def change_status_exe(self, name, status):
        con = sqlite3.connect(self.DATABASE)
        con.execute('UPDATE players SET status = ? WHERE name = ?', [status, name])
        con.commit()
        con.close()
    
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
        con = sqlite3.connect(self.DATABASE)
        ranks_data = con.execute('SELECT * FROM results').fetchall()
        for row in ranks_data:
            players.append({'name': row[0], 'win': row[1], 'lose': row[2], 'stone_diff': row[3]})
        
        players = sorted(players, key=cmp_to_key(self.matcher.comp))
    
        for player in players:
            name = player['name']
            player_info = con.execute('SELECT * FROM players WHERE name=?', [name]).fetchall()
            result_info = con.execute('SELECT * FROM results WHERE name=?', [name]).fetchall()
            battle_info = con.execute('SELECT * FROM game_result WHERE win_player=? OR lose_player=?', [name, name]).fetchall()
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
                opponent_info = con.execute('SELECT * FROM players WHERE name=?', [opponent]).fetchall()
                tmp['opponent'] = opponent_info[0][1]
                battle.append(tmp)
    
            datas.append({'name': player['name'], 'short': player_info[0][1], 'block':player_info[0][2], 'grade': player_info[0][3], 'win': result_info[0][1], 'lose': result_info[0][2], 'stone_diff': result_info[0][3], 'battle': battle })
    
        con.close()
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
        con = sqlite3.connect(self.DATABASE)
        game_result = con.execute('SELECT * FROM results').fetchall()
        now_matches = con.execute('SELECT * FROM now_matches').fetchall()
        
        res = 0 if len(now_matches) == 0 else 1
        for row in game_result:
            res = row[1] + row[2] + 1
            break
        con.close()
        return res
    
    def now_match(self,names):
        con = sqlite3.connect(self.DATABASE)
        now_match = con.execute('SELECT * FROM now_matches WHERE (player1 = ? AND player2 = ?) OR (player1 = ? AND player2 = ?)', [names[0], names[1], names[1], names[0]]).fetchall()
        con.close()
        return now_match

    def game_input(self, win_name, stone_diff):
        round_int = 10
        lose_name = "?"
        con = sqlite3.connect(self.DATABASE)
        round_int = self.round
        game_data = con.execute('SELECT * FROM now_matches WHERE player1=? OR player2=?', [win_name, win_name]).fetchall()
        for row in game_data:
            if row[0]==win_name:
                lose_name=row[1]
            else:
                lose_name=row[0]
        # 訂正時
        data = con.execute('SELECT * FROM game_result WHERE (win_player = ? AND lose_player=?) OR (win_player = ? AND lose_player=?)', [win_name, lose_name, lose_name, win_name]).fetchall()
        if len(data) == 1:
            prev_win = data[0][1]
            prev_lose = data[0][2]
            prev_stone_diff = data[0][3]
            con.execute('DELETE FROM game_result WHERE win_player = ? AND lose_player=?', [prev_win, prev_lose])

        con.execute('INSERT INTO game_result VALUES(?, ?, ?, ?)', [round_int, win_name, lose_name, stone_diff])
        game_data = con.execute('UPDATE now_matches SET winner=? WHERE player1=? OR player2=?', [win_name, win_name, win_name])
        con.commit()
        con.close()

    def swap_matches(self, names):
        oppos = ["_", "__"]
        con = sqlite3.connect(self.DATABASE)
        for i in range(0, 2):
            mch = con.execute("SELECT * FROM now_matches WHERE player1 = ? OR player2 = ?", [names[i], names[i]]).fetchall()
            oppos[i] = mch[0][0] if mch[0][0] != names[i] else mch[0][1]

        for i in range(0, 2):
            con.execute("DELETE FROM now_matches WHERE (player1 = ? AND player2 = ?) OR (player1 = ? AND player2 = ?)", [names[i], oppos[i], oppos[i], names[i]])
    
        con.execute("INSERT INTO now_matches VALUES(?, ?, ?)", [names[0], names[1], "PLAYING"])
        con.execute("INSERT INTO now_matches VALUES(?, ?, ?)", [oppos[0], oppos[1], "PLAYING"])
    
        con.commit()
        con.close()

    @property
    def during_game(self):
        con = sqlite3.connect(self.DATABASE)
        during_game = con.execute('SELECT * FROM now_matches WHERE winner = ?', ["PLAYING"]).fetchall()
        con.close()
        return len(during_game)