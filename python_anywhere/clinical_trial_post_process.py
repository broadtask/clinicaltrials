import sys
import time
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
import emailable


def xpath_to_text(webpage, xpath):
    """Conver elemnt to text"""

    try:
        return webpage.xpath(xpath)[0].strip()
    except:
        return ""


def get_tld_list():
    domain = pd.read_csv("/home/clinicaltrials/clinical_trial_updated/tld.csv", keep_default_na=False)[
        "domain"].values.tolist()
    country = pd.read_csv("/home/clinicaltrials/clinical_trial_updated/tld.csv", keep_default_na=False)[
        "country"].values.tolist()
    return domain, country


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

    if response.status_code != 200:
        print(f"Apollo API error!")
        print(f"RESPONSE: ", response.text)
        os._exit(1)

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
    if response.status_code != 200:
        print(f"Apollo API error!")
        print(f"RESPONSE: ", response.text)
        os._exit(1)
    try:
        json_data = response.json()
    except:
        json_data = {}
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


def check_deliverable(email, api_key):
    if email.strip() == "":
        return True

    c = 0
    while c < 3:
        try:
            isDeliverable = emailable.Client(api_key).verify(
                email, accept_all=True, timeout=30, smtp=True).state
        except:
            isDeliverable = ""

        if isDeliverable == "undeliverable":

            c += 1
            continue
        else:
            return True

    if c == 3:

        return False


def process_each_data(profile_data, file_name, api_key, domain_list, dom_country_list):

    f_name = profile_data["f_name"]
    l_name = profile_data["l_name"]
    email = profile_data["email"]

    email_for_country = profile_data["email_for_country"]

    contact_info_dict = get_contact_enrichment_data(
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
        if email != "":
            company_domain = email.split("@")[-1].strip()
        elif email_for_country != "":
            company_domain = email_for_country.split("@")[-1].strip()
        else:
            company_domain = ""

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

        if company_country != "":

            each_profile["city"] = company_city
            each_profile["country"] = company_country
            each_profile["state"] = company_state
            each_profile["company_website"] = company_website
        else:
            each_profile["city"] = company_city
            each_profile["country"] = profile_data["country"]
            each_profile["state"] = company_state
            each_profile["company_website"] = company_website

    if new_email.lower().strip() == "" or new_email.lower().strip() == email.lower().strip():
        pass
    else:
        email = new_email

    is_deliverable = check_deliverable(email, api_key)

    if is_deliverable == True:
        each_profile["email"] = email
    else:
        each_profile["email"] = ""
    # each_profile["email"] = email

    # REMOVE PROFESSOR FROM NAMES
    first_name = each_profile["f_name"].lower().replace(
        "professor", "").strip()
    last_name = each_profile["l_name"].lower().replace("professor", "").strip()
    other_study_contact = each_profile["Other Study Contact"].lower().replace(
        "professor", "").strip()

    each_profile["f_name"] = first_name.title()
    each_profile["l_name"] = last_name.title()
    each_profile["Other Study Contact"] = other_study_contact.title()

    if each_profile["country"] == "":

        if each_profile["email"] != "":
            try:
                email_domain = "." + each_profile["email"].split(
                    "@")[-1].strip().split(".")[-1].strip().lower()
            except:
                email_domain = "none"

            if email_domain in domain_list:
                domain_index = domain_list.index(email_domain)
                country_name = dom_country_list[domain_index]
                each_profile["country"] = country_name
    try:
        if "china" in each_profile["country"].lower() or "russia" in each_profile["country"].lower():
            return
    except:
        pass

    try:
        if each_profile["country"].lower() == "united states" and each_profile["sequence-category"] == "Not USA":
            each_profile["sequence-category"] = "USA"
    except:
        pass
    # each_profile["ValidationResponse"] = validation_response

    data_list = [each_profile["nct_id"], each_profile["url"], each_profile["posted date"], each_profile["enrollment"], each_profile["sponsor"], each_profile["f_name"], each_profile["l_name"], each_profile["job_title"], each_profile["phone"],
                 each_profile["email"], each_profile["linkedin_url"], each_profile["Other Study Contact"], each_profile["city"], each_profile["state"], each_profile["country"], each_profile["company_website"], each_profile["sequence-category"], each_profile["condition"]]

    save_csv(file_name, data_list, isFirst=False, removeAtStarting=False)


def group_by_id(my_dict):
    # create a list of unique ids in the dictionary
    unique_ids = list(set([d['nct_id'] for d in my_dict]))

    # create a list of lists, where each sublist contains dictionaries with the same id

    result = []
    for id in unique_ids:
        sublist = [d for d in my_dict if d['nct_id'] == id]
        result.append(sublist)

    return result


def get_country_status(data):

    country_list = []

    for each_data in data:

        if each_data["country"] != "":
            country_list.append(each_data["country"])

    if len(country_list) == 0:
        return ""
    else:
        if "United States" in country_list:
            return "United States"
        else:
            return country_list[0]


def save_dict_to_csv(dictionary, filename):
    with open(filename, mode='a', newline='', encoding='utf-8-sig') as file:
        writer = csv.writer(file)
        writer.writerow(dictionary.values())


def apply_algorithm(file_name):

    all_data = csv_to_list_of_dicts(file_name)

    save_csv(file_name, ["nct_id", "url", "posted date", "enrollment",
             "sponsor", "f_name", "l_name", "job_title", "phone", "email", "linkedin_url", "Other Study Contact", "city", "state", "country", "company_website", "sequence-category", "condition"], isFirst=True, removeAtStarting=True)
    similar_nct_id_list = group_by_id(all_data)

    for each_similar_data in similar_nct_id_list:

        country_status = get_country_status(each_similar_data)

        for each_nct in each_similar_data:
            country = each_nct["country"]
            if country.strip() == "":
                country = country_status
                each_nct["country"] = country

            if each_nct["country"].lower() == "united states" and each_nct["sequence-category"].lower() == "not usa":
                each_nct["sequence-category"] = "USA"

            save_dict_to_csv(each_nct, file_name)


def post_process(temp_file_org, api_key):
    print("Started post processing.............")
    output_file_name = f'{temp_file_org.split("_temp")[0].strip()}.csv'

    all_data_from_csv = csv_to_list_of_dicts(temp_file_org)
    # output_file_name = f"{(datetime.now(timezone.utc) - timedelta(hours=8, days=1)).strftime('%Y-%m-%d')}-clinicaltrials-gov.csv"

    save_csv(output_file_name, ["nct_id", "url", "posted date", "enrollment",
             "sponsor", "f_name", "l_name", "job_title", "phone", "email", "validationResponse", "linkedin_url", "Other Study Contact", "city", "state", "country", "company_website", "sequence-category", "condition"], isFirst=True, removeAtStarting=True)
    domain_list, dom_country_list = get_tld_list()
    for idx, each_data in enumerate(all_data_from_csv):

        process_each_data(each_data, output_file_name,
                          api_key, domain_list, dom_country_list)
        print(f"Post processing: {idx+1}/{len(all_data_from_csv)}")
        # print(contact_info_dict["person"]["organization"]["city"])
    time.sleep(2)
    apply_algorithm(output_file_name)
    print("Post processing finished!")
    return output_file_name


# post_process("2023-03-05-clinicaltrials-gov_temp.csv")
# apply_algorithm("2023-03-22-clinicaltrials-gov.csv")
