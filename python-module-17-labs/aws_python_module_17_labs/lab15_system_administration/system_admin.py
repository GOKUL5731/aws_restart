"""Lab 15: run a few fixed system commands from Python.

The examples use argument lists and shell=False with subprocess.run().
Only fixed, read-only diagnostic commands are included.
"""

import os
import platform
import subprocess


def list_directory_with_os_system() -> None:
    # The command is selected from a fixed allow-list based on the operating system.
    command = "dir" if os.name == "nt" else "ls"
    print(f"Directory listing using os.system({command!r}):")
    os.system(command)


def run_command(arguments: list[str]) -> None:
    print("$", " ".join(arguments))
    try:
        subprocess.run(arguments, check=True, text=True)
    except FileNotFoundError:
        print(f"Command not available: {arguments[0]}")
    except subprocess.CalledProcessError as error:
        print(f"Command exited with status {error.returncode}")


def main() -> None:
    list_directory_with_os_system()
    if os.name == "nt":
        run_command(["cmd", "/c", "dir"])
        run_command(["systeminfo"])
    else:
        run_command(["ls"])
        run_command(["ls", "-l"])
        run_command(["uname", "-a"])
        run_command(["ps", "-x"])
        run_command(["df", "-h"])
    print("Operating system:", platform.system())


if __name__ == "__main__":
    main()
