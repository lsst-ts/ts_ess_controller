import csv
from .base_device import BaseDevice


class CSVDevice(BaseDevice):
    def __init__(self, name, csv_path, sensor, callback_func, log, **kwargs):
        super().__init__(name=name, device_id="CSV", sensor=sensor, callback_func=callback_func, log=log)
        self.csv_path = csv_path

    async def start(self):
        self.log.info(f"Reading CSV from {self.csv_path}")
        try:
            with open(self.csv_path, newline="") as csvfile:
                reader = csv.DictReader(csvfile)
                for row in reader:
                    data = {k: float(v) for k, v in row.items()}
                    self.callback_func(data)
        except Exception as e:
            self.log.error(f"Error reading CSV: {e}")

    async def stop(self):
        pass
