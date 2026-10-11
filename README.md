# OAuth 2.0 / OIDC + mTLS Lab

Hands-on lab demonstrating OAuth 2.0 / OIDC flows with Keycloak and mutual
TLS (mTLS) between a CLI client and a Flask API.

## What this project covers

- OAuth 2.0 Authorization Code flow with PKCE (client configuration)
- OIDC access token issuance via Keycloak
- JWT signature validation against Keycloak JWKS (RS256)
- Role-based access control using realm roles
- mTLS between client and API using a self-signed CA

## Architecture

    +-----------+   OAuth 2.0 password grant   +-----------+
    |  Client   | ---------------------------> | Keycloak  |
    |  (CLI)    | <--------------------------- | :8080     |
    +-----------+      access_token (JWT)      +-----------+
         |
         | HTTP + Bearer token
         v
    +------------------+
    |  Flask API       |
    |  :5001           |
    +------------------+

## Prerequisites

- Docker Desktop
- Python 3.11

## Setup

### 1. Start Keycloak

    docker compose up -d

Wait ~30 seconds. Verify:
    http://localhost:8080/admin
    admin / admin

### 2. Start the API

    cd api
    python -m venv venv
    .\venv\Scripts\Activate.ps1
    pip install -r requirements.txt
    python app.py

### 3. Run the client

    cd client
    python client.py alice alice123

Expected:
- GET /me returns alice's claims with role ["user"]
- GET /admin returns 403 forbidden

    python client.py admin admin123

Expected:
- GET /me returns admin claims with role ["admin","user"]
- GET /admin returns 200

## Security controls

| Control | How tested |
|---|---|
| JWT signature (RS256) | Tampered token rejected |
| Token expiry | 5-min lifespan, expired token rejected |
| Wrong issuer | Token from another realm rejected |
| Role check | alice gets 403 on /admin |

## Warning
For training only. Uses self-signed certificates and password grant.
Do not use in production.
