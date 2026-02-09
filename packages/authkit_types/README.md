# Type Stubs for fastapi-jwt-authkit

This directory contains type stub files (`.pyi`) for the `fastapi-jwt-authkit` package, providing type information for IDEs and static type checkers.

## Overview

Type stubs are automatically bundled with the main `fastapi-jwt-authkit` package during the build process. When you install `fastapi-jwt-authkit` from PyPI, the type stubs are included automatically—no separate installation needed.

## Package Information

- **Package Name**: `fastapi-jwt-authkit`
- **Import Name**: `authkit`
- **Python Version**: 3.10+
- **Type Stub Format**: PEP 561 compliant (`.pyi` files + `py.typed` marker)

## Structure

```
packages/authkit_types/src/authkit/
  __init__.pyi          # Package exports
  authenticator.pyi     # Authenticator classes (sync/async)
  extractors.pyi        # Token extraction utilities
  fastapi/
    __init__.pyi        # FastAPI module exports
    routers.pyi         # Router builder functions
  hashing.pyi           # Password hashing functions
  protocols.pyi         # User protocol interfaces
  py.typed              # PEP 561 marker file
  service.pyi           # AuthService classes (sync/async)
  settings.pyi          # AuthSettings configuration
  tokens.pyi            # JWT token creation/decoding
  ext/
    sqlalchmey/         # SQLAlchemy adapters
      __init__.pyi
      sa_async.pyi      # Async SQLAlchemy adapter
      sa_sync.pyi       # Sync SQLAlchemy adapter
```

## Usage

Type stubs are automatically available when you install the package:

```bash
pip install fastapi-jwt-authkit
```

No additional steps required! Your IDE (VS Code, PyCharm, etc.) and type checkers (mypy, pyright, pylance) will automatically detect and use these type stubs.

## Features Covered

The type stubs provide type information for:

- **AuthSettings**: Configuration class with all settings options
- **AuthService / AsyncAuthService**: User management and authentication services
- **SyncAuthenticator / AsyncAuthenticator**: Current user authentication
- **Router Builders**: `build_auth_router_sync` and `build_auth_router_async`
- **Token Utilities**: JWT creation, decoding, and validation
- **Password Hashing**: Secure password hashing and verification
- **SQLAlchemy Adapters**: Protocol implementations for SQLAlchemy
- **Protocols**: `SyncUserProtocol`, `AsyncUserProtocol`, `UserProtocol`
- **Extractors**: Token extraction from headers and cookies
- **BaseUser Model**: Extendable user model mixin

## Type Checking

The package includes a `py.typed` marker file, indicating full PEP 561 compliance. This means:

- Type checkers will automatically discover the type information
- IDEs will provide accurate autocomplete and type hints
- Static analysis tools can verify type correctness

## Example

```python
from authkit import AuthSettings
from authkit.fastapi.routers import build_auth_router_async
from authkit.fastapi.models import BaseUser

# All of these will have full type information:
settings: AuthSettings = AuthSettings(secret_key="secret")
router = build_auth_router_async(
    settings=settings,
    get_session=get_session,
    user_model=User,
)
```

## Development

If you're developing or modifying the type stubs:

1. Edit the `.pyi` files in this directory
2. The stubs are automatically bundled during the build process via `pyproject.toml`:
   ```toml
   [tool.hatch.build.targets.wheel.force-include]
   "packages/authkit_types/src/authkit" = "authkit"
   ```
3. Test your changes by installing the package locally:
   ```bash
   pip install -e .
   ```

## Compatibility

- **PEP 561**: Fully compliant
- **mypy**: Supported
- **pyright/pylance**: Supported
- **PyCharm**: Supported
- **VS Code**: Supported (via Pylance)

## Notes

- Type stubs mirror the structure of the main `authkit` package
- All public APIs are typed
- Internal implementation details are not exposed in type stubs
- The `py.typed` marker file ensures proper type checker discovery

## Related Documentation

For usage examples and API documentation, see the main [README.md](../../README.md) in the project root.

## License

Same as the main package: MIT License (see [LICENSE](LICENSE))
