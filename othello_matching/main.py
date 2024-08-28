from othello_matching import app
from flask import render_template, request, redirect, url_for
from functools import cmp_to_key
import sqlite3
import json
import random
import csv
import pprint
import copy
import time
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
    con = sqlite3.connect(DATABASE)
    db_player = con.execute("SELECT * FROM results").fetchall()
    _game_data = con.execute("SELECT * FROM game_data").fetchall()
    _match_data = con.execute("SELECT * FROM now_matches").fetchall()
    con.close()
    ranks = []
    game_data = []
    now_matches = []
    end_game = 0
    for row in db_player:
        ranks.append({'name': row[0], 'win': row[1], 'lose': row[2], 'stone_diff': row[3], 'status': row[4]})
    ranks = sorted(ranks, key=cmp_to_key(comp))
    for row in _game_data:
        game_data.append({'round': row[0], 'during_game': row[1]})
    for row in _match_data:
        now_matches.append({'player1': row[0], 'player2': row[1], 'winner': row[2]})
        if row[2] != "PLAYING":
            end_game += 1
    return render_template(
        'index.html',
        ranks=ranks,
        game_data=game_data,
        now_matches=now_matches,
        end_game=end_game
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
        player2=player2,
        prev_data={'winner': 'NULL'}
    )

@app.route('/fix_game')
def fix_game():
    player1 = request.args.get('player1')
    player2 = request.args.get('player2')
    con = sqlite3.connect(DATABASE)
    data = con.execute('SELECT * FROM game_result WHERE (win_player = ? AND lose_player=?) OR (win_player=? AND lose_player=?)', [player1, player2, player2, player1]).fetchall()
    prev_win = data[0][1]
    prev_lose = data[0][2]
    stone_diff = data[0][3]
    con.execute('DELETE FROM game_result WHERE (win_player = ? AND lose_player=?) OR (win_player=? AND lose_player=?)', [player1, player2, player2, player1])
    con.execute('UPDATE results SET win = win - 1 WHERE name = ?', [prev_win])
    con.execute('UPDATE results SET stone_diff = stone_diff - ? WHERE name = ?', [stone_diff, prev_win])
    con.execute('UPDATE results SET lose = lose - 1 WHERE name = ?', [prev_lose])
    con.execute('UPDATE results SET stone_diff = stone_diff + ? WHERE name = ?', [stone_diff, prev_lose])
    con.execute('UPDATE game_data SET during_game = during_game + 1')
    con.commit()
    con.close()
    prev_data = {'winner': prev_win, 'loser': prev_lose, 'stone_diff': stone_diff}
    return render_template(
        'game_input.html',
        player1=player1,
        player2=player2,
        prev_data=prev_data
    )

@app.route('/register', methods=['POST'])
def register():
    name = request.form['name']
    short = request.form['short']
    block = request.form['block']
    grade = request.form['grade']
    con = sqlite3.connect(DATABASE)
    con.execute('INSERT INTO players VALUES(?, ?, ?, ?)', [name, short, block, grade])
    con.execute('INSERT INTO results VALUES(?, ?, ?, ?, ?)', [name, 0, 0, 0, "参加"])
    con.commit()
    con.close()
    return redirect(url_for('index'))

