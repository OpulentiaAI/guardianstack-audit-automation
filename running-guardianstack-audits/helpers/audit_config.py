#!/usr/bin/env python3
"""Shared config loader for the GuardianStack audit helpers."""
import json
import os


def _deep_update(base, override):
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(base.get(key), dict):
            _deep_update(base[key], value)
        else:
            base[key] = value
    return base


DEFAULTS = {
    "origin": "https://platform.opulentia.ai",
    "signup_path": "/auth?mode=signup",
    "signin_path": "/auth?mode=signin",
    "auth_header": "better-auth-cookie",
    "storage_prefix": "better-auth",
    "selectors": {
        "signup": {
            "name": "input#name",
            "email": "input#email",
            "password": "input#password",
            "submit": "button[type=submit]",
        },
        "signin": {
            "email": "input#email",
            "password": "input#password",
            "submit": "button[type=submit]",
        },
    },
    "endpoints": {
        "signup": "/api/auth/sign-up/email",
        "signin": "/api/auth/sign-in/email",
        "session": "/api/auth/get-session",
        "secondary_token": "/api/auth/convex/token",
        "signout": "/api/auth/sign-out",
    },
    "token_keys": {
        "session": "__Secure-better-auth.session_token",
        "secondary": "__Secure-better-auth.convex_jwt",
    },
}


def load_config(path=None):
    """Load the audit target config, applying env overrides.

    Precedence: AUDIT_CONFIG file > env vars > built-in defaults.
    """
    config = json.loads(json.dumps(DEFAULTS))

    path = path or os.environ.get("AUDIT_CONFIG")
    if path and os.path.exists(path):
        with open(path) as f:
            _deep_update(config, json.load(f))

    # Env overrides for the most common targets.
    if os.environ.get("AUDIT_ORIGIN"):
        config["origin"] = os.environ["AUDIT_ORIGIN"].rstrip("/")
    if os.environ.get("SIGNUP_PATH"):
        config["signup_path"] = os.environ["SIGNUP_PATH"]
    if os.environ.get("SIGNIN_PATH"):
        config["signin_path"] = os.environ["SIGNIN_PATH"]
    if os.environ.get("AUTH_HEADER"):
        config["auth_header"] = os.environ["AUTH_HEADER"]
    if os.environ.get("STORAGE_PREFIX"):
        config["storage_prefix"] = os.environ["STORAGE_PREFIX"]

    return config
