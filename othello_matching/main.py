from othello_matching import app
from flask import render_template, request, redirect, url_for
from functools import cmp_to_key
import sqlite3
import json
import random
DATABASE = 'database.db'

def comp(player1, player2):
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

#トップページ
@app.route('/')
def index():
    print("a")
    con = sqlite3.connect(DATABASE)
    db_player = con.execute("SELECT * FROM results").fetchall()
    _game_data = con.execute("SELECT * FROM game_data").fetchall()
    _match_data = con.execute("SELECT * FROM now_matches").fetchall()
    con.close()
    print("b")
    ranks = []
    game_data = []
    now_matches = []
    for row in db_player:
        ranks.append({'name': row[0], 'win': row[1], 'lose': row[2], 'stone_diff': row[3]})
    ranks = sorted(ranks, key=cmp_to_key(comp))
    for row in _game_data:
        game_data.append({'round': row[0], 'during_game': row[1]})
    for row in _match_data:
        now_matches.append({'player1': row[0], 'player2': row[1], 'winner': row[2]})
    print(now_matches)
    return render_template(
        'index.html',
        ranks=ranks,
        game_data=game_data,
        now_matches=now_matches
    )

@app.route('/add_player')
def add_player():
    return render_template(
        'add_player.html'
    )

@app.route('/add_game')
def add_game():
    player1 = request.args.get('player1')
    player2 = request.args.get('player2')
    return render_template(
        'game_input.html',
        player1=player1,
        player2=player2
    )

@app.route('/register', methods=['POST'])
def register():
    print("he")
    name = request.form['name']
    short = request.form['short']
    block = request.form['block']
    grade = request.form['grade']
    print(grade)
    con = sqlite3.connect(DATABASE)
    con.execute('INSERT INTO players VALUES(?, ?, ?, ?)', [name, short, block, grade])
    con.execute('INSERT INTO results VALUES(?, ?, ?, ?)', [name, 0, 0, 0])
    con.commit()
    con.close()
    return redirect(url_for('index'))

@app.route('/matching')
def matching():
    # DBからデータを持ってきて保存
    players = []
    con = sqlite3.connect(DATABASE)
    ranks_data = con.execute('SELECT * FROM results').fetchall()
    for row in ranks_data:
        players.append({'name': row[0], 'win': row[1], 'lose': row[2], 'stone_diff': row[3]})
    
    # 順位順にsort(比較関数作ってやる)
    players = sorted(players, key=cmp_to_key(comp))

    n = len(players)
    pairs = []
    dicided = [0] * n
    for i in range(0, n):
        if (dicided[i]):
            continue;
        for j in range(i + 1, n):
            if (dicided[j]):
                continue
            # すでに当たってたら飛ばす
            befo_game = con.execute("SELECT * FROM game_result WHERE (win_player=? AND lose_player=?) OR (win_player=? AND lose_player=?)", [players[i]['name'], players[j]['name'], players[j]['name'], players[i]['name']]).fetchall()
            if len(befo_game) != 0:
                continue
            pairs.append([i, j])
            dicided[i] = 1
            dicided[j] = 1
            break;
        
    no_game_player = -1
    for i in range(0, n):
        if dicided[i] == 0:
            no_game_player = i
            break
    
    con = sqlite3.connect(DATABASE)
    game_data = con.execute("SELECT * FROM game_data").fetchall()
    round = -1
    for row in game_data:
        round = row[0]
    print(round)
    con.execute("DELETE FROM now_matches")
    for pair in pairs:
        player1 = players[pair[0]]['name']
        player2 = players[pair[1]]['name']
        con.execute("INSERT INTO now_matches VALUES(?, ?, ?)", [player1, player2, "PLAYING"])
        print(f'player1: {player1}, player2; {player2}')
    if (no_game_player != -1):
        player1 = players[no_game_player]['name']
        con.execute('INSERT INTO game_result VALUES(?, ?, ?, ?)', [round, player1, "不戦勝", 2])
        con.execute("INSERT INTO now_matches VALUES (?, ?, ?)", [player1, "-", "不戦勝"])
        con.execute('UPDATE results SET win = win + 1 WHERE name = ?', [player1])
        con.execute('UPDATE results SET stone_diff = stone_diff + ? WHERE name = ?', [2, player1])


    con.commit()
    con.execute("DELETE FROM game_data")
    con.execute("INSERT INTO game_data VALUES(?, ?)", [round + 1, n // 2])
    con.commit()
    con.close()
    return redirect(url_for('index'))

@app.route('/game_input', methods=["POST"])
def game_input():
    print(request.form)
    win_name = request.form['winner']
    stone_diff = request.form['stone_diff']
    print(win_name)
    round_int = 10
    lose_name = "?"
    during_game = 10
    con = sqlite3.connect(DATABASE)
    round_data = con.execute('SELECT * FROM game_data').fetchall()
    for row in round_data:
        round_int = row[0]
        during_game = row[1]
    game_data = con.execute('SELECT * FROM now_matches WHERE player1=? OR player2=?', [win_name, win_name]).fetchall()
    print(game_data)
    for row in game_data:
        if row[0]==win_name:
            lose_name=row[1]
        else:
            lose_name=row[0]
    print("lose_name")
    con.execute('INSERT INTO game_result VALUES(?, ?, ?, ?)', [round_int, win_name, lose_name, stone_diff])
    con.execute('UPDATE results SET win = win + 1 WHERE name = ?', [win_name])
    con.execute('UPDATE results SET stone_diff = stone_diff + ? WHERE name = ?', [stone_diff, win_name])
    con.execute('UPDATE results SET lose = lose + 1 WHERE name = ?', [lose_name])
    con.execute('UPDATE results SET stone_diff = stone_diff - ? WHERE name = ?', [stone_diff, lose_name])
    con.execute('DELETE FROM game_data')
    con.execute('INSERT INTO game_data VALUES(?, ?)', [round_int, during_game - 1])
    game_data = con.execute('UPDATE now_matches SET winner=? WHERE player1=? OR player2=?', [win_name, win_name, win_name])
    con.commit()
    con.close()
    return redirect(url_for('index'))

@app.route('/person_result')
def person_result():
    name = request.args.get('name')

    # Game result DBから各人の結果を持ってくる
    con = sqlite3.connect(DATABASE)
    person_result_data = con.execute('SELECT * FROM game_result WHERE (win_player=? OR lose_player=?)', [name, name]).fetchall()
    person_results = []
    print(person_result_data)
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
        
    return render_template(
        'person_result.html',
        person_results=person_results,
        name=name,
        win=total_win,
        lose=total_lose,
        stone_diff=total_stone
    )

@app.route('/reset')
def reset():
    print("a")
    con = sqlite3.connect(DATABASE)
    con.execute('DELETE from players')
    print("c")
    con.execute('DELETE from results')
    con.execute('DELETE from game_data')
    con.execute("INSERT INTO game_data VALUES(?, ?)", [0, 0])
    con.execute("DELETE FROM now_matches")
    con.execute("DELETE FROM game_result")
    con.commit()
    con.close()
    return redirect(url_for('index'))