# AWS Restart — Python Introduction Practice (17 Labs)

This repository section contains independent, runnable Python practice implementations for the **17 numbered labs** present in the supplied AWS Introduction to Programming material (`0 1` through `0 17`). It is not a collection of 108 labs; the source file supplied for this task contains 17 numbered lab sections.

## Contents

| Lab | Topic | Main file(s) |
|---:|---|---|
| 01 | Hello World | `lab01_hello_world/hello_world.py` |
| 02 | Numeric data types | `lab02_numeric_data_types/numeric_data_types.py` |
| 03 | String data types | `lab03_string_data_types/string_data_types.py` |
| 04 | Lists, tuples, dictionaries | `lab04_collections/collections_demo.py` |
| 05 | Categorize values | `lab05_categorize_values/categorize_values.py` |
| 06 | Composite data types and CSV | `lab06_composite_data_types/composite_data.py` |
| 07 | Conditionals | `lab07_conditionals/conditionals.py` |
| 08 | Loops | `lab08_loops/while_loop.py`, `for_loop.py` |
| 09 | Git repository workflow | `lab09_git/README.md` |
| 10 | Analyze insulin sequence | `lab10_analyze_insulin/analyze_insulin.py` |
| 11 | Insulin sequence and molecular weight | `lab11_insulin_weight/insulin_weight.py` |
| 12 | Lists, loops, and net charge | `lab12_net_charge/net_charge.py` |
| 13 | Functions and Caesar cipher | `lab13_caesar_cipher/caesar_cipher.py` |
| 14 | File handlers and JSON | `lab14_json_file_handlers/calc_weight_json.py`, `jsonFileHandler.py`, `files/insulin.json` |
| 15 | System administration | `lab15_system_administration/system_admin.py` |
| 16 | Debugger basics | `lab16_debugger/debugger_demo.py` |
| 17 | Debug Caesar cipher bugs | `lab17_debug_caesar/buggy_versions/`, `fixed_caesar_cipher.py` |

## Run locally (Windows PowerShell or Linux/macOS terminal)

```bash
python --version
python lab01_hello_world/hello_world.py
python lab10_analyze_insulin/analyze_insulin.py
python lab13_caesar_cipher/caesar_cipher.py
python lab14_json_file_handlers/calc_weight_json.py
```

Use Python 3.10 or newer. Most scripts use only the Python standard library. No AWS credentials or paid AWS resources are required to run these Python exercises locally.

## Run an exercise

From the repository root, run a script using its relative path. For example:

```bash
python lab06_composite_data_types/composite_data.py
python lab12_net_charge/net_charge.py
```

The interactive exercises will prompt for input. The CSV and JSON labs read sample data stored in their own lab folders.

## Git workflow (Lab 09)

See [`lab09_git/README.md`](lab09_git/README.md) for the basic Git commands used to initialize, commit, connect, and push a practice repository.

## Notes

- These are independently written study implementations based on the topics and objectives in the uploaded lab material. They are not an official AWS solution pack and this repository is not affiliated with AWS.
- The supplied lab document lists 17 numbered sections. Additional labs beyond those sections are not included because their source instructions/code were not supplied.
- The insulin sample is included only to demonstrate string processing and molecular-weight calculations in a programming exercise; it is not medical guidance.
- Avoid committing AWS access keys, secret keys, session tokens, passwords, `.env` files, or learner-lab credentials.
