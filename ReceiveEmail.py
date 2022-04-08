import email
import os
import imaplib


def receiveEmail(receiveAddress, destinationFolder):
    EMAIL = receiveAddress
    PASSWORD = 'coe8172022'
    SERVER = 'imap.gmail.com'


    mail = imaplib.IMAP4_SSL(SERVER)
    mail.login(EMAIL, PASSWORD)

    mail.select('inbox')

    status, data = mail.search(None, '(SUBJECT "Order Invoice")')

    mail_ids = []

    for block in data:
        mail_ids += block.split()

        status, data = mail.fetch(mail_ids[len(mail_ids)-1], '(RFC822)')

        for response_part in data:
            if isinstance(response_part, tuple):
                message = email.message_from_bytes(response_part[1])

                mail_from = message['from']
                mail_subject = message['subject']

                if message.is_multipart():
                    mail_content = ''

                    for part in message.get_payload():
                        if part.get_content_type() == 'text/plain':
                            mail_content += part.get_payload()
                else:
                    mail_content = message.get_payload()

                if part.get_content_maintype() == 'multipart':
                    continue

                if part.get('Content-Disposition') is None:
                    continue
                invoiceNumber = mail_subject.split(" ")[2]
                fileName = "ReceivedInvoice#"+invoiceNumber+".pdf"
                if bool(fileName):
                    filePath = os.path.join(destinationFolder+"/", fileName)
                    if not os.path.isfile(filePath) :
                        fp = open(filePath, 'wb')
                        fp.write(part.get_payload(decode=True))
                        fp.close()

                    print('Downloaded "{file}" from email titled "{subject}" sent by "{sender}".'.format(file=fileName, subject=mail_subject, sender=mail_from))
    return mail_subject
