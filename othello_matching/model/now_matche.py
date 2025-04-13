import sqlite3

class NowMatchModel():
    DATABASE = 'database.db'
    
    def all(self):
        con = sqlite3.connect(self.DATABASE)
        res = con.execute('SELECT * FROM now_matches').fetchall()
        con.close()
        return res

    def add(self, player1, player2, winner):
        con = sqlite3.connect(self.DATABASE)
        con.execute('INSERT INTO now_matches VALUES(?, ?, ?)', [player1, player2, winner])
        con.commit()
        con.close()
    
    def during_game(self):
        con = sqlite3.connect(self.DATABASE)
        during_game = con.execute('SELECT * FROM now_matches WHERE winner = ?', ['PLAYING']).fetchall()
        con.close()
        return len(during_game)
    
    def delete(self, player):
        con = sqlite3.connect(self.DATABASE)
        con.execute('DELETE FROM now_matches WHERE player1 = ? OR player2 = ?', [player, player])
        con.close()
    
    def reset(self):
        con = sqlite3.connect(self.DATABASE)
        con.execute('DELETE FROM now_matches')
        con.commit()
        con.close()

    def reset_winner(self, player1, player2):
        con = sqlite3.connect(self.DATABASE)
        con.execute('UPDATE now_matches SET winner = ? WHERE (player1=? AND player2 = ?) OR (player1=? AND player2 = ?)', ["PLAYING", player1, player2, player2, player1])
        con.commit()
        con.close()
    
    def now_match(self, names):
        con = sqlite3.connect(self.DATABASE)
        now_match = con.execute('SELECT * FROM now_matches WHERE (player1 = ? AND player2 = ?) OR (player1 = ? AND player2 = ?)', [names[0], names[1], names[1], names[0]]).fetchall()
        con.close()
        return now_match 
        
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

    def reset_match(self, name1, name2):
        con = sqlite3.connect(self.DATABASE)
        con.execute('UPDATE now_matches SET winner = ? WHERE (player1=? AND player2 = ?) OR (player1=? AND player2 = ?)', ["PLAYING", name1, name2, name2, name1])
        con.commit()
        con.close()

    def set_winner(self, win_name):
        con = sqlite3.connect(self.DATABASE)
        con.execute('UPDATE now_matches SET winner=? WHERE player1=? OR player2=?', [win_name, win_name, win_name])
        con.commit()
        con.close()

    def get_data(self, name):
        con = sqlite3.connect(self.DATABASE)
        game_data = con.execute('SELECT * FROM now_matches WHERE player1=? OR player2=?', [name, name]).fetchall()
        con.close()
        return game_data
