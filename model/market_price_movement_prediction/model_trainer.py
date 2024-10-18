import json
import numpy as np
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense


class ModelTrainer:
    def __init__(self, target, features, steps, feature_tickers, store_model_path):
        self.feature_tickers = feature_tickers
        self.steps = steps
        self.target = target
        self.features = features
        self.store_model_path = store_model_path
        self.match_target_features = None

    def match(self):
        print("matching")
        match_target_features = {}
        start_index = 0
        end_index = self.steps
        while end_index < len(self.features):
            current_features = self.features.iloc[start_index:end_index]
            forecast_at = current_features.iloc[-1]["forecast_at"]
            target_movement = self.target[self.target["Time"] == forecast_at]
            start_index += 1
            end_index += 1
            match_target_features[forecast_at] = [target_movement, current_features]
        self.match_target_features = match_target_features

    def train(self):
        Y_train = []
        X_train = []
        for key, value in self.match_target_features.items():
            modified_feature = (
                value[1]
                .drop(
                    columns=[
                        "forecast_at",
                        "end_at",
                        "start_at",
                        "forecast_at_next_period",
                    ]
                )
                .to_numpy()
            )  # need to find a good way to remove these columns
            Y_train.append(value[0].iat[0, value[0].columns.get_loc("Movement")])
            X_train.append(modified_feature)
        X_train = np.array(X_train)
        Y_train = np.array(Y_train)
        model = Sequential()
        model.add(LSTM(50, input_shape=X_train[0].shape))
        model.add(Dense(1, activation="sigmoid"))
        model.compile(
            optimizer="adam", loss="binary_crossentropy", metrics=["accuracy"]
        )
        model.fit(X_train, Y_train, epochs=10, batch_size=32)

        model_path = self.store_model_path
        model.save(model_path)
