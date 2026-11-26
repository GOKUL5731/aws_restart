"""Lab 11: store insulin chains, print them, and estimate molecular weight."""

# Store the human preproinsulin sequence.
preproInsulin = (
    "malwmrllpllallalwgpdpaaafvnqhlcgshlvealylvcgergffytpktr"
    "reaedlqvgqvelgggpgagslqplalegslqkrgiveqcctsicslyqlenycn"
)

# Store the separate sequence elements.
lsInsulin = "malwmrllpllallalwgpdpaaa"
bInsulin = "fvnqhlcgshlvealylvcgergffytpkt"
aInsulin = "giveqcctsicslyqlenycn"
cInsulin = "rreaedlqvgqvelgggpgagslqplalegslqkr"
insulin = bInsulin + aInsulin

AA_WEIGHTS = {
    "A": 89.09, "C": 121.16, "D": 133.10, "E": 147.13, "F": 165.19,
    "G": 75.07, "H": 155.16, "I": 131.17, "K": 146.19, "L": 131.17,
    "M": 149.21, "N": 132.12, "P": 115.13, "Q": 146.15, "R": 174.20,
    "S": 105.09, "T": 119.12, "V": 117.15, "W": 204.23, "Y": 181.19,
}
ACTUAL_MOLECULAR_WEIGHT = 5807.63


def calculate_rough_weight(sequence: str) -> float:
    counts = {amino_acid: sequence.upper().count(amino_acid) for amino_acid in AA_WEIGHTS}
    return sum(counts[amino_acid] * AA_WEIGHTS[amino_acid] for amino_acid in AA_WEIGHTS)


def main() -> None:
    print("The sequence of human preproinsulin:")
    print(preproInsulin)
    print("Insulin B chain:", bInsulin)
    print("Insulin A chain:", aInsulin)

    rough_weight = calculate_rough_weight(insulin)
    error_percent = abs(rough_weight - ACTUAL_MOLECULAR_WEIGHT) / ACTUAL_MOLECULAR_WEIGHT * 100
    print(f"Rough molecular weight of insulin: {rough_weight:.2f}")
    print(f"Reference molecular weight: {ACTUAL_MOLECULAR_WEIGHT:.2f}")
    print(f"Percentage error: {error_percent:.2f}%")


if __name__ == "__main__":
    main()
