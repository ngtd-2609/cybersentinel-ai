import argparse
import getpass
import sys

from cybersentinel_ai.auth.schemas import UserCreate
from cybersentinel_ai.auth.service import bootstrap_first_admin
from cybersentinel_ai.db.database import SessionLocal


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Create the first CyberSentinel administrator exactly once.",
    )
    parser.add_argument("--email", required=True)
    parser.add_argument("--username", required=True)
    parser.add_argument("--full-name")
    parser.add_argument(
        "--password-stdin",
        action="store_true",
        help="Read one password line from stdin instead of a hidden prompt.",
    )
    return parser


def read_password(password_stdin: bool) -> str:
    if password_stdin:
        return sys.stdin.readline().rstrip("\r\n")
    return getpass.getpass("Admin password: ")


def main() -> int:
    args = build_parser().parse_args()
    try:
        payload = UserCreate(
            email=args.email,
            username=args.username,
            password=read_password(args.password_stdin),
            full_name=args.full_name,
        )
        with SessionLocal() as database:
            admin = bootstrap_first_admin(database, payload)
            admin_email = admin.email
            admin_id = admin.id
    except (ValueError, EOFError) as exc:
        print(f"Bootstrap failed: {exc}", file=sys.stderr)
        return 1

    print(f"Created administrator {admin_email} (user id {admin_id}).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
