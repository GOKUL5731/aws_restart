"""Lab 12: estimate insulin net charge at pH 0 through pH 14."""

preproInsulin = (
    "malwmrllpllallalwgpdpaaafvnqhlcgshlvealylvcgergffytpktr"
    "reaedlqvgqvelgggpgagslqplalegslqkrgiveqcctsicslyqlenycn"
)
lsInsulin = "malwmrllpllallalwgpdpaaa"
bInsulin = "fvnqhlcgshlvealylvcgergffytpkt"
aInsulin = "giveqcctsicslyqlenycn"
cInsulin = "rreaedlqvgqvelgggpgagslqplalegslqkr"
insulin = bInsulin + aInsulin

PKR = {"y": 10.07, "c": 8.18, "k": 10.53, "h": 6.00, "r": 12.48, "d": 3.65, "e": 4.25}


def calculate_net_charge(ph: float) -> float:
    counts = {amino_acid: float(insulin.upper().count(amino_acid.upper())) for amino_acid in PKR}
    basic = sum(
        counts[aa] * (10 ** PKR[aa]) / ((10 ** ph) + (10 ** PKR[aa]))
        for aa in ("k", "h", "r")
    )
    acidic = sum(
        counts[aa] * (10 ** ph) / ((10 ** ph) + (10 ** PKR[aa]))
        for aa in ("y", "c", "d", "e")
    )
    return basic - acidic


def main() -> None:
    ph = 0
    while ph <= 14:
        print(f"{ph:.2f} {calculate_net_charge(ph):.6f}")
        ph += 1


if __name__ == "__main__":
    main()
