from urllib.parse import urlparse
import re
from datetime import datetime, timedelta, timezone
from functools import reduce  # forward compatibility for Python 3
import operator
import os
import requests
from lxml import html
import csv
import json
from mail import send_email
import pandas as pd


def save_csv(filename, data_list, isFirst=False, removeAtStarting=True):
    """Save data to csv file"""

    if isFirst:
        if os.path.isfile(filename):
            if removeAtStarting:
                os.remove(filename)
            else:
                pass

    with open(f'{filename}', "a", newline='', encoding='utf-8-sig') as fp:
        wr = csv.writer(fp, dialect='excel')
        wr.writerow(data_list)


def get_company_enrichment_data(domain_name):
    url = "https://api.apollo.io/v1/organizations/enrich"

    querystring = {
        "api_key": "Zt4fkBc2in5Em1k2X5iybA",
        "domain": domain_name
    }

    headers = {
        'Cache-Control': 'no-cache',
        'Content-Type': 'application/json'
    }

    response = requests.request(
        "GET", url, headers=headers, params=querystring)

    return response.json(), response


def get_contact_enrichment_data(f_name, l_name, email):
    url = "https://api.apollo.io/v1/people/match"

    data = {
        "api_key": "Zt4fkBc2in5Em1k2X5iybA",
        "first_name": f_name,
        "last_name": l_name,
        "email": email,

    }

    headers = {
        'Cache-Control': 'no-cache',
        'Content-Type': 'application/json'
    }

    response = requests.request("POST", url, headers=headers, json=data)
    json_data = response.json()
    return json_data, response


def getFromDict(dataDict, mapList):
    return reduce(operator.getitem, mapList, dataDict)


def json_to_text(json_data, keys):

    try:
        return getFromDict(json_data, keys)

    except:
        return ""


def csv_to_list_of_dicts(csv_filename):
    with open(csv_filename, mode='r', encoding="utf-8-sig") as csv_file:
        csv_reader = csv.DictReader(csv_file)
        list_of_dicts = []
        for row in csv_reader:
            list_of_dicts.append(row)
    return list_of_dicts


def process_each_data(profile_data, file_name):

    f_name = profile_data["f_name"]
    l_name = profile_data["l_name"]
    email = profile_data["email"]

    contact_info_dict, response = get_contact_enrichment_data(
        f_name, l_name, email)

    new_city = json_to_text(contact_info_dict, ["person", "city"])
    new_country = json_to_text(contact_info_dict, ["person", "country"])
    new_state = json_to_text(contact_info_dict, ["person", "state"])
    new_email = json_to_text(contact_info_dict, ["person", "email"])
    linkedin_url = json_to_text(contact_info_dict, ["person", "linkedin_url"])
    job_title = json_to_text(contact_info_dict, ["person", "title"])

    each_profile = profile_data.copy()

    each_profile["job_title"] = job_title
    each_profile["linkedin_url"] = linkedin_url
    each_profile["city"] = new_city
    each_profile["state"] = new_state
    each_profile["company_website"] = ""

    if new_country != "":
        each_profile["country"] = new_country
    else:
        company_domain = email.split("@")[-1].strip()
        company_json_data, response = get_company_enrichment_data(
            company_domain)
        company_website = json_to_text(
            company_json_data, ["organization", "website_url"])
        company_country = json_to_text(
            company_json_data, ["organization", "country"])
        company_state = json_to_text(
            company_json_data, ["organization", "state"])
        company_city = json_to_text(
            company_json_data, ["organization", "city"])

        each_profile["city"] = company_city
        each_profile["country"] = company_country
        each_profile["state"] = company_state
        each_profile["company_website"] = company_website

        # print(company_json_data)
        # input()

    if new_email.lower().strip() == "" or new_email.lower().strip() == email.lower().strip():
        pass
    else:
        email = new_email

    each_profile["email"] = email

    data_list = [each_profile["nct_id"], each_profile["url"], each_profile["posted date"], each_profile["brief_title"],
                 each_profile["official_title"], each_profile["enrollment"], each_profile["sponsor"], each_profile["f_name"], each_profile["l_name"], each_profile["job_title"], each_profile["phone"], each_profile["email"], each_profile["linkedin_url"], each_profile["Other Study Contact"], each_profile["city"], each_profile["state"], each_profile["country"], each_profile["company_website"], each_profile["condition"]]

    save_csv(file_name, data_list, isFirst=False, removeAtStarting=False)


def post_process(temp_file_org):
    print("Started post processing.............")
    output_file_name = f'{temp_file_org.split("_temp")[0].strip()}.csv'

    all_data_from_csv = csv_to_list_of_dicts(temp_file_org)
    # output_file_name = f"{(datetime.now(timezone.utc) - timedelta(hours=8, days=1)).strftime('%Y-%m-%d')}-clinicaltrials-gov.csv"

    save_csv(output_file_name, ["nct_id", "url", "posted date", "brief_title", "official_title", "enrollment",
             "sponsor", "f_name", "l_name", "job_title", "phone", "email", "linkedin_url", "Other Study Contact", "city", "state", "country", "company_website", "condition"], isFirst=True, removeAtStarting=False)

    for each_data in all_data_from_csv:

        process_each_data(each_data, output_file_name)
        # print(contact_info_dict["person"]["organization"]["city"])
    print("Post processing finished!")

# post_process("2023-03-05-clinicaltrials-gov_temp.csv")
