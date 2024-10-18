import pandas as pd
import datetime
import pickle


def daterange(date1, date2):
    """
    :param date1: start date
    :param date2: end date
    :return: a list of date
    """
    for n in range(int((date2 - date1).days) + 1):
        yield date1 + datetime.timedelta(n)


def date_format(date):
    list_date = date.split("-")
    year, month, day = list_date[0], list_date[1], list_date[2]
    return datetime.date(int(year), int(month), int(day))


class Movement:

    def __init__(self, file_path, store_path):
        self.file_path = file_path
        self.store_path = store_path
        self.movement_in_value = None
        self.movement_in_label = None

    def calculate_movement_in_value(self, dataframe):
        result = dataframe.apply(
            lambda row: row["Close"] - row["Open"], axis=1
        ).to_frame()
        result.columns = ["Movement"]  # use movement instead
        result["Time"] = dataframe["time"]  # use time instead
        return result

    def calculate_movement_in_label(dataframe):

        # get the rownames
        rownames = dataframe.index
        # print(len(rownames))

        # list to save index
        index_list = []
        for index, row in dataframe.iterrows():

            Open = row["Open"]
            Close = row["Close"]

            if Close > Open:
                movement = 1
            else:
                movement = 0

            # list to save index
            index_list.append(movement)

        # turn the list into dataframe
        result = pd.DataFrame(index_list)
        result.index = rownames
        # print(result)

        # add new column of index to dataframe
        return result

    def get_movements(self, method):
        df = pd.read_csv(self.file_path)

        if method == "value":
            self.movement_in_value = self.calculate_movement_in_value(df)
        elif method == "label":
            self.movement_in_label = self.calculate_movement_in_label(df)
        else:
            print("The method can only be value or label")

    # obtain specify periods of volatility
    def periods_of_movement(self):

        start = date_format("1900-01-01")
        end = date_format(self.end_dt)

        list_date = []

        for dt in daterange(start, end):
            # print(dt)
            list_date.append(dt.strftime("%Y-%m-%d"))
            # print(type(dt.strftime("%Y-%m-%d")))

        # specify date here, create specified Date data
        dataframe_date = pd.DataFrame({"Date": list_date})
        dataframe_date.index = list_date

        # merge all the movements
        dict_movement = self.dict_movement
        result = dataframe_date
        for movement in dict_movement:
            # print(list(movement))
            movement_data = dict_movement[movement]
            movement_data.columns = [movement]
            # print(movement_data)
            result = result.merge(movement_data, left_index=True, right_index=True)
        # result = result.drop(columns=['Date'])

        self.dataframe = result
        # print(result)

    def store(self):
        with open(self.store_path, "wb") as f:
            pickle.dump(self.movement_in_value, f)
