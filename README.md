# OAuth 2.0 / OIDC + mTLS Lab

Hands-on lab demonstrating OAuth 2.0 / OIDC flows with Keycloak and mutual
TLS (mTLS) between a CLI client and a Flask API, using nginx as the mTLS
terminator.

## What this project covers

- OAuth 2.0 password grant with Keycloak
- OIDC access token issuance
- JWT signature validation against Keycloak JWKS (RS256)
- Role-based access control using realm roles
- Real mTLS enforcement with nginx (self-signed CA + client certificates)

## Architecture

    +-----------+   OAuth 2.0 password grant   +-----------+
    |  Client   | ---------------------------> | Keycloak  |
    |  (CLI)    | <--------------------------- | :8090     |
    +-----------+      access_token (JWT)      +-----------+
         |
         | HTTPS + client certificate (mTLS)
         v
    +-------------------+
    | nginx :5443       |
    | (TLS + mTLS)      |
    +-------------------+
         |
         | HTTP
         v
    +-------------------+
    | Flask API :5001   |
    +-------------------+

## Prerequisites

- Docker Desktop (Linux containers mode)
- Python 3.11
- WSL Ubuntu (for cert generation and testing)
- OpenSSL (in WSL)

## Setup

### 1. Generate certificates (one time)

    wsl -d Ubuntu
    cd /mnt/c/Users/neeraja/oauth-oidc-mtls-lab/certs
    echo "subjectAltName=DNS:localhost,IP:127.0.0.1" > san.cnf
    openssl genrsa -out ca.key 4096
    openssl req -x509 -new -nodes -key ca.key -sha256 -days 3650 -subj "/CN=mtls-lab-ca" -out ca.crt
    openssl genrsa -out server.key 2048
    openssl req -new -key server.key -subj "/CN=localhost" -out server.csr
    openssl x509 -req -in server.csr -CA ca.crt -CAkey ca.key -CAcreateserial -out server.crt -days 825 -sha256 -extfile san.cnf
    openssl genrsa -out client.key 2048
    openssl req -new -key client.key -subj "/CN=alice-client" -out client.csr
    openssl x509 -req -in client.csr -CA ca.crt -CAkey ca.key -CAcreateserial -out client.crt -days 825 -sha256
    exit

### 2. Start the Flask API

    cd api
    python -m venv venv
    .\venv\Scripts\Activate.ps1
    pip install -r requirements.txt
    python app.py

### 3. Start Keycloak and nginx

    docker compose up -d
    docker compose ps

Wait ~45 seconds. Keycloak at http://localhost:8090, nginx at https://localhost:5443.

### 4. Test mTLS (from WSL — Windows schannel cannot handle PEM client certs)

    wsl -d Ubuntu
    cd /mnt/c/Users/neeraja/oauth-oidc-mtls-lab
    TOKEN=$(curl -s -X POST http://localhost:8090/realms/mtls-lab/protocol/openid-connect/token \
      -d "grant_type=password" \
      -d "client_id=mtls-lab-client" \
      -d "username=alice" -d "password=alice123" -d "scope=openid" \
      | grep -o '"access_token":"[^"]*"' | cut -d'"' -f4)

    # WITH client cert (should succeed)
    curl -k --cert certs/client.crt --key certs/client.key \
      --cacert certs/ca.crt https://localhost:5443/me \
      -H "Authorization: Bearer $TOKEN"

    # WITHOUT client cert (should fail with 400)
    curl -k --cacert certs/ca.crt https://localhost:5443/me \
      -H "Authorization: Bearer $TOKEN"

## Security controls tested

| Control | How tested |
|---|---|
| JWT signature (RS256) | Tampered token rejected |
| Token expiry | 5-min lifespan, expired token rejected |
| Wrong issuer | Token from another realm rejected |
| Role check | alice gets 403 on `/admin`, admin gets 200 |
| mTLS enforcement | Request without client cert returns 400 |
| CA validation | Only certs signed by local CA accepted |

## Notes

- Windows `curl.exe` uses Schannel, which cannot load PEM client certificates.
  Run mTLS tests from WSL (`curl` there uses OpenSSL).
- Certificates are gitignored. Run the generation script before first use.
- This is a training lab. Password grant and self-signed certs are not for production.