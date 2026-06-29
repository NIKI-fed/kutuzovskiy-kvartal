"""Add or update an agent account.

Usage:
    python scripts/add_agent.py <username> <password> [name]

Example:
    python scripts/add_agent.py ivan secret123 "Иван Иванов"

If the username already exists its password (and name) are updated.
"""
import os
import sys

# Make the project root importable so `agents.db` resolves.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.db import add_agent, connect, init_db  # noqa: E402


def main(argv):
    if len(argv) < 3:
        print(__doc__)
        return 1

    username = argv[1].strip()
    password = argv[2]
    name = argv[3] if len(argv) > 3 else ""

    if not username or not password:
        print("Username and password are required.")
        return 1

    init_db()  # ensure schema + instance folder exist
    db = connect()
    try:
        add_agent(db, username, password, name)
    finally:
        db.close()

    print(f"Saved agent '{username}'.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
