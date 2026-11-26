"""Read insulin molecule information from JSON and calculate rough weight."""

from pathlib import Path
import jsonFileHandler


def main() -> None:
    data_path = Path(__file__).parent / "files" / "insulin.json"
    data = jsonFileHandler.readJsonFile(data_path)
    if not data:
        print("Error. Exiting program.")
        return

    molecules = data["molecules"]
    amino_acid_weights = data["weights"]
    insulin = molecules["bInsulin"] + molecules["aInsulin"]
    reference_weight = float(data["molecularWeightInsulinActual"])

    print("B chain:", molecules["bInsulin"])
    print("A chain:", molecules["aInsulin"])
    print(f"Reference molecular weight: {reference_weight:.2f}")

    counts = {aa: insulin.upper().count(aa) for aa in amino_acid_weights}
    rough_weight = sum(count * float(amino_acid_weights[aa]) for aa, count in counts.items())
    percent_error = abs(rough_weight - reference_weight) / reference_weight * 100
    print(f"Rough molecular weight: {rough_weight:.2f}")
    print(f"Percent error: {percent_error:.2f}%")


if __name__ == "__main__":
    main()
