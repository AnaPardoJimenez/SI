import file, user
import os, uuid
from quart import Quart, jsonify, request

uidtest, token = user.create_user("testuser", "testpassword")
uidtest2, token2 = user.create_user("testuser2", "testpassword2")

file.create_file(uidtest, token, "testfile.txt", "This is a test file.", "private")