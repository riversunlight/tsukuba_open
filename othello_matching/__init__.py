from flask import Flask
from flask_cors import CORS
app = Flask(__name__, static_folder='./templates/assets')
CORS(app)
import othello_matching.main

from othello_matching import db
db.create_players_table()
db.create_results_table()
db.create_new_matches_table()
db.create_new_game_result_table()
