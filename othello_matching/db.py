import sqlite3

DATABASE = 'database.db'

def create_players_table():
    con = sqlite3.connect(DATABASE)
    con.execute("CREATE TABLE IF NOT EXISTS players (name, prefecture, grade)")
    con.close()

def create_results_table():
    con = sqlite3.connect(DATABASE)
    con.execute("CREATE TABLE IF NOT EXISTS results (name, win int, lose int, draw int, stone_diff int)")
    con.close()

def create_game_data_table():
    con = sqlite3.connect(DATABASE)
    con.execute("CREATE TABLE IF NOT EXISTS game_data (round int, during_game int)")
    res = con.execute("SELECT * FROM game_data").fetchall()
    if (len(res) == 0):
        con.execute("INSERT INTO game_data VALUES(?, ?)", [0, 0])
    con.commit()
    con.close()

def create_new_matches_table():
    con = sqlite3.connect(DATABASE)
    con.execute("CREATE TABLE IF NOT EXISTS now_matches (player1, player2, winner)")
    con.close()

def create_new_game_result_table():
    con = sqlite3.connect(DATABASE)
    con.execute("CREATE TABLE IF NOT EXISTS game_result (round int, win_player, lose_player, stone_diff int)")
    con.close()
    