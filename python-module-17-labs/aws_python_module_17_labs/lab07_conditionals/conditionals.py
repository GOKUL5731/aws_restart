"""Lab 07: if, elif, and else decisions."""


def main() -> None:
    answer = input("Do you need to ship a package? (yes/no) ").strip().lower()
    if answer == "yes":
        print("We can help you ship that package!")
    elif answer == "no":
        print("Please come back when you need to ship a package. Thank you.")
    else:
        print("Please enter yes or no.")

    service = input("Choose stamps, envelope, or copy: ").strip().lower()
    if service == "stamps":
        print("We have many stamp designs to choose from.")
    elif service == "envelope":
        print("We have many envelope sizes to choose from.")
    elif service == "copy":
        try:
            copies = int(input("How many copies would you like? "))
            if copies < 1:
                raise ValueError
        except ValueError:
            print("Enter a positive whole number of copies.")
        else:
            print(f"Here are {copies} copies.")
    else:
        print("Thank you. Please choose one of the listed services next time.")


if __name__ == "__main__":
    main()
