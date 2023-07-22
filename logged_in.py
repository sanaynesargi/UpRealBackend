
def logged_in(cookies):
    token = cookies.get("login_token")

    if not token:
        return False

    return token
