#!/usr/bin/env python3
"""Generate a PBKDF2 password hash for STUDIO_PASSWORD_HASH."""
import getpass
import hashlib
import secrets

password = getpass.getpass("New studio password: ")
confirm = getpass.getpass("Confirm password: ")
if len(password) < 14:
    raise SystemExit("Use at least 14 characters.")
if password != confirm:
    raise SystemExit("Passwords do not match.")
salt = secrets.token_bytes(16)
iterations = 600_000
digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, iterations).hex()
print(f"pbkdf2_sha256${iterations}${salt.hex()}${digest}")
