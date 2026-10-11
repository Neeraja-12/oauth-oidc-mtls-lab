"""
Flask API that validates OAuth 2.0 / OIDC access tokens from Keycloak.
"""

from flask import Flask, request, jsonify
import jwt
import requests
from functools import wraps
import os

app = Flask(__name__)

KEYCLOAK_BASE = os.environ.get("KEYCLOAK_BASE", "http://localhost:8090")
REALM = os.environ.get("REALM", "mtls-lab")
ISSUER = f"{KEYCLOAK_BASE}/realms/{REALM}"
JWKS_URL = f"{ISSUER}/protocol/openid-connect/certs"


def get_jwks():
    r = requests.get(JWKS_URL, timeout=5)
    r.raise_for_status()
    return r.json()


def verify_token(token):
    jwks = get_jwks()
    unverified = jwt.get_unverified_header(token)
    kid = unverified.get("kid")
    key = next((k for k in jwks["keys"] if k["kid"] == kid), None)
    if not key:
        raise jwt.InvalidTokenError("unknown kid")
    public_key = jwt.algorithms.RSAAlgorithm.from_jwk(key)
    return jwt.decode(
        token,
        public_key,
        algorithms=["RS256"],
        issuer=ISSUER,
        options={"verify_aud": False},
    )


def require_token(required_role=None):
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            auth = request.headers.get("Authorization", "")
            if not auth.startswith("Bearer "):
                return jsonify({"error": "missing token"}), 401
            try:
                claims = verify_token(auth.split(" ", 1)[1])
            except Exception as e:
                return jsonify({"error": f"invalid token: {e}"}), 401
            request.claims = claims
            if required_role:
                roles = claims.get("realm_access", {}).get("roles", [])
                if required_role not in roles:
                    return jsonify({"error": "forbidden"}), 403
            return fn(*args, **kwargs)
        return wrapper
    return decorator


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})


@app.route("/me", methods=["GET"])
@require_token()
def me():
    c = request.claims
    return jsonify({
        "sub": c.get("sub"),
        "username": c.get("preferred_username"),
        "roles": c.get("realm_access", {}).get("roles", []),
    })


@app.route("/admin", methods=["GET"])
@require_token(required_role="admin")
def admin():
    return jsonify({"message": "admin access granted"})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=False)
