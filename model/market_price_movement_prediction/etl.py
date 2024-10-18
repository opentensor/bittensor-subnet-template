# Should deal with different timezone issue
import os
import pandas as pd
from pathlib import Path


class ETL:
    def __init__(self, file_dir):
        self.file_dir = Path(file_dir)
        self.csv_files = list(self.file_dir.glob("*.csv"))
        self.names = [file.stem for file in self.csv_files]
        self.dict_data = {
            name: pd.read_csv(file, index_col="time", parse_dates=["time"])
            for name, file in zip(self.names, self.csv_files)
        }
        self.time_span = None

    def check_same_time_column(self):
        time_columns = [df.index for df in self.dict_data.values()]
        union_time_index = time_columns[0]

        for time_column in time_columns[1:]:
            union_time_index = union_time_index.union(time_column)

        for name, df in self.dict_data.items():
            self.dict_data[name] = df.reindex(union_time_index).interpolate(
                method="time"
            )

    def write_back_to_csv(self):
        for name, df in self.dict_data.items():
            file_path = self.file_dir / f"{name}.csv"
            df.to_csv(file_path)
            print(f"Written {name} to {file_path}")

    def process(self):
        self.check_same_time_column()
        self.write_back_to_csv()

    def check_same_time_span(self):
        files = os.listdir(self.file_dir)
        csv_files = [file for file in files if file.endswith('.csv')]
        data = pd.read_csv(os.path.join(self.file_dir, csv_files[0]))
        first_time_sapn = [data.iloc[0]['time'], data.iloc[-1]['time']]
        for csv_file in csv_files:
            data = pd.read_csv(os.path.join(self.file_dir, csv_file))
            if [data.iloc[0]['time'], data.iloc[-1]['time']] != first_time_sapn:
                print(f"Time span of {csv_file} is different from others")
                return False
        print(f"All time spans are the same, {first_time_sapn}")
        return True
