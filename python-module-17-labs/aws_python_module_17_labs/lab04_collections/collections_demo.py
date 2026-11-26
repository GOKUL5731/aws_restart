"""Lab 04: lists, tuples, and dictionaries."""


def main() -> None:
    fruits = ["apple", "banana", "cherry"]
    print("List:", fruits)
    for index, fruit in enumerate(fruits):
        print(f"fruits[{index}] = {fruit}")

    fruits[2] = "orange"
    print("Updated list:", fruits)

    fixed_fruits = ("apple", "banana", "pineapple")
    print("Tuple:", fixed_fruits)
    print("First tuple item:", fixed_fruits[0])

    favorite_fruit = {
        "Akua": "apple",
        "Saanvi": "banana",
        "Paulo": "pineapple",
    }
    print("Dictionary:", favorite_fruit)
    for person, fruit in favorite_fruit.items():
        print(f"{person}'s favorite fruit is {fruit}")


if __name__ == "__main__":
    main()
