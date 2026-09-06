import argparse
import getpass
import sys

from sqlalchemy import select

from cybersentinel_ai.auth.schemas import UserCreate
from cybersentinel_ai.auth.service import bootstrap_first_admin
from cybersentinel_ai.core.config import get_settings
from cybersentinel_ai.db.database import SessionLocal
from cybersentinel_ai.db.models import User


def sync_existing_admin_identity(database, admin: User, payload: UserCreate) -> bool:
    """Align the one owner account with its configured public identity."""
    conflicting_user = database.scalar(
        select(User)
        .where(
            User.id != admin.id,
            (User.email == payload.email) | (User.username == payload.username),
        )
        .limit(1)
    )
    if conflicting_user is not None:
        raise ValueError("configured administrator identity belongs to another user")

    changed = admin.email != payload.email or admin.username != payload.username
    if payload.full_name is not None and admin.full_name != payload.full_name:
        admin.full_name = payload.full_name
        changed = True
    if not changed:
        return False

    admin.email = payload.email
    admin.username = payload.username
    database.commit()
    database.refresh(admin)
    return True


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Create the first CyberSentinel administrator exactly once.",
    )
    parser.add_argument("--email")
    parser.add_argument("--username")
    parser.add_argument("--full-name")
    parser.add_argument(
        "--from-env",
        action="store_true",
        help="Read the administrator identity from CYBERSENTINEL_BOOTSTRAP_ADMIN_*.",
    )
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
        if args.from_env:
            settings = get_settings()
            if not all(
                (
                    settings.bootstrap_admin_email,
                    settings.bootstrap_admin_username,
                    settings.bootstrap_admin_password,
                )
            ):
                print("Administrator bootstrap is not configured; skipping.")
                return 0
            email = settings.bootstrap_admin_email
            username = settings.bootstrap_admin_username
            password = settings.bootstrap_admin_password.get_secret_value()
        else:
            if not args.email or not args.username:
                raise ValueError("--email and --username are required unless --from-env is used")
            email = args.email
            username = args.username
            password = read_password(args.password_stdin)

        payload = UserCreate(
            email=email,
            username=username,
            password=password,
            full_name=args.full_name,
        )
        with SessionLocal() as database:
            existing_admin = database.scalar(
                select(User).where(User.role == "ADMIN").limit(1)
            )
            if existing_admin is not None:
                if args.from_env and sync_existing_admin_identity(
                    database, existing_admin, payload
                ):
                    print(
                        f"Updated administrator identity to {existing_admin.email} "
                        f"(user id {existing_admin.id})."
                    )
                    return 0
                print(f"Administrator already exists (user id {existing_admin.id}); skipping.")
                return 0
            admin = bootstrap_first_admin(database, payload)
            admin_email = admin.email
            admin_id = admin.id
    except (ValueError, EOFError, AttributeError) as exc:
        print(f"Bootstrap failed: {exc}", file=sys.stderr)
        return 1

    print(f"Created administrator {admin_email} (user id {admin_id}).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
