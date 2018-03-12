{
    'name': 'Multiple discount on invoices',
    'version': '1.0',
    'category': 'Invoices',
    'sequence': 6,
    'summary': "Discount on invoices",
    'author': 'Sp4tz',
    'company': 'Magneticlab SARL',
    'website': "https://magneticlab.ch",
    'description': """

Invoice Discount for Total Amount
=======================
Module to manage discount on total amount in Invoice.
        as an specific amount or percentage
""",
    'depends': ['base', 'account', 'sale'],
    'data': [
        'views/account_invoice_form.xml',
        'views/product_template_form.xml',
        'data/product_product.xml',

    ],
    'demo': [
    ],
    'price': '25',
    'currency': 'EUR',
    'installable': True,
    'auto_install': False,
    'images': ['static/description/banner.png'],
}
