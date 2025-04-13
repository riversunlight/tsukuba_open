from flask import Flask
from flask_cors import CORS
app = Flask(__name__, static_folder='./templates/assets')
CORS(app)
import abello.main

from abello.model.db import *
create_players_table()
create_results_table()
create_new_matches_table()
create_new_game_result_table()
