import os
import pandas as pd
import json
from multi_time_series_connectedness import (
    Volatility,
    RollingConnectedness,
)
from market_price_movement_prediction.movement import Movement
from market_price_movement_prediction.model_trainer import ModelTrainer

with open('model_config.json', 'r') as file:
    data = json.load(file)
train_tickers = data['train_tickers']
market_prices_dir = data['market_prices_dir']
train_dir = data['train_dir']
if not os.path.exists(market_prices_dir):
    os.makedirs(market_prices_dir)
if not os.path.exists(train_dir):
    os.makedirs(train_dir)
volatilities_filename = f"{train_dir}/volatilities.pickle"
roll_conn_filename = f"{train_dir}/roll_conn.pickle"
movement_filename = f"{train_dir}/movement.pickle"
max_lag = 20
# train_from >= volatilities_from + periods_per_volatility
periods_per_volatility = data['periods_per_volatility']
volatilities_from = data['volatilities_from']
volatilities_to = data['volatilities_to']
train_from = data['train_from']
train_to = data['train_to']
predict_ticker = "AUDCAD=X"
past_roll_conn_period = data['past_roll_conn_period']

print("calculating volatilities")
volatility = Volatility(n=2)
volatility.calculate(
    market_prices_dir,
    volatilities_from,
    volatilities_to,
    volatilities_filename,
)

# Should enable choosing the tickers
print("calculate rolling connectedness")
volatilities = pd.read_pickle(volatilities_filename)
roll_conn = RollingConnectedness(
    volatilities.dropna(),
    max_lag,
    periods_per_volatility,
    train_from,
    train_to,
)
roll_conn.calculate(roll_conn_filename)

print("calculate movements")
movement = Movement(
    f"{market_prices_dir}/{predict_ticker}.csv", movement_filename
)
movement.get_movements("value")
movement.store()

print("train LSTM model")
with open(movement_filename, "rb") as f:
    movement = pd.read_pickle(f)
with open(roll_conn_filename, "rb") as f:
    roll_conn = pd.read_pickle(f)
model_trainer = ModelTrainer(movement, roll_conn, past_roll_conn_period, train_tickers, "trained_model.keras")
model_trainer.match()
model_trainer.train()
