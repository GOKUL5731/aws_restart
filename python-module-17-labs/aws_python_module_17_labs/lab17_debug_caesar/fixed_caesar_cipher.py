"""Correct Caesar cipher used to verify fixes from the four debugging tasks."""

ALPHABET = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"


def transform(message: str, shift: int) -> str:
    output: list[str] = []
    for character in message.upper():
        if character in ALPHABET:
            output.append(ALPHABET[(ALPHABET.index(character) + shift) % 26])
        else:
            output.append(character)
    return "".join(output)


def main() -> None:
    message = input("Please enter a message to encrypt: ")
    while True:
        try:
            key = int(input("Please enter a key (whole number from 1-25): "))
        except ValueError:
            print("The key must be a whole number.")
            continue
        if 1 <= key <= 25:
            break
        print("The key must be between 1 and 25.")

    encrypted = transform(message, key)
    decrypted = transform(encrypted, -key)
    print(f"Encrypted Message: {encrypted}")
    print(f"Decrypted Message: {decrypted}")
    print("Round-trip successful:", decrypted == message.upper())


if __name__ == "__main__":
    main()
