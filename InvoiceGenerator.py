from borb.pdf.document.document import Document
from borb.pdf.page.page import Page
from borb.pdf.canvas.layout.page_layout.multi_column_layout import SingleColumnLayout
from decimal import Decimal
from borb.pdf.canvas.layout.image.image import Image
from borb.pdf.canvas.layout.text.paragraph import Paragraph
from borb.pdf.canvas.layout.layout_element import Alignment
from datetime import datetime
import random
from borb.pdf.pdf import PDF
from borb.pdf.canvas.color.color import HexColor, X11Color
from borb.pdf.canvas.layout.table.fixed_column_width_table import FixedColumnWidthTable as Table
from borb.pdf.canvas.layout.table.table import TableCell
import json


def buildJSON(cart, subtotal, invoice_json=None):
    if invoice_json is None:
        invoice_json = {"order": []}
    for key in cart:
        invoice_json["order"].append(
            {
                "Description": key,
                "Quantity": cart[key][0],
                "Unit Price": cart[key][1],
                "Amount": cart[key][0] * cart[key][1],
            })

    taxes = 0.13 * subtotal
    total = subtotal + taxes
    invoice_json["Subtotal"] = subtotal
    invoice_json["Taxes"] = taxes
    invoice_json["Total"] = total
    return invoice_json


def _build_itemized_description_table(cart, subtotal):
    table_001 = Table(number_of_rows=15, number_of_columns=4)
    for h in ["DESCRIPTION", "QTY", "UNIT PRICE", "AMOUNT"]:
        table_001.add(
            TableCell(
                Paragraph(h, font_color=X11Color("White")),
                background_color=X11Color("Gray"),
            )
        )

    odd_color = HexColor("BBBBBB")
    even_color = HexColor("FFFFFF")
    for row_number, key in enumerate(cart):
        c = even_color if row_number % 2 == 0 else odd_color
        table_001.add(TableCell(Paragraph(key), background_color=c))
        table_001.add(TableCell(Paragraph(str(cart[key][0])), background_color=c))
        table_001.add(TableCell(Paragraph("$ " + "{:.2f}".format(cart[key][1])), background_color=c))
        table_001.add(TableCell(Paragraph("$ " + "{:.2f}".format(cart[key][0] * cart[key][1])), background_color=c))

    # Optionally add some empty rows to have a fixed number of rows for styling purposes
    for row_number in range(len(cart), 11):
        c = even_color if row_number % 2 == 0 else odd_color
        for _ in range(0, 4):
            table_001.add(TableCell(Paragraph(" "), background_color=c))

    table_001.add(
        TableCell(Paragraph("Subtotal", font="Helvetica-Bold", horizontal_alignment=Alignment.RIGHT, ), col_span=3, ))
    table_001.add(TableCell(Paragraph(f"$ {subtotal:.2f}", horizontal_alignment=Alignment.RIGHT)))
    table_001.add(
        TableCell(Paragraph("Taxes", font="Helvetica-Bold", horizontal_alignment=Alignment.RIGHT), col_span=3, ))
    table_001.add(TableCell(Paragraph(f"$ {subtotal * 0.13:.2f}", horizontal_alignment=Alignment.RIGHT)))
    table_001.add(
        TableCell(Paragraph("Total", font="Helvetica-Bold", horizontal_alignment=Alignment.RIGHT), col_span=3, ))
    table_001.add(TableCell(Paragraph(f"$ {subtotal * 1.13:.2f}", horizontal_alignment=Alignment.RIGHT)))
    table_001.set_padding_on_all_cells(Decimal(2), Decimal(2), Decimal(2), Decimal(2))
    table_001.no_borders()
    return table_001


