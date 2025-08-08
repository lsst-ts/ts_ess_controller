import csv
from typing import Any
from .base_device import BaseDevice


class CSVDevice(BaseDevice):
    def __init__(
        self,
        name: str,
        csv_path: str,
        sensor: Any,
        callback_func: Any,
        log: Any,
        **kwargs: Any,
    ) -> None:
        super().__init__(
            name=name,
            device_id="CSV",
            sensor=sensor,
            callback_func=callback_func,
            log=log,
        )
        self.csv_path = csv_path

    async def start(self) -> None:
        self.log.info(f"Reading CSV from {self.csv_path}")
        try:
            with open(self.csv_path, newline="") as csvfile:
                reader = csv.DictReader(csvfile)
                for row in reader:
                    data = {k: float(v) for k, v in row.items()}
                    self.callback_func(data)
        except Exception as e:
            self.log.error(f"Error reading CSV: {e}")

    async def stop(self) -> None:
        pass

