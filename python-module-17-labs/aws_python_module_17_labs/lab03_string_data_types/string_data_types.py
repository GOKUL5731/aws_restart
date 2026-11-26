"""Lab 03: strings, concatenation, input, and formatted output."""


def main() -> None:
    message = "This is a string."
    print(message)
    print(type(message))
    print(f"{message} is of type {type(message).__name__}")

    first = "water"
    second = "fall"
    print("Concatenation:", first + second)

    name = input("What is your name? ").strip()
    favorite_color = input("What is your favorite color? ").strip()
    favorite_animal = input("What is your favorite animal? ").strip()
    print(f"{name}, you like a {favorite_color} {favorite_animal}!")


if __name__ == "__main__":
    main()