def _build_billing_and_shipping_information():
    table_001 = Table(number_of_rows=6, number_of_columns=2)
    table_001.add(
        Paragraph(
            "BILL TO",
            background_color=HexColor("263238"),
            font_color=X11Color("White"),
        )
    )
    table_001.add(
        Paragraph(
            "SHIP TO",
            background_color=HexColor("263238"),
            font_color=X11Color("White"),
        )
    )
    table_001.add(Paragraph("[Company]"))  # BILLING
    table_001.add(Paragraph("[Recipient Name]"))  # SHIPPING
    table_001.add(Paragraph("[Company Name]"))  # BILLING
    table_001.add(Paragraph("[Company Name]"))  # SHIPPING
    table_001.add(Paragraph("[Street Address]"))  # BILLING
    table_001.add(Paragraph("[Street Address]"))  # SHIPPING
    table_001.add(Paragraph("[City, State, ZIP Code]"))  # BILLING
    table_001.add(Paragraph("[City, State, ZIP Code]"))  # SHIPPING
    table_001.add(Paragraph("[Phone]"))  # BILLING
    table_001.add(Paragraph("[Phone]"))  # SHIPPING
    table_001.set_padding_on_all_cells(Decimal(2), Decimal(2), Decimal(2), Decimal(2))
    table_001.no_borders()
    return table_001


def _build_invoice_information(invoiceNumber):
    table_001 = Table(number_of_rows=5, number_of_columns=3)

    table_001.add(Paragraph("[Street Address]"))
    table_001.add(Paragraph("Date", font="Helvetica-Bold", horizontal_alignment=Alignment.RIGHT))
    now = datetime.now()
    table_001.add(Paragraph("%d/%d/%d" % (now.day, now.month, now.year)))

    table_001.add(Paragraph("[City, State, ZIP Code]"))
    table_001.add(Paragraph("Invoice #", font="Helvetica-Bold", horizontal_alignment=Alignment.RIGHT))
    table_001.add(Paragraph("%d" % invoiceNumber))

    table_001.add(Paragraph("[Phone]"))
    table_001.add(Paragraph("Due Date", font="Helvetica-Bold", horizontal_alignment=Alignment.RIGHT))
    table_001.add(Paragraph("%d/%d/%d" % (now.day, now.month, now.year)))

    table_001.add(Paragraph("[Email Address]"))
    table_001.add(Paragraph(" "))
    table_001.add(Paragraph(" "))

    table_001.add(Paragraph("[Company Website]"))
    table_001.add(Paragraph(" "))
    table_001.add(Paragraph(" "))

    table_001.set_padding_on_all_cells(Decimal(2), Decimal(2), Decimal(2), Decimal(2))
    table_001.no_borders()
    return table_001


def createPDF(cart, subtotal):
    invoiceNumber = random.randint(1000, 10000)
    # Create document
    pdf = Document()

    # Add page
    page = Page()
    pdf.append_page(page)

    page_layout = SingleColumnLayout(page)
    page_layout.vertical_margin = page.get_page_info().get_height() * Decimal(0.02)

    page_layout.add(
        Image(
            "https://s3.stackabuse.com/media/articles/creating-an-invoice-in-python-with-ptext-1.png",
            width=Decimal(128),
            height=Decimal(128),
        ))

    # Invoice information table
    page_layout.add(_build_invoice_information(invoiceNumber))

    # Empty paragraph for spacing
    page_layout.add(Paragraph(" "))

    # Billing and shipping information table
    page_layout.add(_build_billing_and_shipping_information())

    # Itemized description
    page_layout.add(_build_itemized_description_table(cart, subtotal))

    # Creating a JSON file
    invoice_json = buildJSON(cart, subtotal)
    invoice_json_bytes = bytes(json.dumps(invoice_json, indent=4), encoding="latin1")

    pdf.append_embedded_file("invoice.json", invoice_json_bytes)

    with open("PurchaserInvoices/PurchaseInvoice#"+str(invoiceNumber)+".pdf", "wb") as pdf_file_handle:
        PDF.dumps(pdf_file_handle, pdf)

    return invoiceNumber
