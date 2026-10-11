"""
CLI client that:
1. Gets an access token from Keycloak using password grant.
2. Calls the API with the token.
"""

import os
import sys

import requests

KEYCLOAK = "http://localhost:8090"
REALM = "mtls-lab"
TOKEN_URL = f"{KEYCLOAK}/realms/{REALM}/protocol/openid-connect/token"
API = "http://localhost:5001"


def get_token(user, password):
    data = {
        "grant_type": "password",
        "client_id": "mtls-lab-client",
        "username": user,
        "password": password,
        "scope": "openid",
    }
    r = requests.post(TOKEN_URL, data=data, timeout=10)
    r.raise_for_status()
    return r.json()["access_token"]


def call_api(path, token):
    headers = {"Authorization": f"Bearer {token}"}
    r = requests.get(API + path, headers=headers, timeout=10)
    return r.status_code, r.text


if __name__ == "__main__":
    user = sys.argv[1] if len(sys.argv) > 1 else "alice"
    pw = sys.argv[2] if len(sys.argv) > 2 else "alice123"

    print(f"Logging in as {user}...")
    token = get_token(user, pw)
    print("Token acquired.")
    print()
    print("GET /me...")
    print(call_api("/me", token))
    print()
    print("GET /admin...")
    print(call_api("/admin", token))
