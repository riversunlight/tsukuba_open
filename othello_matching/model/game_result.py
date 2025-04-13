import sqlite3

class GameResultModel():
    DATABASE = 'database.db'

    def game_no_battle(self, player1, player2):
        player = player1 if player2 == '-' else player2

        con = sqlite3.connect(self.DATABASE)
        data = con.execute('SELECT * FROM game_result WHERE round = ? AND (win_player = ? OR lose_player = ?)', [self.round, player, player]).fetchall()
        prev_stone = data[0][3]
        win_lose = "不戦勝" if data[0][1] == player else "不戦敗"
        con.close()
        return win_lose, prev_stone
    
    def person_game_result(self, name):
        con = sqlite3.connect(self.DATABASE)
        person_result_data = con.execute('SELECT * FROM game_result WHERE (win_player=? OR lose_player=?)', [name, name]).fetchall()
        con.close()
        return person_result_data
    
    def now_games(self, round):
        con = sqlite3.connect(self.DATABASE)
        game_data = con.execute("SELECT * FROM game_result WHERE round = ?", [round]).fetchall()
        con.close()
        return game_data

    def delete_now_games(self, round):
        con = sqlite3.connect(self.DATABASE)
        con.execute('DELETE FROM game_result WHERE round = ?', [round])
        con.commit()
        con.close()

    def add(self, round, win_name, lose_name, stone_diff):
        con = sqlite3.connect(self.DATABASE)
        con.execute('INSERT INTO game_result VALUES(?, ?, ?, ?)', [round, win_name, lose_name, stone_diff])
        con.commit()
        con.close()

    def get_game(self, name1, name2):
        con = sqlite3.connect(self.DATABASE)
        data = con.execute('SELECT * FROM game_result WHERE (win_player = ? AND lose_player=?) OR (win_player = ? AND lose_player=?)', [name1, name2, name2, name1]).fetchall()
        con.close()
        return data
    
    def get_now_game(self, round, name):
        con = sqlite3.connect(self.DATABASE)
        game_data = con.execute('SELECT * FROM game_result WHERE (win_player = ? OR lose_player = ?) AND round = ?', [name, name, round]).fetchall()
        con.close()
        return game_data
    
    def delete_game(self, win_name, lose_name):
        con = sqlite3.connect(self.DATABASE)
        con.execute('DELETE FROM game_result WHERE win_player = ? AND lose_player=?', [win_name, lose_name])
        con.commit()
        con.close()
    
    def delete_now_game(self, round, player):
        con = sqlite3.connect(self.DATABASE)
        con.execute('DELETE FROM game_result WHERE round = ? AND (win_player = ? OR lose_player = ?)', [round, player, player]).fetchall()
        con.commit()
        con.close()

    def reset(self):
        con = sqlite3.connect(self.DATABASE)
        con.execute("DELETE FROM game_result")
        con.commit()
        con.close()
