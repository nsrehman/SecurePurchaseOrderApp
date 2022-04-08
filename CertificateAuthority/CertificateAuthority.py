from Crypto.Signature import pkcs1_15  # RSA Encryption
from Crypto.PublicKey import RSA  # RSA Public/Private Key
from Crypto.Hash import SHA256
import socket
import threading


def listen(_socket, key):
    ID, publicKeyPem = _socket.recv(2000).split(b'||')
    # publicKey = RSA.import_key(publicKeyPem)
    Hash = SHA256.new(ID)
    signature = pkcs1_15.new(key).sign(Hash)
    certificate = signature + b'||' + ID + b'||' + publicKeyPem
    _socket.send(certificate)


def main():
    purchaser_port = 60000  # Reserve a port for purchaser.
    purchaser_socket = socket.socket()  # Create a socket object
    purchaser_socket.bind(('127.0.0.1', purchaser_port))  # Bind to the port
    purchaser_socket.listen(5)  # Now wait for client connection.
    purchaser_connection, address = purchaser_socket.accept()
    print("Connection Established with Purchaser\n")

    supervisor_port = 60001  # Reserve a port for supervisor.
    supervisor_socket = socket.socket()  # Create a socket object
    supervisor_socket.bind(('127.0.0.1', supervisor_port))  # Bind to the port
    supervisor_socket.listen(5)  # Now wait for client connection.
    supervisor_connection, address = supervisor_socket.accept()
    print("Connection Established with Supervisor\n")

    ordersDepartment_port = 60002  # Reserve a port for the purchasing department.
    ordersDepartment_socket = socket.socket()  # Create a socket object
    ordersDepartment_socket.bind(('127.0.0.1', ordersDepartment_port))  # Bind to the port
    ordersDepartment_socket.listen(5)
    ordersDepartment_connection, address = ordersDepartment_socket.accept()  # Now wait for client connection.
    print("Connection Established with Purchasing Department\n")

    certificateAuthorityPrivateKey = RSA.import_key(open('CA_privateKey.pem').read())

    t1 = threading.Thread(target=listen, args=(purchaser_connection, certificateAuthorityPrivateKey))
    t2 = threading.Thread(target=listen, args=(supervisor_connection, certificateAuthorityPrivateKey))
    t3 = threading.Thread(target=listen, args=(ordersDepartment_connection, certificateAuthorityPrivateKey))

    t1.start()
    t2.start()
    t3.start()

    t1.join()
    t2.join()
    t3.join()

    purchaser_socket.close()
    supervisor_socket.close()
    ordersDepartment_socket.close()


if __name__ == "__main__":
    main()
