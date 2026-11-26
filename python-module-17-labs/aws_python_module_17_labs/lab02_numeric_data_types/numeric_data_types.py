"""Lab 02: explore integer, float, complex, and Boolean values."""


def describe_value(value: object) -> None:
    print(f"Value: {value!r}")
    print(f"Type:  {type(value).__name__}")
    print("-")


def main() -> None:
    print("Basic arithmetic:")
    print("2 + 2 =", 2 + 2)
    print("4 - 2 =", 4 - 2)
    print("2 * 2 =", 2 * 2)
    print("4 / 2 =", 4 / 2)
    print("\nPython numeric and Boolean types:")

    samples = [42, 3.14, 5j, True, False]
    for sample in samples:
        describe_value(sample)


if __name__ == "__main__":
    main()
