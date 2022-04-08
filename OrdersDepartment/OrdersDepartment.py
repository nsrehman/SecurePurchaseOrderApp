import socket
import time
from Crypto.PublicKey import RSA
from Crypto.Hash import SHA256
from Crypto.Signature import pkcs1_15

import sharedFunctions
from sharedFunctions import *
from ReceiveEmail import *
import threading


def listenOnSocket(connection, connectionsPublicKey, ordersDepartment_privateKey, destinationFolder):
    while True:
        try:
            ping = connection.recv(100)
            if ping == b'':
                quit()
            time.sleep(3)
            mailSubject = receiveEmail("order.department1@gmail.com", destinationFolder)
            invoiceNumber = mailSubject.split("#")[1][1:]

            #Verify
            with open(destinationFolder + "/ReceivedInvoice#" + invoiceNumber + ".pdf", "rb") as file:
                fileData = file.read()
                fileTime = int(RSAdecrypt(fileData[:256], ordersDepartment_privateKey))
                filePDF = fileData[256:-256]
                fileHash = fileData[-256:]
                curTime = int(time.time())
                h = SHA256.new(filePDF)
                try:
                    pkcs1_15.new(connectionsPublicKey).verify(h, fileHash)
                    if (curTime - fileTime) < 60:
                        if destinationFolder == "ReceivedInvoicesFromPurchaser":
                            print("The signature of the purchaser is valid.")
                        if destinationFolder == "ReceivedInvoicesFromSupervisor":
                            print("The signature of the supervisor is valid.")
                            print("The signature of the purchaser matches that of the supervisor.")
                            encryptedMessage = RSAencrypt("Purchase request was received and approved. Order is being processed", connectionsPublicKey)
                            connection.send(encryptedMessage)
                    else:
                        encryptedMessage = RSAencrypt("The time is not within a reasonable range", connectionsPublicKey)
                        connection.send(encryptedMessage)
                except(ValueError, TypeError):
                    print("The signature is not valid.")
                    encryptedMessage = RSAencrypt("Signature was not valid. Invoice PDF has been tampered with.",
                                                  connectionsPublicKey)
                    connection.send(encryptedMessage)
        except ConnectionResetError:
            connection.close()
            quit()


def main():
    ordersDepartmentID = b'ordersDepartmentID'

    purchaser_port = 60003  # Reserve a port for purchaser.
    purchaser_socket = socket.socket()  # Create a socket object
    purchaser_socket.bind(('127.0.0.1', purchaser_port))  # Bind to the port
    purchaser_socket.listen(5)  # Now wait for client connection.
    purchaser_connection, address = purchaser_socket.accept()
    print("Connection Established with Purchaser\n")

    supervisor_port = 60004  # Reserve a port for supervisor.
    supervisor_socket = socket.socket()  # Create a socket object
    supervisor_socket.bind(('127.0.0.1', supervisor_port))  # Bind to the port
    supervisor_socket.listen(5)
    supervisor_connection, address = supervisor_socket.accept()
    print("Connection Established with Supervisor\n")

    certificateAuthority_socket = socket.socket()  # Create a socket object for the certificate authority.
    certificateAuthority_port = 60002  # Reserve a port for certificate authority.

    certificateAuthority_socket.connect(('127.0.0.1', certificateAuthority_port))
    print("Connected to Certificate Authority\n")

    ordersDepartment_privateKey = RSA.generate(2048)
    ordersDepartment_publicKey = ordersDepartment_privateKey.public_key()

    CA_publicKey = RSA.import_key(open("../CertificateAuthority/CA_publicKey.pem").read())

    certificate = getCertificate(certificateAuthority_socket, ordersDepartment_publicKey, ordersDepartmentID)

    certificateList = distributeKeys(certificate, [purchaser_connection, supervisor_connection])

    for certificate in certificateList:
        h = SHA256.new(certificate[1])
        try:
            pkcs1_15.new(CA_publicKey).verify(h, certificate[0])
            if certificate[1] == b'purchaserID':
                print("The signature is valid, public key of purchaser is legitimate.")
                purchaser_publicKey = certificate[2]
            elif certificate[1] == b'supervisorID':
                print("The signature is valid, public key of supervisor is legitimate.")
                supervisor_publicKey = certificate[2]
        except(ValueError, TypeError):
            print("The signature is not valid.")


    t1 = threading.Thread(target=listenOnSocket, args=(purchaser_connection, purchaser_publicKey, ordersDepartment_privateKey, "ReceivedInvoicesFromPurchaser"))
    t2 = threading.Thread(target=listenOnSocket, args=(supervisor_connection, supervisor_publicKey, ordersDepartment_privateKey, "ReceivedInvoicesFromSupervisor"))

    t1.start()
    t2.start()

    t1.join()
    t2.join()





if __name__ == "__main__":
    main()
