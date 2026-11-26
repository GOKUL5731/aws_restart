"""Intentional debugging exercise: Caesar cipher variant 2.

This file contains one deliberate defect. Run it with a test phrase and key,
then compare the result with ../fixed_caesar_cipher.py.
"""

ALPHABET = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"

def encrypt_message(message, key):
    result = ""
    source = message
    for character in source:
        position = (ALPHABET + ALPHABET).find(character)
        new_position = position + int(key)
        if character in ALPHABET + ALPHABET:
            result += (ALPHABET + ALPHABET)[new_position]
        else:
            result += character
    return result

def decrypt_message(message, key):
    decrypt_key = -1 * int(key)
    return encrypt_message(message, decrypt_key)

def main():
    message = input("Message: ")
    key = input("Key (1-25): ")
    encrypted = encrypt_message(message, key)
    print("Encrypted:", encrypted)
    decrypted = decrypt_message(encrypted, key)
    print("Decrypted:", decrypted)

if __name__ == "__main__":
    main()
