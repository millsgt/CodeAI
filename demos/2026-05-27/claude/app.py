"""Mini Flask app demonstrating the auth module."""

from flask import Flask, g, jsonify, request

from auth.jwt_handler import (
    generate_token,
    hash_password,
    refresh_token,
    validate_token,
    verify_password,
)

app = Flask(__name__)

# In-memory user store for demo purposes
USERS: dict[int, dict] = {}
_next_id = 1


@app.route("/register", methods=["POST"])
def register():
    global _next_id
    data = request.get_json()
    email = data.get("email")
    password = data.get("password")

    if not email or not password:
        return jsonify({"error": "email and password required"}), 400

    for user in USERS.values():
        if user["email"] == email:
            return jsonify({"error": "email already registered"}), 409

    user_id = _next_id
    _next_id += 1
    USERS[user_id] = {
        "id": user_id,
        "email": email,
        "password_hash": hash_password(password),
    }

    return jsonify({"id": user_id, "email": email}), 201


@app.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    email = data.get("email")
    password = data.get("password")

    if not email or not password:
        return jsonify({"error": "email and password required"}), 400

    for user in USERS.values():
        if user["email"] == email:
            if verify_password(password, user["password_hash"]):
                tokens = generate_token(user["id"])
                return jsonify(tokens)
            break

    return jsonify({"error": "invalid credentials"}), 401


@app.route("/refresh", methods=["POST"])
def refresh():
    data = request.get_json()
    token = data.get("refresh_token")

    if not token:
        return jsonify({"error": "refresh_token required"}), 400

    try:
        tokens = refresh_token(token)
        return jsonify(tokens)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception:
        return jsonify({"error": "invalid or expired refresh token"}), 401


@app.route("/protected")
def protected():
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return jsonify({"error": "missing or malformed Authorization header"}), 401

    token = auth_header.split(" ", 1)[1]

    try:
        payload = validate_token(token)
    except Exception:
        return jsonify({"error": "invalid or expired token"}), 401

    if payload.get("type") != "access":
        return jsonify({"error": "not an access token"}), 401

    user = USERS.get(int(payload["sub"]))
    if not user:
        return jsonify({"error": "user not found"}), 404

    return jsonify({"message": f"Hello, {user['email']}!", "user_id": user["id"]})


if __name__ == "__main__":
    app.run(debug=True, port=5001)
