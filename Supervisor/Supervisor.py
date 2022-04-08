import socket
import time
import threading
import os

from Crypto.Hash import SHA256
from Crypto.Signature import pkcs1_15
from ReceiveEmail import receiveEmail
from GetJSON import getJSON, printJSON
from SendEmail import sendEmail
from sharedFunctions import *


def getResponse(connectionToDepartment, connectionToPurchaser, invoiceNumber, ordersDepartmentPublicKey, purchaserPublicKey, signer, fileToSign):
    invoiceJSON = getJSON("ReceivedInvoices/ExtractedPDFs/ExtractedPDF#" + invoiceNumber + ".pdf")
    printJSON(invoiceJSON)
    print("An employee is requesting to make the above purchase. Do you accept this purchase? '(Y)es' or '(N)o'")
    while True:
        inputText = input().lower()
        if inputText == "yes" or inputText == "y":
            encryptedTimestamp = RSAencrypt(str(int(time.time())).encode(), ordersDepartmentPublicKey)
            digest = SHA256.new(fileToSign)
            signature = signer.sign(digest)
            signedPackage = encryptedTimestamp + fileToSign + signature
            with open("SignedInvoices/SignedPurchaseInvoice#" + invoiceNumber + ".pdf", "wb") as signedFile:
                signedFile.write(signedPackage)
            sendEmail("supervisor.employee1@gmail.com", "order.department1@gmail.com", invoiceNumber, "SignedInvoices")
            connectionToDepartment.send(b'dummyMessage')
            break
        elif inputText == "no" or inputText == "n":
            encryptedMessage = RSAencrypt("The order was declined by supervisor.", purchaserPublicKey)
            connectionToPurchaser.send(encryptedMessage)
            break
        else:
            print("Invalid entry, please enter again.")



def listenOnSocket(ordersDepartmentsocket, purchaserConnection, supervisor_privateKey, purchaser_publicKey):
    confirmationString = b"Purchase request was received and approved. Order is being processed"
    while True:
        try:
            msg = ordersDepartmentsocket.recv(1000)
            decryptedMsg = RSAdecrypt(msg, supervisor_privateKey)
            print("FROM Orders Department: ", decryptedMsg.decode())
            if decryptedMsg == confirmationString:
                encryptedMessage = RSAencrypt(confirmationString, purchaser_publicKey)
                purchaserConnection.send(encryptedMessage)
        except(ValueError, ConnectionAbortedError):
            ordersDepartmentsocket.close()
            quit()



def main():
    supervisorID = b'supervisorID'

    purchaser_port = 60005  # Reserve a port for purchaser.
    purchaser_socket = socket.socket()  # Create a socket object
    purchaser_socket.bind(('127.0.0.1', purchaser_port))  # Bind to the port
    purchaser_socket.listen(5)  # Now wait for client connection.
    purchaser_connection, address = purchaser_socket.accept()
    print("Connection Established with Purchaser\n")

    certificateAuthority_socket = socket.socket()  # Create a socket object for the certificate authority.
    certificateAuthority_port = 60001  # Reserve a port for certificate authority.

    ordersDepartment_socket = socket.socket()  # Create a socket object for purchasing department.
    ordersDepartment_port = 60004  # Reserve a port for purchasing department.

    certificateAuthority_socket.connect(('127.0.0.1', certificateAuthority_port))
    print("Connected to Certificate Authority\n")

    ordersDepartment_socket.connect(('127.0.0.1', ordersDepartment_port))
    print("Connected to Purchasing Department\n")

    supervisor_privateKey = RSA.generate(2048)
    supervisor_publicKey = supervisor_privateKey.public_key()

    signer = pkcs1_15.new(supervisor_privateKey)

    CA_publicKey = RSA.import_key(open("../CertificateAuthority/CA_publicKey.pem").read())

    certificate = getCertificate(certificateAuthority_socket, supervisor_publicKey, supervisorID)

    certificateList = distributeKeys(certificate, [ordersDepartment_socket, purchaser_connection])

    for certificate in certificateList:
        h = SHA256.new(certificate[1])
        try:
            pkcs1_15.new(CA_publicKey).verify(h, certificate[0])
            if certificate[1] == b'purchaserID':
                print("The signature is valid, public key of purchaser is legitimate.")
                purchaser_publicKey = certificate[2]
            elif certificate[1] == b'ordersDepartmentID':
                print("The signature is valid, public key of purchasing department is legitimate.")
                ordersDepartment_publicKey = certificate[2]
        except(ValueError, TypeError):
            print("The signature is not valid.")

    t1 = threading.Thread(target=listenOnSocket, args=(ordersDepartment_socket, purchaser_connection, supervisor_privateKey, purchaser_publicKey))
    t1.start()


    while True:
        try:
            ping = purchaser_connection.recv(1000)
            time.sleep(3)
            print("Received Purchase Invoice")
            mailSubject = receiveEmail("supervisor.employee1@gmail.com", "ReceivedInvoices")
            invoiceNumber = mailSubject.split("#")[1][1:]

            #Decrypt
            with open("ReceivedInvoices/ReceivedInvoice#" + invoiceNumber + ".pdf", "rb") as file:
                fileData = file.read()
                fileTime = int(RSAdecrypt(fileData[:256], supervisor_privateKey))
                filePDF = fileData[256:-256]
                with open("ReceivedInvoices/ExtractedPDFs/ExtractedPDF#" + invoiceNumber + ".pdf", "wb") as pdfFile:
                    pdfFile.write(filePDF)
                fileHash = fileData[-256:]
                curTime = int(time.time())
                h = SHA256.new(filePDF)
                try:
                    pkcs1_15.new(purchaser_publicKey).verify(h, fileHash)
                    if (curTime - fileTime) < 60:
                        print("The signature is valid, digest from user and supervisor match.")
                        fileToSign = fileData[256:-256]
                        t1 = threading.Thread(target=getResponse, args=(ordersDepartment_socket,
                                                                          purchaser_connection,
                                                                          invoiceNumber,
                                                                          ordersDepartment_publicKey,
                                                                          purchaser_publicKey,
                                                                          signer, fileToSign))
                        t1.daemon = True
                        t1.start()

                    else:
                        print("Timestamps are not within reasonable range.")
                        encryptedMessage = RSAencrypt("The time is not within a reasonable range", purchaser_publicKey)
                        purchaser_connection.send(encryptedMessage)
                        os.remove("ReceivedInvoices/ReceivedInvoice#" + invoiceNumber + ".pdf")
                except(ValueError, TypeError):
                    print("The signature is not valid.")
                    try:
                        os.remove("ReceivedInvoices/ReceivedInvoice#" + invoiceNumber + ".pdf")
                    except PermissionError:
                        pass
        except ConnectionResetError:
            ordersDepartment_socket.close()
            quit()


if __name__ == "__main__":
    main()
