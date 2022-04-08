import threading

from Crypto.Hash import SHA256
from Crypto.Signature import pkcs1_15

import InvoiceGenerator
import socket
import time
from sharedFunctions import *
from SendEmail import sendEmail

CATALOG = {
    "Big Hammer": 10,
    "VBucks": 18.99,
    "Cowboy Belt Buckle": 169
}


def print_catalog(catalog):
    print("\nCATALOG")
    for key in catalog:
        print(f"Product: {key:<18}  Price: ${catalog[key]:.2f}")


def print_cart(cart):
    print("CART")
    for key in cart:
        print(f"Product: {key:<18}  Quantity: {cart[key][0]:<4}  Unit Price: ${cart[key][1]:>7.2f}"
              f"   Amount: ${cart[key][0] * cart[key][1]:>8.2f}")
    subtotal = getSubtotal(cart)
    print(f"\n{' ' * 57}Subtotal:          ${subtotal:>9.2f}")
    print(f"{' ' * 57}Taxes (13%):       ${subtotal * 0.13:>9.2f}")
    print(f"{' ' * 57}Total:             ${subtotal * 1.13:>9.2f}")


def getSubtotal(cart, subtotal=0):
    for key in cart:
        subtotal += cart[key][0] * cart[key][1]
    return subtotal


def listenOnSocket(socket, purchaser_privateKey):
    while True:
        try:
            msg = socket.recv(1000)
            decryptedMsg = RSAdecrypt(msg, purchaser_privateKey)
            print("FROM Supervisor: ", decryptedMsg.decode())
        except ConnectionAbortedError:
            pass
        except OSError:
            quit()



def main():
    purchaserID = b'purchaserID'

    certificateAuthority_socket = socket.socket()  # Create a socket object for the certificate authority.
    certificateAuthority_port = 60000  # Reserve a port for certificate authority.

    ordersDepartment_socket = socket.socket()  # Create a socket object for purchasing department.
    ordersDepartment_port = 60003  # Reserve a port for purchasing department.

    supervisor_socket = socket.socket()  # Create a socket object for supervisor.
    supervisor_port = 60005  # Reserve a port for supervisor.

    certificateAuthority_socket.connect(('127.0.0.1', certificateAuthority_port))
    print("Connected to Certificate Authority\n")

    ordersDepartment_socket.connect(('127.0.0.1', ordersDepartment_port))
    print("Connected to Purchasing Department\n")

    supervisor_socket.connect(('127.0.0.1', supervisor_port))
    print("Connected to Supervisor\n")

    purchaser_privateKey = RSA.generate(2048)
    purchaser_publicKey = purchaser_privateKey.public_key()

    signer = pkcs1_15.new(purchaser_privateKey)

    CA_publicKey = RSA.import_key(open("../CertificateAuthority/CA_publicKey.pem").read())

    certificate = getCertificate(certificateAuthority_socket, purchaser_publicKey, purchaserID)

    certificateList = distributeKeys(certificate, [ordersDepartment_socket, supervisor_socket])

    for certificate in certificateList:
        h = SHA256.new(certificate[1])
        try:
            pkcs1_15.new(CA_publicKey).verify(h, certificate[0])
            if certificate[1] == b'supervisorID':
                print("The signature is valid, public key of supervisor is legitimate.")
                supervisor_publicKey = certificate[2]
            elif certificate[1] == b'ordersDepartmentID':
                print("The signature is valid, public key of purchasing department is legitimate.")
                ordersDepartment_publicKey = certificate[2]
        except(ValueError, TypeError):
            print("The signature is not valid.")

    cart = {}
    print_catalog(CATALOG)
    print(f"\nAvailable Commands are 'add' 'remove' and 'checkout'")
    print(
        f"Use [Add/Remove] [Quantity] [Product] to add/remove items to/from cart (i.e. add 1 apple or remove 1 banana)")
    print(f"Type 'View Cart' to show current cart")
    print(f"Type 'Checkout' to finalize order")
    print(f"Type 'Quit' to exit the application\n")

    t1 = threading.Thread(target=listenOnSocket, args=(supervisor_socket, purchaser_privateKey))

    t1.start()


    while True:
        inputText = input()
        input_split = inputText.split(" ")
        if (len(input_split) > 2) and input_split[1].isnumeric():
            command = input_split[0].lower()
            quantity = int(input_split[1])
            product = inputText[len(command) + len(str(quantity)) + 2:]
            if command == "add":
                if product in CATALOG:
                    if product in cart:
                        cart[product][0] += quantity
                    else:
                        cart[product] = [quantity, CATALOG[product]]
                else:
                    print("Item not in catalog")
            elif command == "remove":
                if product in cart:
                    if cart[product][0] > quantity:
                        cart[product][0] -= quantity
                    else:
                        cart.pop(product)
                else:
                    print("Item not in cart")
        elif inputText.lower() == "view cart":
            print_cart(cart)
        elif inputText.lower() == "checkout":
            invoiceNumber = InvoiceGenerator.createPDF(cart, getSubtotal(cart))
            print("Created PDF")
            # Encrypt PDF
            with open("PurchaserInvoices/PurchaseInvoice#" + str(invoiceNumber) + ".pdf", "rb") as file:

                pdfFileData = file.read()
                bytesTimestamp = str(int(time.time())).encode()
                encryptedTimestampForSupervisor = RSAencrypt(bytesTimestamp,supervisor_publicKey)
                encryptedTimestampForDepartment = RSAencrypt(bytesTimestamp,ordersDepartment_publicKey)
                digest = SHA256.new(pdfFileData)
                signature = signer.sign(digest)
                signedPackageForSupervisor = encryptedTimestampForSupervisor + pdfFileData + signature
                signedPackageForDepartment = encryptedTimestampForDepartment + pdfFileData + signature
                with open("SignedInvoicesForSupervisor/SignedPurchaseInvoice#" + str(invoiceNumber) + ".pdf", "wb") as signedFile:
                    signedFile.write(signedPackageForSupervisor)
                with open("SignedInvoicesForOrdersDepartment/SignedPurchaseInvoice#" + str(invoiceNumber) + ".pdf", "wb") as signedFile:
                    signedFile.write(signedPackageForDepartment)

            #
            sendEmail("purchaser.employee@gmail.com", "supervisor.employee1@gmail.com", invoiceNumber, "SignedInvoicesForSupervisor")
            supervisor_socket.send(b'dummyMessage')
            sendEmail("purchaser.employee@gmail.com", "order.department1@gmail.com", invoiceNumber, "SignedInvoicesForOrdersDepartment")
            ordersDepartment_socket.send(b'dummyMessage')
            #
        elif inputText.lower() == "quit":
            ordersDepartment_socket.close()
            supervisor_socket.close()
            quit()
        else:
            print("Command not accepted")


if __name__ == "__main__":
    main()
