# Lab 17 — Caesar cipher debugging

Run the four intentionally defective programs in `buggy_versions/` one at a time. Each file has one planned issue:

1. `bug01_key_type.py` — adds a string key to an integer position.
2. `bug02_case_handling.py` — does not normalize lower-case input before searching the uppercase alphabet.
3. `bug03_wrong_decrypt_key.py` — computes a negative key but passes the original key to the encryption function.
4. `bug04_wrong_output_variable.py` — prints the encrypted value again instead of the decrypted value.

The corrected reference implementation is `fixed_caesar_cipher.py`.

```bash
python lab17_debug_caesar/buggy_versions/bug01_key_type.py
python lab17_debug_caesar/fixed_caesar_cipher.py
```
