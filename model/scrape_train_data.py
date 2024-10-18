import asyncio
import json
from market_price_movement_prediction.scrape_finance_data_yahoo import scrape_and_save_data
from market_price_movement_prediction.etl import ETL

with open('model_config.json', 'r') as file:
    data = json.load(file)
tickers = data['train_tickers']
train_data_dir = 'model/docs/market_prices/train'
volatilities_filename = "model/docs/volatilities_train.pickle"

# scrape data from training
print("scraping finance data for training")
asyncio.run(scrape_and_save_data(tickers, train_data_dir))

# Process the data
print("modifying data")
etl = ETL(train_data_dir)
etl.process()
etl.check_same_time_span()
