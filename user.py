import pandas as pd
import os, uuid

def create_user(username, password):
    """
    Create a new user with the given username, email, and password.
    
    Args:
        username (str): The username of the new user.
        email (str): The email address of the new user.
        password (str): The password for the new user.

    Returns:
        str: The token for the newly created user.
        
    """
    # Comprobar si el usuario ya existe (preguntar si mejor excepcion)
    if(get_user_id(username) is not False):
        return login_user(username, password)
    
    df = open_or_create_txt()

    uid = uuid.uuid4()

    df.loc[len(df)] = [username, password, uid]

    Secret_uuid = uuid.UUID('00010203-0405-0607-0809-0a0b0c0d0e0f') # Preguntar el martes con que generarlo 

    return uid, uuid.uuid5(Secret_uuid, uid)

def login_user(username, password):
    """
    Log in a user with the given username and password.
    
    Args:
        username (str): The username of the user.
        password (str): The password of the user.
        
    Returns:
        bool: UID and token if login is successful, None otherwise.
    """

    df = open_or_create_txt()

    usuario = df[(df["username"] == username) & (df["password"] == password)]

    if not usuario.empty:
        uid = usuario.iloc[0]["UID"]
        Secret_uuid = uuid.UUID('00010203-0405-0607-0809-0a0b0c0d0e0f') 
        return uid, uuid.uuid5(Secret_uuid, uid)
    
    return None

def get_user_id(username):
    """
    Retrieve the user ID for the given username.
    
    Args:
        username (str): The username of the user.

    Returns:
        bool: True if user exists, False otherwise.
    """

    df = open_or_create_txt()

    usuario = df[df["username"] == username]

    if not usuario.empty:
        return True
    else:
        return False

def open_or_create_txt():
    # Si el archivo existe, lo abre; si no, lo crea vacío
    if os.path.exists("users.txt"):
        df = pd.read_csv("users.txt", sep="\t")
    else:
        df = pd.DataFrame(columns=["username", "password", "UID"])
        df.to_csv("users.txt", sep="\t", index=False)
    return df
