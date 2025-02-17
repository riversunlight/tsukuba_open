from othello_matching import app
from flask import render_template, request, redirect, url_for
from .game_manager import GameManager

gm = GameManager()

#トップページ
@app.route('/')
def index():
    players, ranks, game_data, now_matches, end_game, no_matches = gm.data_for_index()

    return render_template(
        'index.html',
        players=players,
        ranks=ranks,
        game_data=game_data,
        now_matches=now_matches,
        end_game=end_game,
        no_matches = no_matches
    )

@app.route('/add_player')
def add_player():
    return render_template(
        'add_player.html'
    )

@app.route('/delete_player')
def delete_player():
    name = request.args.get('name')
    gm.delete_player(name)
    return redirect(url_for('index'))

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
    
    if player1 == '-' or player2 == '-':
        player = player1 if player2 == '-' else player2
        win_lose, prev_stone = gm.game_data_no_battle(player1, player2)
        
        return render_template(
            'fix_no_game.html',
            player=player,
            win_lose = win_lose,
            prev_stone = prev_stone
        )
    else:
        round, prev_data = gm.get_game_result(player1, player2)
        print(prev_data)
        return render_template(
            'game_input.html',
            player1=player1,
            player2=player2,
            prev_data=prev_data
        )

@app.route('/fix_no_game', methods=['POST'])
def fix_no_game():
    player = request.form['player']
    kind = request.form['kind']
    stone_diff = request.form['stone_diff']
    gm.fix_no_game(player, kind, stone_diff)

    return redirect(url_for('index'))

@app.route('/register', methods=['POST'])
def register():
    name = request.form['name']
    short = request.form['short']
    block = request.form['block']
    grade = request.form['grade']
    gm.register(name, short, block, grade)
    return redirect(url_for('index'))

@app.route('/matching')
def matching():
    gm.matching()
    return redirect(url_for('index'))

@app.route('/fix_draw')
def fix_draw():
    player1 = request.args.get('player1')
    player2 = request.args.get('player2')

    round, prev_data = gm.get_game_result(player1, player2)
    return render_template(
        'fix_draw.html',
        player1=player1,
        player2=player2,
        prev_data=prev_data,
        round=round
    )
    

@app.route('/fix_prev_game', methods=["POST"])
def fix_prev_game():
    win_name = request.form['winner']
    round = request.form['round']
    stone_diff = request.form['stone_diff']
    gm.fix_prev_game(win_name, round, stone_diff)
    return redirect(url_for('index'))

@app.route('/hand_matching')
def hand_matching():
    now_matches, players = gm.data_for_hand()
    return render_template(
        'hand_matching.html',
        now_matches=now_matches,
        players = players
    )

@app.route('/swap_match', methods=["POST"])
def swap_match():
    names = ["_", "__"]
    names[0] = request.form['name1']
    names[1] = request.form['name2']
    
    now_match = gm.now_match(names)
    if len(now_match) != 0:
        return redirect(url_for('index'))

    if names[0] != names[1]:
        gm.swap_matches(names)

    return redirect(url_for('index'))

@app.route('/change_status')
def change_status():
    name = request.args.get('name')
    status = gm.get_status(name)
    return render_template(
        'change_status.html',
        name=name,
        status = status
    )

@app.route('/change_status_exe', methods=["POST"])
def change_status_exe():
    name = request.form['name']
    status = request.form['status']
    gm.change_status_exe(name, status)
    return redirect(url_for('index'))

@app.route('/delete_match')
def delete_match():
    name1 = request.args.get('name1')
    name2 = request.args.get('name2')
    gm.delete_match(name1, name2)
    return redirect(url_for('index'))

@app.route('/game_input', methods=["POST"])
def game_input():
    print(request.form)
    win_name = request.form['winner']
    stone_diff = request.form['stone_diff']
    gm.game_input(win_name, stone_diff)
    return redirect(url_for('index'))

@app.route('/person_result')
def person_result():
    name = request.args.get('name')

    person_results, total_win, total_lose, total_stone = gm.person_result(name)
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
    gm.reset_database()
    return redirect(url_for('index'))

@app.route('/outcsv')
def outcsv():
    gm.outcsv()
    return redirect(url_for('index'))