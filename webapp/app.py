from flask import Flask, render_template
from flask_socketio import SocketIO, emit
import TextLabeling
import pandas as pd

initial_dataset = pd.read_csv('./data/initial_dataset.csv')
unlabeled_dataset = pd.read_csv('./data/unlabeled_dataset.csv')
validation_dataset = pd.read_csv('./data/validation_dataset.csv')

# Flask app setup
app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app)

@app.route('/')
def index():
    return TextLabeling.plot_guided_labeling_html(
        initial_dataset,
        unlabeled_dataset,
        validation_dataset)

@socketio.on('get_candidates_comm_api')
def ws_get_candidates_comm_api(msg):
    return TextLabeling.comm_get_candidates(msg)

if __name__ == '__main__':
    socketio.run(app)
