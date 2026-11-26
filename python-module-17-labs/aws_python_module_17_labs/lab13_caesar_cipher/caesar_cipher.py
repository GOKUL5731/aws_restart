"""Lab 13: Caesar cipher implemented with reusable functions."""

ALPHABET = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"


def get_double_alphabet(alphabet: str) -> str:
    return alphabet + alphabet


def get_message() -> str:
    return input("Message to encrypt: ")


def get_cipher_key() -> int:
    while True:
        raw_key = input("Enter a whole-number key from 1 to 25: ").strip()
        try:
            key = int(raw_key)
        except ValueError:
            print("The key must be a whole number.")
            continue
        if 1 <= key <= 25:
            return key
        print("The key must be between 1 and 25.")


def encrypt_message(message: str, cipher_key: int, alphabet: str = ALPHABET) -> str:
    """Shift letters while leaving punctuation, spaces, and digits untouched."""
    result = []
    for character in message.upper():
        if character in alphabet:
            position = alphabet.index(character)
            result.append(alphabet[(position + cipher_key) % len(alphabet)])
        else:
            result.append(character)
    return "".join(result)


def decrypt_message(message: str, cipher_key: int, alphabet: str = ALPHABET) -> str:
    return encrypt_message(message, -cipher_key, alphabet)


def main() -> None:
    print(f"Alphabet: {ALPHABET}")
    print(f"Double alphabet: {get_double_alphabet(ALPHABET)}")
    message = get_message()
    key = get_cipher_key()
    encrypted = encrypt_message(message, key)
    decrypted = decrypt_message(encrypted, key)
    print(f"Encrypted message: {encrypted}")
    print(f"Decrypted message: {decrypted}")


if __name__ == "__main__":
    main()
