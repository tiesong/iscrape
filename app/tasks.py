import requests
import re
import csv
import urllib3
import time
import os

from bs4 import BeautifulSoup
from celery import shared_task
from django.core.mail import EmailMessage
from django.conf import settings

from .models import ScrapeRequest

urllib3.disable_warnings()

except_strings = ['.png', 'jpg']


@shared_task
def scrape(s_id):
    scrape_request = ScrapeRequest.objects.get(id=s_id)
    result_path = 'csv/result/'
    if not os.path.exists(result_path):
        os.makedirs(result_path)
    result_csv_path = result_path + time.strftime("%Y_%m_%d_%H_%M_%S_") + '.csv'
    with open(scrape_request.csv_path, encoding='utf-8') as csv_file:
        with open(result_csv_path, 'w') as output_file:
            reader = csv.reader(csv_file)
            writer = csv.writer(output_file, delimiter=",", lineterminator="\n")
            writer.writerow(['website', 'facebook', 'instagram', 'email'])
            # i = 0
            for row in reader:
                try:
                    if row:
                        url = row[0]
                        if url.lower() == 'website':
                            continue

                        if not url:
                            row.append('')
                            row.append('')
                            row.append('')
                        else:
                            facebook, instagram, emails = extract_data(url)
                            row.append(facebook)
                            row.append(instagram)
                            row.append(','.join(emails))

                        # print(i)
                        # i = i + 1
                        writer.writerow(row, )
                except Exception as e:
                    print(e)
                    continue

            scrape_request.result_csv_path = result_csv_path
            scrape_request.status = 1
            scrape_request.save()

    message = EmailMessage("Scraped Result", "Here is the scraped result: {}.".format(scrape_request.subject), settings.DEFAULT_FROM_EMAIL,
                           [scrape_request.email])
    message.attach('{}.csv'.format(scrape_request.subject), open(result_csv_path).read(), 'text/csv')
    f = message.send()
    return f


def extract_data(address):
    if not address.startswith('http'):
        address = 'http://' + address

    headers = {
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/42.0.2311.90 Safari/537.36'}

    email = list()
    facebook = list()
    instagram = list()

    try:
        soup = BeautifulSoup(requests.get(address, headers=headers, verify=False,).text, 'html.parser')
        [s.extract() for s in soup('link')]
        [s.extract() for s in soup('script')]
        [s.extract() for s in soup('img')]

        # content = requests.get(address, headers=headers, verify=False).text
        content = str(soup)
        facebook.extend(re.findall(
            'href="http[s]?://www.facebook.com(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\), ]|(?:%[0-9a-fA-F][0-9a-fA-F]))+',
            content))
        facebook.extend(re.findall(
            'href="http[s]?://facebook.com(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\), ]|(?:%[0-9a-fA-F][0-9a-fA-F]))+',
            content))

        instagram.extend(re.findall(
            'href="http[s]?://www.instagram.com(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\), ]|(?:%[0-9a-fA-F][0-9a-fA-F]))+',
            content))
        instagram.extend(re.findall(
            'href="http[s]?://instagram.com(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\), ]|(?:%[0-9a-fA-F][0-9a-fA-F]))+',
            content))

        email.extend(re.findall('[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+', content))
    except Exception as e:
        print('no content for main')
        return '', '', email

    try:
        soup = BeautifulSoup(requests.get(address + '/contact', headers=headers, verify=False, ).text, 'html.parser')
        [s.extract() for s in soup('link')]
        [s.extract() for s in soup('script')]
        [s.extract() for s in soup('img')]
        content = str(soup)
        email.extend(re.findall('[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+', content))
    except Exception as e:
        print('no content for contact')

    try:
        soup = BeautifulSoup(requests.get(address + '/about', headers=headers, verify=False, ).text, 'html.parser')
        [s.extract() for s in soup('link')]
        [s.extract() for s in soup('script')]
        [s.extract() for s in soup('img')]
        content = str(soup)
        email.extend(re.findall('[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+', content))
    except Exception as e:
        print('no content for about')

    facebook = list(set(facebook))
    instagram = list(set(instagram))
    email = remove_duplicate_email(email)

    for index, item in enumerate(facebook):
        facebook[index] = facebook[index][6:]
    for index, item in enumerate(instagram):
        instagram[index] = instagram[index][6:]

    facebook_list = list()
    instagram_list = list()
    email_list = list()

    for index, item in enumerate(instagram):
        if not instagram[index].startswith('https://www.instagram.com/p/') \
                and not instagram[index].startswith('http://www.instagram.com/p/'):
            instagram_list.append(instagram[index])

    for index, item in enumerate(facebook):
        if not facebook[index].startswith('https://www.facebook.com/sharer/') \
                and not facebook[index].startswith('http://www.facebook.com/sharer/'):
            facebook_list.append(facebook[index])

    for index, item in enumerate(email):
        if any(check_str in email[index] for check_str in except_strings):
            continue
        else:
            email_list.append(email[index])
    if len(facebook_list) == 0:
        facebook = ''
    else:
        facebook = facebook[0]
    if len(instagram_list) == 0:
        instagram = ''
    else:
        instagram = instagram_list[0]
    return facebook, instagram, email_list


def remove_duplicate_email(emails):
    result = []
    marker = set()

    for l in emails:
        ll = l.lower()
        if ll not in marker:
            marker.add(ll)
            result.append(l)
    return result