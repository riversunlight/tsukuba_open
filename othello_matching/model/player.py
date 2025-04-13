import sqlite3

class PlayerModel():
    DATABASE = 'database.db'

    def add(self, name, short, block, grade):
        con = sqlite3.connect(self.DATABASE)
        con.execute('INSERT INTO players VALUES(?, ?, ?, ?, ?)', [name, short, block, grade, "参加"])
        con.commit()
        con.close()

    def delete(self, name):
        con = sqlite3.connect(self.DATABASE)
        con.execute('DELETE FROM players WHERE name = ?', [name])
        con.execute('DELETE FROM results WHERE name = ?', [name])
        con.commit()
        con.close()

    def get_player_data(self, name):
        con = sqlite3.connect(self.DATABASE)
        data = con.execute('SELECT * FROM players WHERE name = ?', [name]).fetchall()
        con.close()
        return {'name': data[0][0], 'short': data[0][1], 'block': data[0][2], 'grade': data[0][3], 'status': data[0][4]}

    def all(self):
        con = sqlite3.connect(self.DATABASE)
        data = con.execute("SELECT * FROM players").fetchall()
        con.close()

        res = []
        for row in data:
            res.append({'name': row[0], 'short': row[1], 'block': row[2], 'grade': row[3], 'status': row[4]})
        return res
    
    def change_status(self, name, status):
        con = sqlite3.connect(self.DATABASE)
        con.execute('UPDATE players SET status = ? WHERE name = ?', [status, name])
        con.commit()
        con.close()
    
    def reset(self):
        con = sqlite3.connect(self.DATABASE)
        con.execute("DELETE FROM players")
        con.commit()
        con.close()
