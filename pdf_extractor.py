import os
import json
import pdfplumber
import re


def extract_text_from_pdf(filename):
    with pdfplumber.open(filename) as pdf:
        page = pdf.pages[0]
        text = page.extract_text()

    return text.lower()


def handle_items_data(text):
    items = re.findall('(?<=line total)(.*?)(?=subtotal)',
                       text, flags=re.S)[0].split('\n')
    items = [item for item in items if re.search('[a-z]+', item)]

    items_aux = []
    for item in items:
        item = re.sub('  +', ' ', item)
        item = item.lstrip()
        items_aux.append(item.split(' '))

    result = []
    for item_aux in items_aux:
        item_aux.pop(-1)

        qty = item_aux[0]
        unit_price = item_aux[-2]
        total = item_aux[-1]

        item_aux.pop(0)
        item_aux.pop(-2)
        item_aux.pop(-1)

        description = ' '.join(str(x) for x in item_aux)

        result.append({'quantity': qty, 'description': description,
                       'Unit price': unit_price, 'total': total})

    return result


def handle_invoice_data(text):
    values = text[text.rfind('subtotal'):text.rfind(
        'make all checks payable to stark industries')]
    values = re.findall('\d+', values)
    values_len = len(values)

    subtotal = values[0]
    if values_len < 3:
        total = values[1]
        tax = 0
    else:
        tax = values[1]
        total = values[2]

    id = re.search('#[0-9]+', text).group()
    dates = re.findall(r'(\d+/\d+/\d+)', text)

    return {
        'id': id, 'date': dates[0], 'due_date': dates[1],
        'subtotal': subtotal, 'tax': tax, 'total': total,
    }


def handle_customer_data(text):
    customer_data = re.findall(
        '(?<=to:)(.*?)(?=salesperson)', text, flags=re.S)[0].split('\n')

    new_customer_data = []
    for item in customer_data:
        item = item.rstrip()
        item = item.lstrip()
        new_customer_data.append(item)

    id = new_customer_data[6]
    id = id[id.rfind('id:')+4:]
    name = new_customer_data[0]
    company = new_customer_data[1]
    phone = re.search('[0-9]+', new_customer_data[5]).group()
    location = new_customer_data[3].split(',')
    city = location[0]
    state = location[1].replace(' ', '')
    street = new_customer_data[2]
    postal_code = new_customer_data[4]

    customer = {
        'id': id, 'name': name, 'company': company,
        'phone': phone, 'street': street,
        'city': city, 'state': state,
        'postal_code': postal_code
    }

    return customer


def generate_json(filename, dictionary):
    filename = filename.replace('pdf', 'json')
    filename = filename.replace('input', 'output_f')
    with open(filename, 'w') as outfile:
        json.dump(dictionary, outfile)


def main(file):
    text = extract_text_from_pdf(file)
    customer = handle_customer_data(text)
    invoice = handle_invoice_data(text)
    items = handle_items_data(text)
    result = {'customer': customer, 'invoice': invoice, 'items': items}

    generate_json(file, result)


if __name__ == '__main__':
    input_path = r'C:\Users\danie\OneDrive\Desktop\ocr\input'
    for file in os.listdir(input_path):
        main(f'{input_path}/{file}')
