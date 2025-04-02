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

    def get_status(self, name):
        pass

    def all(self):
        con = sqlite3.connect(self.DATABASE)
        data = con.execute("SELECT * FROM players").fetchall()
        con.close()

        res = []
        for row in data:
            res.append({'name': row[0], 'short': row[1], 'block': row[2], 'grade': row[3], 'status': row[4]})
        return res