### SET UP EMAILS
import smtplib
import ssl
from email.message import EmailMessage
import mimetypes
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from os.path import basename

def sendEmail(sendAdress, recieveAddress, invoiceNumber, directory):
    smtp_host = 'smtp.gmail.com'
    smtp_tls_port = 587

    username = sendAdress
    password = 'coe8172022'

    from_addr = sendAdress
    to_addrs = [recieveAddress]

    message = EmailMessage()
    message['subject'] = 'Order Invoice# ' + str(invoiceNumber)
    message['from'] = from_addr
    message['to'] = ', '.join(to_addrs)

    ctype, encoding = mimetypes.guess_type(directory+"/SignedPurchaseInvoice#"+str(invoiceNumber)+".pdf")
    maintype, subtype = ctype.split('/', 1)
    with open(directory+"/SignedPurchaseInvoice#"+str(invoiceNumber)+".pdf", 'rb') as file:
        PDFdata = file.read()
        message.add_attachment(PDFdata, maintype=maintype,
                       subtype=subtype, filename="Purchase Invoice")
    context = ssl.create_default_context()
    server = smtplib.SMTP(smtp_host, smtp_tls_port)
    server.starttls(context=context)

    server.login(username, password)
    server.sendmail(from_addr, to_addrs, message.as_string())
    server.quit()