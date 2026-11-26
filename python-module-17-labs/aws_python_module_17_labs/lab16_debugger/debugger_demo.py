"""Lab 16: a small program for practicing VS Code breakpoints and watches."""


def main() -> None:
    name = "John"
    print("Hello " + name + ".")

    age = 40
    print(name + " is " + str(age) + " years old.")

    next_year_age = age + 1
    print(f"Next year, {name} will be {next_year_age}.")


if __name__ == "__main__":
    main()
