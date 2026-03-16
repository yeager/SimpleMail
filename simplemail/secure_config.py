"""Secure configuration storage.

Saves settings with restricted file permissions (0600).
For sensitive data like passwords, uses libsecret when available.
"""
import json
import os
from pathlib import Path

try:
    import gi
    gi.require_version('Secret', '1')
    from gi.repository import Secret
    HAS_LIBSECRET = True
except (ImportError, ValueError):
    HAS_LIBSECRET = False


def save_config(config_path: str, data: dict):
    """Save config with chmod 600."""
    path = Path(config_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2))
    try:
        path.chmod(0o600)
    except OSError:
        pass


def load_config(config_path: str) -> dict:
    """Load config from file."""
    path = Path(config_path)
    if path.exists():
        try:
            return json.loads(path.read_text())
        except (json.JSONDecodeError, OSError):
            pass
    return {}


def store_secret(app_id: str, key: str, value: str):
    """Store a secret (password/token) securely.
    
    Uses libsecret (GNOME Keyring) if available, falls back to file.
    """
    if HAS_LIBSECRET:
        schema = Secret.Schema.new(
            app_id,
            Secret.SchemaFlags.NONE,
            {"key": Secret.SchemaAttributeType.STRING}
        )
        Secret.password_store_sync(
            schema, {"key": key}, Secret.COLLECTION_DEFAULT,
            f"{app_id}: {key}", value, None
        )
    else:
        # Fallback: save in config with chmod 600
        config_dir = Path(os.path.expanduser(f"~/.config/{app_id}"))
        config_dir.mkdir(parents=True, exist_ok=True)
        secrets_file = config_dir / "secrets.json"
        secrets = {}
        if secrets_file.exists():
            try:
                secrets = json.loads(secrets_file.read_text())
            except (json.JSONDecodeError, OSError):
                pass
        secrets[key] = value
        secrets_file.write_text(json.dumps(secrets, indent=2))
        secrets_file.chmod(0o600)


def get_secret(app_id: str, key: str) -> str:
    """Retrieve a secret."""
    if HAS_LIBSECRET:
        schema = Secret.Schema.new(
            app_id,
            Secret.SchemaFlags.NONE,
            {"key": Secret.SchemaAttributeType.STRING}
        )
        value = Secret.password_lookup_sync(schema, {"key": key}, None)
        if value:
            return value
    
    # Fallback
    secrets_file = Path(os.path.expanduser(f"~/.config/{app_id}/secrets.json"))
    if secrets_file.exists():
        try:
            secrets = json.loads(secrets_file.read_text())
            return secrets.get(key, "")
        except (json.JSONDecodeError, OSError):
            pass
    return ""
