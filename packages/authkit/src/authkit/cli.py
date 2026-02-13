from __future__ import annotations

import argparse
import getpass
import importlib
import sys
from typing import Any, Sequence


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="authkit",
        description="Authkit command line utilities.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    create_superuser = subparsers.add_parser(
        "csu",
        help="Create a superuser in your SQLAlchemy database.",
    )
    create_superuser.add_argument(
        "--dburl",
        help="SQLAlchemy database URL (example: sqlite:///./app.db).",
    )
    create_superuser.add_argument(
        "--model",
        help="Python module path where your User model lives (example: app.models).",
    )
    create_superuser.add_argument(
        "--user",
        help="User model class name (example: User).",
    )
    create_superuser.add_argument(
        "--email",
        help="Superuser email.",
    )
    create_superuser.add_argument(
        "--username",
        help="Superuser username.",
    )
    create_superuser.add_argument(
        "--create-tables",
        action="store_true",
        help="Create model metadata tables before creating the user.",
    )
    create_superuser.add_argument(
        "--echo",
        action="store_true",
        help="Enable SQLAlchemy engine SQL logging.",
    )

    return parser


def _load_user_model(import_path: str) -> type[Any]:
    module_name, separator, class_name = import_path.partition(":")
    if not separator or not module_name or not class_name:
        raise ValueError("Invalid model path format. Use 'module.submodule:ClassName'.")

    module = importlib.import_module(module_name)
    model = getattr(module, class_name, None)
    if model is None:
        raise ValueError(f"Model '{class_name}' was not found in module '{module_name}'.")
    return model


def _read_password() -> str:
    first = getpass.getpass("Password: ")
    second = getpass.getpass("Confirm Password: ")
    if first != second:
        raise ValueError("Passwords do not match.")
    if not first:
        raise ValueError("Password cannot be empty.")
    return first


def _prompt_value(label: str, initial_value: str | None) -> str:
    if initial_value:
        return initial_value
    entered = input(f"{label}: ").strip()
    if not entered:
        raise ValueError(f"{label} cannot be empty.")
    return entered


def _command_create_superuser(args: argparse.Namespace) -> int:
    try:
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker
    except ImportError as exc:
        print(
            "SQLAlchemy is required for this command. Install with: "
            "pip install fastapi-jwt-authkit[sqlalchemy]",
            file=sys.stderr,
        )
        print(str(exc), file=sys.stderr)
        return 1

    try:
        from .ext.sqlalchemy.sa_sync import SQLAlchemySyncUserProtocol
        from .service import AuthService
        from .settings import AuthSettings
    except ImportError as exc:
        print(
            "Missing authkit CLI dependencies. Install with: "
            "pip install fastapi-jwt-authkit[fastapi,sqlalchemy]",
            file=sys.stderr,
        )
        print(str(exc), file=sys.stderr)
        return 1

    try:
        dburl = _prompt_value("DB URL", args.dburl)
        model = _prompt_value("Model", args.model)
        user_class = _prompt_value("User", args.user)
        username = _prompt_value("Username", args.username)
        email = _prompt_value("Email", args.email)
        user_model = _load_user_model(f"{model}:{user_class}")
        password = _read_password()
    except Exception as exc:
        print(f"Invalid input: {exc}", file=sys.stderr)
        return 1

    engine = create_engine(dburl, echo=args.echo)
    session_local = sessionmaker(bind=engine, autocommit=False, autoflush=False)

    if args.create_tables:
        metadata = getattr(user_model, "metadata", None)
        if metadata is None:
            print("Model does not expose SQLAlchemy metadata for --create-tables.", file=sys.stderr)
            return 1
        metadata.create_all(bind=engine)

    session = session_local()
    try:
        repo = SQLAlchemySyncUserProtocol(session=session, user_model=user_model)
        service = AuthService(
            settings=AuthSettings(secret_key="authkit-cli-superuser-bootstrap"),
            repo=repo,
        )
        user = service.create_superuser(
            email=email,
            username=username,
            password=password,
        )
        print(
            "Superuser created successfully: "
            f"id={user.id}, email={user.email}, username={user.username}"
        )
        return 0
    except Exception as exc:
        detail = getattr(exc, "detail", None)
        print(f"Failed to create superuser: {detail or exc}", file=sys.stderr)
        return 1
    finally:
        session.close()


def main(argv: Sequence[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.command == "csu":
        return _command_create_superuser(args)

    parser.print_help()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
