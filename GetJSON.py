import PyPDF4 as pf
import json

def printJSON(cart):
    print("INVOICE")
    for product in cart['order']:
        print(f"Product: {product['Description']:<18}  Quantity: {product['Quantity']:<4}  Unit Price: ${product['Unit Price']:>7.2f} "
              f"   Amount: ${(product['Quantity'] * product['Unit Price']):>8.2f}")
    print(f"\n{' ' * 57}Subtotal:          ${cart['Subtotal']:>9.2f}")
    print(f"{' ' * 57}Taxes (13%):       ${cart['Taxes']:>9.2f}")
    print(f"{' ' * 57}Total:             ${cart['Total']:>9.2f}")

def getJSON(filepath):
    pdf = pf.PdfFileReader(filepath)

    catalog = pdf.trailer['/Root']
    fDetail = catalog['/Names']['/EmbeddedFiles']['/Kids'][0].getObject()['/Names']
    soup = fDetail[1].getObject()

    file = soup['/EF']['/F'].getData().decode()
    invoiceJSON = json.loads(str(file))
    return invoiceJSON
