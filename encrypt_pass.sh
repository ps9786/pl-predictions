#!/bin/bash

read -s -p "Enter password: " PASSWORD
echo

python3 -c "
import bcrypt
import base64
import sys

password = sys.argv[1].encode('utf-8')
hashed = bcrypt.hashpw(password, bcrypt.gensalt())
encoded = base64.b64encode(hashed).decode('utf-8')
print(encoded)
" "$PASSWORD"
