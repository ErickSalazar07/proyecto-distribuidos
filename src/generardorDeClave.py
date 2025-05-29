from cryptography.fernet import Fernet

clave = Fernet.generate_key()
with open("clave.key", "wb") as archivo:
    archivo.write(clave)
