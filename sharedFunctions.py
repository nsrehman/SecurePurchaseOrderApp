from Crypto.Cipher import PKCS1_OAEP
from Crypto.PublicKey import RSA


def getCertificate(connectionToCertificateAuthority, publicKey, ID):
    connectionToCertificateAuthority.send(ID + b'||' + publicKey.export_key("PEM"))
    return connectionToCertificateAuthority.recv(2000)


def distributeKeys(certificate, connections, certificateList=None):
    if certificateList is None:
        certificateList = []
    for connection in connections:
        connection.send(certificate)
        signature, ID, publicKeyPem = connection.recv(2000).split(b'||')
        certificateList.append((signature, ID, RSA.import_key(publicKeyPem)))
    return certificateList


def RSAencrypt(msg, key):
    cipher = PKCS1_OAEP.new(key)
    if type(msg) is bytes:
        plaintext = msg
    else:
        plaintext = msg.encode()
    ciphertext = cipher.encrypt(plaintext)
    return ciphertext


def RSAdecrypt(ciphertext, key):
    cipher = PKCS1_OAEP.new(key)
    plaintext = cipher.decrypt(ciphertext)
    return plaintext