def matching_cost(matches, already_battle):
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
def concider_match(players, already_battle):
    matches = [[2 * i + j for j in range(0, 2)] for i in range(0, len(players) // 2)]
    print(already_battle)
    best_cost = matching_cost(matches, already_battle)
    best_matches = copy.deepcopy(matches)
    tabu_span = 10
    tabu_list = [[- tabu_span - 10 for i in range(0, len(players))] for j in range(0, len(players))]
    exe_time = 1000
    start_time = time.time()
    search_cnt = 100000
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
                new_cost = matching_cost(new_match, already_battle)

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
    if len(players) % 2 == 1:
        players.append({'name': "不戦勝", 'win': 0, 'lose': 100, 'stone_diff': -1000})

    players_id = [0 for i in range(0, (len(players)))]
    #ここまでの工夫で遅刻早退対応!!(入力受け取り)

    already_battle = [[0 for i in range(0, len(players_id))] for j in range(0, len(players_id))]
    for i in range(0, len(players)):
        for j in range(0, len(players)):
            if players[i]['name'] == players[j]['name']:
                continue;
            befo_game = con.execute("SELECT * FROM game_result WHERE (win_player=? AND lose_player=?) OR (win_player=? AND lose_player=?)", [players[i]['name'], players[j]['name'], players[j]['name'], players[i]['name']]).fetchall()
            if len(befo_game) != 0:
                already_battle[i][j] = 1
                already_battle[j][i] = 1
    con.close()
    pairs = concider_match(players_id, already_battle)

    #いにしえの嘘貪欲??
    # 未証明: 嘘か本当か知りえない
    #n = len(players)
    #pairs = []
    #dicided = [0] * n
    #for i in range(0, n):
    #    if (dicided[i]):
    #        continue;
    #    for j in range(i + 1, n):
    #        if (dicided[j]):
    #            continue
    #        # すでに当たってたら飛ばす
    #        befo_game = con.execute("SELECT * FROM game_result WHERE (win_player=? AND lose_player=?) OR (win_player=? AND lose_player=?)", [players[i]['name'], players[j]['name'], players[j]['name'], players[i]['name']]).fetchall()
    #        if len(befo_game) != 0:
    #            continue
    #        pairs.append([i, j])
    #        dicided[i] = 1
    #        dicided[j] = 1
    #        break;
    #    
    #no_game_player = -1
    #for i in range(0, n):
    #    if dicided[i] == 0:
    #        no_game_player = i
    #        break
    #
    con = sqlite3.connect(DATABASE)
    game_data = con.execute("SELECT * FROM game_data").fetchall()
    round = -1
    for row in game_data:
        round = row[0]
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

@app.route('/hand_matching')
def hand_matching():
    now_matches = []
    players = []
    con = sqlite3.connect(DATABASE)
    _match_data = con.execute("SELECT * FROM now_matches").fetchall()
    _players = con.execute("SELECT * FROM players").fetchall()
    for row in _match_data:
        now_matches.append({'player1': row[0], 'player2': row[1], 'winner': row[2]})
    for row in _players:
        players.append({'name': row[0]})
    con.close()

    return render_template(
        'hand_matching.html',
        now_matches=now_matches,
        players = players
    )

@app.route('/swap_match', methods=["POST"])
def swap_match():
    print(request.form)
    names = ["_", "__"]
    oppos = ["_", "__"]
    names[0] = request.form['name1']
    names[1] = request.form['name2']
    if names[0] != names[1]:
        con = sqlite3.connect(DATABASE)
        for i in range(0, 2):
            mch = con.execute("SELECT * FROM now_matches WHERE player1 = ? OR player2 = ?", [names[i], names[i]]).fetchall()
            oppos[i] = mch[0][0] if mch[0][0] != names[i] else mch[0][1]
        print(oppos)
        for i in range(0, 2):
            con.execute("DELETE FROM now_matches WHERE (player1 = ? AND player2 = ?) OR (player1 = ? AND player2 = ?)", [names[i], oppos[i], oppos[i], names[i]])
    
        con.execute("INSERT INTO now_matches VALUES(?, ?, ?)", [names[0], names[1], "PLAYING"])
        con.execute("INSERT INTO now_matches VALUES(?, ?, ?)", [oppos[0], oppos[1], "PLAYING"])
    
        con.commit()
        con.close()

    return redirect(url_for('index'))

@app.route('/change_status')
def change_status():
    name = request.args.get('name')
    con = sqlite3.connect(DATABASE)
    player = con.execute('SELECT * FROM results WHERE name=?', [name]).fetchall()
    status = player[0][4]
    con.close()
    return render_template(
        'change_status.html',
        name=name,
        status = status
    )

@app.route('/change_status_exe', methods=["POST"])
def change_status_exe():
    name = request.form['name']
    status = request.form['status']
    con = sqlite3.connect(DATABASE)
    con.execute('UPDATE results SET status = ? WHERE name = ?', [status, name])
    con.commit()
    con.close()
    return redirect(url_for('index'))


@app.route('/game_input', methods=["POST"])
def game_input():
    print(request.form)
    win_name = request.form['winner']
    stone_diff = request.form['stone_diff']
    round_int = 10
    lose_name = "?"
    during_game = 10
    con = sqlite3.connect(DATABASE)
    round_data = con.execute('SELECT * FROM game_data').fetchall()
    for row in round_data:
        round_int = row[0]
        during_game = row[1]
    game_data = con.execute('SELECT * FROM now_matches WHERE player1=? OR player2=?', [win_name, win_name]).fetchall()
    for row in game_data:
        if row[0]==win_name:
            lose_name=row[1]
        else:
            lose_name=row[0]
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

@app.route('/reset_conf')
def reset_conf():
    return render_template('reset_conf.html')

@app.route('/reset')
def reset():
    con = sqlite3.connect(DATABASE)
    con.execute('DELETE from players')
    con.execute('DELETE from results')
    con.execute('DELETE from game_data')
    con.execute("INSERT INTO game_data VALUES(?, ?)", [0, 0])
    con.execute("DELETE FROM now_matches")
    con.execute("DELETE FROM game_result")
    con.commit()
    con.close()
    return redirect(url_for('index'))

@app.route('/outcsv')
def outcsv():
    datas = []
    players = []
    con = sqlite3.connect(DATABASE)
    ranks_data = con.execute('SELECT * FROM results').fetchall()
    for row in ranks_data:
        players.append({'name': row[0], 'win': row[1], 'lose': row[2], 'stone_diff': row[3]})
    
    players = sorted(players, key=cmp_to_key(comp))

    for player in players:
        name = player['name']
        player_info = con.execute('SELECT * FROM players WHERE name=?', [name]).fetchall()
        result_info = con.execute('SELECT * FROM results WHERE name=?', [name]).fetchall()
        battle_info = con.execute('SELECT * FROM game_result WHERE win_player=? OR lose_player=?', [name, name]).fetchall()
        battle = []
        for row in battle_info:
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
                tmp['stone_diff'] *= -1;
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
            print(prev_stone)
            write_row1 = [str(rank) + ".", data['name'], data['short']]
            write_row2 = ['', data['block'], data['grade']]
            stone_tot = 0
            for row in data['battle']:
                stone_num = 32 + row['stone_diff'] // 2
                stone_tot += stone_num
                write_row1.append(row['result'] + str(stone_num))
                write_row2.append(row['opponent'])

            write_row1.append(str(data['win']) + "勝" + str(data['lose']) +  "敗")
            write_row2.append(str(stone_tot))
            writer.writerow(write_row1)
            writer.writerow(write_row2)
    return redirect(url_for('index'))