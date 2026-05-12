"""
CLI tool for managing AVM AI Agent users.

Usage:
  python manage_users.py add <username> <password> <role> <group>
  python manage_users.py remove <username>
  python manage_users.py list

Roles:  executive | manager | analyst
Groups: dpd_taiwan | nccu_students

Examples:
  python manage_users.py add allum secret123 executive dpd_taiwan
  python manage_users.py add chen_wei nccu2026 analyst nccu_students
  python manage_users.py list
  python manage_users.py remove allum
"""

import sys
from src.auth.users import add_user, remove_user, list_users

VALID_ROLES = {"executive", "manager", "analyst"}
VALID_GROUPS = {"dpd_taiwan", "nccu_students"}


def cmd_add(args: list[str]) -> None:
    if len(args) != 4:
        print("Usage: python manage_users.py add <username> <password> <role> <group>")
        sys.exit(1)
    username, password, role, group = args
    if role not in VALID_ROLES:
        print(f"Invalid role '{role}'. Choose from: {', '.join(sorted(VALID_ROLES))}")
        sys.exit(1)
    if group not in VALID_GROUPS:
        print(f"Invalid group '{group}'. Choose from: {', '.join(sorted(VALID_GROUPS))}")
        sys.exit(1)
    add_user(username, password, role, group)
    print(f"User '{username}' added (role={role}, group={group}).")


def cmd_remove(args: list[str]) -> None:
    if len(args) != 1:
        print("Usage: python manage_users.py remove <username>")
        sys.exit(1)
    username = args[0]
    if remove_user(username):
        print(f"User '{username}' removed.")
    else:
        print(f"User '{username}' not found.")
        sys.exit(1)


def cmd_list() -> None:
    users = list_users()
    if not users:
        print("No users configured. Use 'python manage_users.py add ...' to create one.")
        return
    print(f"{'Username':<20} {'Role':<12} {'Group'}")
    print("-" * 50)
    for u in users:
        print(f"{u['username']:<20} {u['role']:<12} {u['group']}")


def main() -> None:
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    command = sys.argv[1]
    args = sys.argv[2:]

    if command == "add":
        cmd_add(args)
    elif command == "remove":
        cmd_remove(args)
    elif command == "list":
        cmd_list()
    else:
        print(f"Unknown command '{command}'. Use: add | remove | list")
        sys.exit(1)


if __name__ == "__main__":
    main()
