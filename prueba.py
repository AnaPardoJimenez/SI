import user as us

us.create_user("Juan", "Larrondo")
(uid, token) = us.login_user("Juan", "Larrondo")
print(uid, "\n", token)