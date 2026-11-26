"""Lab 05: combine different value types in one list."""


def main() -> None:
    mixed_values = [45, 290578, 1.02, True, "My dog is on the bed.", "45"]
    for value in mixed_values:
        print(f"{value!r} is of type {type(value).__name__}")


if __name__ == "__main__":
    main()
