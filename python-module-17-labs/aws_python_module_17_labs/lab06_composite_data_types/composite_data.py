"""Lab 06: load CSV rows into a list of dictionaries."""

from __future__ import annotations
import csv
from copy import deepcopy
from pathlib import Path

TEMPLATE = {
    "vin": "<empty>",
    "make": "<empty>",
    "model": "<empty>",
    "year": 0,
    "range": 0,
    "topSpeed": 0,
    "zeroSixty": 0.0,
    "mileage": 0,
}


def load_inventory(csv_path: Path) -> list[dict[str, object]]:
    inventory: list[dict[str, object]] = []
    with csv_path.open(newline="", encoding="utf-8") as csv_file:
        reader = csv.DictReader(csv_file)
        for row in reader:
            vehicle = deepcopy(TEMPLATE)
            vehicle["vin"] = row["vin"].strip()
            vehicle["make"] = row["make"].strip()
            vehicle["model"] = row["model"].strip()
            vehicle["year"] = int(row["year"])
            vehicle["range"] = int(row["range"])
            vehicle["topSpeed"] = int(row["topSpeed"])
            vehicle["zeroSixty"] = float(row["zeroSixty"])
            vehicle["mileage"] = int(row["mileage"])
            inventory.append(vehicle)
    return inventory


def main() -> None:
    data_file = Path(__file__).with_name("car_fleet.csv")
    inventory = load_inventory(data_file)
    print(f"Loaded {len(inventory)} vehicles")
    for vehicle in inventory:
        for key, value in vehicle.items():
            print(f"{key}: {value}")
        print("-----")


if __name__ == "__main__":
    main()
