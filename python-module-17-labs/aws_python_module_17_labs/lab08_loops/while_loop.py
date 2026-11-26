"""Lab 08A: repeat until the user guesses the generated number."""

import random


def main() -> None:
    target = random.randint(1, 10)
    print("Welcome to Guess the Number!")
    print("Guess a whole number between 1 and 10.")

    while True:
        raw_guess = input("Your guess: ").strip()
        try:
            guess = int(raw_guess)
        except ValueError:
            print("Please enter a whole number.")
            continue
        if not 1 <= guess <= 10:
            print("Your guess must be between 1 and 10.")
        elif guess == target:
            print(f"You guessed {guess}. That is correct! You win!")
            break
        else:
            print("That is not it. Try again.")


if __name__ == "__main__":
    main()
