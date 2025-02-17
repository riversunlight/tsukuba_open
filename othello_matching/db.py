import sqlite3

DATABASE = 'database.db'

def create_players_table():
    con = sqlite3.connect(DATABASE)
    con.execute("CREATE TABLE IF NOT EXISTS players (name, short, block, grade, status)")
    con.close()

def create_results_table():
    con = sqlite3.connect(DATABASE)
    con.execute("CREATE TABLE IF NOT EXISTS results (name, win int, lose int, stone_diff int, status)")
    con.close()

def create_new_matches_table():
    con = sqlite3.connect(DATABASE)
    con.execute("CREATE TABLE IF NOT EXISTS now_matches (player1, player2, winner)")
    con.close()

def create_new_game_result_table():
    con = sqlite3.connect(DATABASE)
    con.execute("CREATE TABLE IF NOT EXISTS game_result (round int, win_player, lose_player, stone_diff int)")
    con.close()
    