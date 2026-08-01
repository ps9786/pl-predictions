#!/usr/bin/env bash
#
# Set/change the plp.html password. Writes a bcrypt hash to ../password.enc
# (commit + push it to deploy). Uses the htpasswd built into macOS/Apache.
#
# NOTE: password.enc is publicly served by Amplify, so pick a strong
# passphrase — anyone can download the hash and brute-force weak passwords.

set -euo pipefail
cd "$(dirname "$0")/.."

read -rsp "New password: " PW; echo
read -rsp "Confirm password: " PW2; echo
[ "$PW" = "$PW2" ] || { echo "Passwords do not match."; exit 1; }
[ -n "$PW" ] || { echo "Empty password not allowed."; exit 1; }

printf '%s' "$PW" | htpasswd -niBC 12 "" | cut -d: -f2 | tr -d '\n' > password.enc
echo "Wrote password.enc — commit and push it to activate the gate."
