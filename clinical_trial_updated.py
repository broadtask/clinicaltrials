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
from clinical_trial_post_process import post_process
from clinical_trial_email_database import update_email_database

Name_Data = ""
EACH_STUDY = ""


def read_competitors():

    file_name = "competitors.csv"
    domains = []

    all_completitors = pd.read_csv(file_name, keep_default_na=False)[
        "Website"].values.tolist()

    for each_completitor in all_completitors:
        domain = '.'.join(urlparse(each_completitor).netloc.split('.')[-2:])
        domains.append(domain)

    return domains


def get_all_domains():
    url = "https://en.wikipedia.org/wiki/Country_code_top-level_domain"

    webpage, response = send_requests(url)
    all_domain_elems = webpage.xpath(
        "//div[@class = 'mw-parser-output']/table[@class = 'wikitable mw-collapsible sortable'][1]/tbody/tr[not (@style)]")
    for each_domain_elem in all_domain_elems:

        domain_name = each_domain_elem.xpath("td[1]//text()")
        print(domain_name)


def xpath_to_text(webpage, xpath):
    """Conver elemnt to text"""

    try:
        return webpage.xpath(xpath)[0].strip()
    except:
        return ""


def send_requests(url, headers="", cookies="", params=""):
    """Request sending Function"""

    response = requests.get(url, headers=headers,
                            cookies=cookies, params=params)
    webpage = html.fromstring(response.content)
    return webpage, response


def get_all_domains():
    url = "https://en.wikipedia.org/wiki/Country_code_top-level_domain"

    webpage, response = send_requests(url)
    all_domain_elems = webpage.xpath(
        "//div[@class = 'mw-parser-output']/table[@class = 'wikitable mw-collapsible sortable'][1]/tbody/tr[not (@style)]")
    all_domain_data = []
    for each_domain_elem in all_domain_elems:

        domain_name = xpath_to_text(each_domain_elem, "td[1]//text()")
        country_name = xpath_to_text(each_domain_elem, "td[2]/a/text()")

        all_domain_data.append({
            "domain": domain_name,
            "country": country_name
        })
    return all_domain_data


ALL_COMPLETITORS = read_competitors()
ALL_DOMAINS = get_all_domains()


def check_domain(email):

    domain_name = email.split("@")[-1].split(".")[-1].strip()

    for each_domain in ALL_DOMAINS:

        if each_domain["domain"].replace(".", "").lower().strip() == domain_name:

            country_name = each_domain["country"]

            # if "united" in country_name.lower().strip() and "states" in country_name.lower().strip():
            #     country_data = "United States"

            # else:
            #     country_data = "Not United States"
            return country_name
    else:
        return "Not Matched"


def read_scrapped_data(previous_data_file):
    f = open(previous_data_file)
    return json.load(f)


def check_listed_word_in_name(name):
    listed_words = ["call",
                    "projects",
                    "project",
                    "center",
                    "recruitment",
                    "office",
                    "clinical",
                    "trials",
                    "trial",
                    "study",
                    "studies",
                    "toll",
                    "free",
                    "number",
                    "Central",
                    "Contact",
                    "Therapeutics",
                    "Research",
                    "Development",
                    "Surgical",
                    "Vision",
                    "Pharmaceuticals",
                    "Pharma",
                    "Medical",
                    "Director",
                    "Information",
                    "Info",
                    "Boehringer",
                    "Transparency",
                    "Department",
                    "Dpt.",
                    "Dept.",
                    "Affairs",
                    "Xenon",
                    "Gilead",
                    "Novo",
                    "The",
                    "Diagnostic",
                    "Radiology",
                    "Novartis",
                    "Contact",
                    "Info",
                    "Information",
                    "Clin", "Triage",
                    "Line",
                    "Of",
                    "Email",
                    "NCT", "Site", "Bristol-Myers", "Squibb", "Med",
                    "HR", "quality", "management", "compliance"]

    listed_words = [s.lower() for s in listed_words]
    if any(word in name.strip().lower() for word in listed_words):

        return True
    else:
        return False


def remove_middle_initials_from_name(name):

    if check_listed_word_in_name(name):
        return "bypass"

    split_name = name.split(" ")
    split_name = [s.strip() for s in split_name if s.strip() != ""]
    middle_name = ""

    if len(split_name) >= 3:

        split_name.pop()
        first_name = split_name.pop(0)
        if ("." in first_name.strip() and len(first_name) <= 2) or first_name.strip().lower() == "dr" or first_name.strip().lower() == "dr.":
            name = name.replace(first_name, "")

        for s in split_name:
            if len(s) <= 2 and s.isupper():
                middle_name = s
                break

    else:
        pass

    if middle_name.strip() != "":
        new_name = name.replace(f"{middle_name} ", "").strip()
    else:
        new_name = name.strip()
    return re.sub(' +', ' ', new_name)


def save_csv(filename, data_list, isFirst=False):
    """Save data to csv file"""

    global Name_Data

    if isFirst:
        if os.path.isfile(filename):
            os.remove(filename)
        else:
            pass
        data_set = data_list

    else:
        try:
            name = data_list[7].split(",")[0]
            name = remove_middle_initials_from_name(name)

            if name == "bypass":
                return
        except:
            name = ""
        try:
            other_name = data_list[10].strip().split(",")[0]
            other_name = remove_middle_initials_from_name(other_name)
            if other_name == "bypass":
                return
        except:
            other_name = ""

        name_splitted = name.strip().split(" ")

        if len(name_splitted) > 1:
            name_splitted = [s.strip() for s in name_splitted if len(
                s.strip().replace(".", "")) != 1]

            first_name = name_splitted[0]
            name_splitted.pop(0)
            last_name = " ".join(name_splitted)
        elif len(name_splitted) == 1:
            return
        else:
            return

        other_name_splitted = other_name.split(" ")
        other_name_splitted = [s.strip()
                               for s in other_name_splitted if s.strip() != ""]
        other_name_splitted = [s for s in other_name_splitted if len(s) > 1]

        other_name = " ".join(other_name_splitted).title()
        phone = data_list[8].replace("+", "")
        email = data_list[9]
        email_for_country = email

        if any(competitor in email for competitor in ALL_COMPLETITORS):

            email = "inCompetitors"
        else:
            email = email.lower()

        if email == "inCompetitors":
            return
        else:
            pass

        if check_listed_word_in_name(email.split("@")[0].strip()):
            email = ""

        full_name = f"{first_name} {last_name}"

        if full_name in Name_Data:
            return
        else:
            Name_Data = full_name

        sponsor_name = data_list[5].strip()

        if first_name.lower() in sponsor_name.lower() and last_name.lower() in sponsor_name.lower():
            return

        check_domain_name = check_domain(email)

        if check_domain_name == "Not Matched":

            country = data_list[11]
        else:
            country = check_domain_name

        # if check_domain_name == "United States":
        #     country = "United States"

        # elif check_domain_name == "Not United States":
        #     country = "Not United States"

        # else:
        #     pass

        category = get_category_data(EACH_STUDY, data_list[5], country)

        data_set = [data_list[0], data_list[1], data_list[2], data_list[3], data_list[4], data_list[5],
                    data_list[6], first_name.title(), last_name.title(), phone, email, other_name, country, category, data_list[12], email_for_country]

    with open(f'{filename}', "a", newline='', encoding='utf-8-sig') as fp:
        wr = csv.writer(fp, dialect='excel')
        wr.writerow(data_set)


def getFromDict(dataDict, mapList):
    return reduce(operator.getitem, mapList, dataDict)


def json_to_text(json_data, keys):

    try:
        return getFromDict(json_data, keys)

    except:
        return ""


def check_posted_date(posted_date):

    time_zone_fixed = 8
    todays_date = (datetime.now(timezone.utc) -
                   timedelta(hours=time_zone_fixed))
    todays_date_string = todays_date.strftime("%B %d, %Y")
    prev_day = (todays_date -
                timedelta(days=1)).strftime("%B %d, %Y")
    FMT = "%B %d, %Y"
    posted_date_formatted = datetime.strptime(posted_date, FMT)
    today_date_formatted = datetime.strptime(todays_date_string, FMT)
    prev_day_formatted = datetime.strptime(prev_day, FMT)

    # print(f"Poseted Date: {posted_date_formatted}")
    # print(f"Todays Date: {today_date_formatted}")
    # print(f"Previous Day: {prev_day_formatted}")

    if posted_date_formatted == today_date_formatted:
        return "same_day", prev_day
    elif posted_date_formatted < prev_day_formatted:
        return False, prev_day
    else:
        return True, prev_day


def get_duplicate(name, dict_list):

    for idx, each_dict in enumerate(dict_list):

        if each_dict["name_modified"] == name:
            return True, idx
    else:
        return False, ""


def remove_duplicate_from_contact_list(investor_list, contact_list):

    uniq_contact_list = []
    investor_list_new = investor_list.copy()

    for idx_cont, each_contact in enumerate(contact_list):
        contact_name_original = each_contact["CentralContactName"]
        contact_name = name_modifier(contact_name_original)
        check = False

        for idx_inv, each_investor in enumerate(investor_list):

            investor_name_original = each_investor["OverallOfficialName"]
            investor_name = name_modifier(investor_name_original)

            if investor_name == contact_name:

                investor_list_new[idx_inv]["OverallOfficialName"] = each_contact["CentralContactName"]

                try:
                    investor_list_new[idx_inv]["OverallOfficialEMail"] = each_contact["CentralContactEMail"]
                except:
                    investor_list_new[idx_inv]["OverallOfficialEMail"] = ""

                try:
                    investor_list_new[idx_inv]["OverallOfficialPhone"] = each_contact["CentralContactPhone"]
                except:
                    investor_list_new[idx_inv]["OverallOfficialPhone"] = ""
                check = True
                break
        if check == False:
            uniq_contact_list.append(each_contact)

    return uniq_contact_list, investor_list_new


def name_modifier(name):
    name = name.lower().split(",")[0].strip()
    name_splitted = name.split(" ")
    name_splitted = [s.strip() for s in name_splitted if len(
        s.strip().replace(".", "")) > 1]
    name = " ".join(name_splitted)
    return name


def get_uniq_list_of_contacts(contact_list, investor_list):

    main_dict = []
    duplicate_status = "none"

    for each_contact in contact_list:
        contact_name_original = each_contact["CentralContactName"]
        contact_name = name_modifier(contact_name_original)

        isDuplicate, dup_idx = get_duplicate(contact_name, main_dict)

        if isDuplicate:
            main_dict[dup_idx]["isDuplicate"] = True
            duplicate_status = "partial"
        else:
            temp_dict = {
                "name": contact_name_original,
                "name_modified": contact_name,
                "isDuplicate": False,
                "phone": json_to_text(each_contact, ["CentralContactPhone"]),
                "email": json_to_text(each_contact, ["CentralContactEMail"]),
                "type": "contact",
            }

            main_dict.append(temp_dict)

    for each_investor in investor_list:
        investor_name_original = each_investor["OverallOfficialName"]
        investor_name = name_modifier(investor_name_original)

        isDuplicate, dup_idx = get_duplicate(investor_name, main_dict)

        if isDuplicate:
            main_dict[dup_idx]["isDuplicate"] = True
            duplicate_status = "partial"
        else:
            temp_dict = {
                "name": investor_name_original,
                "name_modified": investor_name,
                "isDuplicate": False,
                "phone": json_to_text(each_contact, ["OverallOfficialPhone"]),
                "email": json_to_text(each_contact, ["OverallOfficialEMail"]),
                "type": "investor",
            }
            main_dict.append(temp_dict)

    if len(contact_list) == len(main_dict):
        duplicate_status = "all same"
    else:
        pass

    return main_dict, duplicate_status


def get_category_data(each_study, enrollment_data, country):

    try:
        enrollment = int(enrollment_data)
    except:
        enrollment = 999999

    study_text = f"{each_study}".lower()
    try:
        study_text_without_elegibility = study_text.split(
            "'condition':")[1].split(r"]},")[0].strip().lower()
    except:
        study_text_without_elegibility = ""

    if "diabetes" in study_text_without_elegibility or "diabetic" in study_text_without_elegibility or "prediabetes" in study_text_without_elegibility or "prediabetic" in study_text_without_elegibility:
        category = "Diabetes"
    elif "dementia" in study_text_without_elegibility or "cognitive impairment" in study_text_without_elegibility or "cognitive decline" in study_text_without_elegibility or "cognitive dysfunction" in study_text_without_elegibility or "neurocognitive dysfunction" in study_text_without_elegibility or "cognitive deficits" in study_text_without_elegibility:
        category = "Dementia"
    elif "cbt" in study_text or "cognitive behavioral" in study_text or "cognitive behavior" in study_text:
        category = "CBT"
    elif "mhealth" in study_text or "mobile health" in study_text:
        category = "mHealth"
    elif "digital health" in study_text or "digital healthcare" in study_text or "digital therapy" in study_text:
        category = "Digital Health"
    elif enrollment < 100:
        category = "<100P"
    elif country.lower() == "united states" or country.lower() == "us" or country.lower() == "usa":
        category = "USA"
    else:
        category = "Not USA"
    return category


def get_all_data(API, file_name, enrollment_filter=40):

    range_number = 100

    for i in range(1, range_number):
        min_rank = 1+(i-1)*range_number
        max_rank = i*range_number
        print(min_rank, max_rank)
        # params = {
        #     'expr': 'NCT05709548',

        #     'fmt': 'json', }
        params = {
            'expr': '',
            'min_rnk': min_rank,
            'max_rnk': max_rank,
            'fmt': 'json', }

        while True:
            try:

                response = requests.get(API, params=params, timeout=30)
                break
            except:
                time.sleep(5)
                print("trying again....")
                continue

        all_study_data = response.json()["FullStudiesResponse"]["FullStudies"]

        for each_study in all_study_data:

            global EACH_STUDY

            EACH_STUDY = each_study

            each_study_data = json_to_text(each_study, ["Study"])

            posted_date = json_to_text(each_study_data, [
                                       "ProtocolSection", "StatusModule", "StudyFirstPostDateStruct", "StudyFirstPostDate"])

            isPostedDateGreater, prev_day = check_posted_date(posted_date)

            if isPostedDateGreater == "same_day":

                continue
            elif isPostedDateGreater == True:
                pass
            else:
                print(f"Finished Scraping: {prev_day}")
                return

            recruitment = json_to_text(
                each_study_data, ["ProtocolSection", "StatusModule", "OverallStatus"])
            if recruitment == "Not yet recruiting":
                pass
            else:
                continue

            nct_id = json_to_text(
                each_study_data, ["ProtocolSection", "IdentificationModule", "NCTId"])
            url = f"https://clinicaltrials.gov/ct2/show/{nct_id}"
            brief_title = json_to_text(
                each_study_data, ["ProtocolSection", "IdentificationModule", "BriefTitle"])
            official_title = json_to_text(
                each_study_data, ["ProtocolSection", "IdentificationModule", "OfficialTitle"])
            try:
                enrollment_int = int(json_to_text(
                    each_study_data, ["ProtocolSection", "DesignModule", "EnrollmentInfo", "EnrollmentCount"]))
                enrollment = f"{enrollment_int:,}"

            except:
                enrollment = 0

            # FILTER ENTROLLMENT
            if enrollment_int < enrollment_filter:
                continue
            # contact_person_list = json_to_text(each_study_data, [
            #                                    "ProtocolSection", "ContactsLocationsModule", "CentralContactList", "CentralContact"])

            condition_list = json_to_text(each_study_data, [
                                          "ProtocolSection", "ConditionsModule", "ConditionList", "Condition"])

            acronym = json_to_text(
                each_study_data, ["ProtocolSection", "IdentificationModule", "Acronym"])
            if acronym == "":

                conditions = "\n".join(condition_list)
            else:
                conditions = acronym

            location_list = json_to_text(each_study_data, [
                "ProtocolSection", "ContactsLocationsModule", "LocationList", "Location"])

            if location_list != "":
                location = location_list[0]["LocationCountry"]

                # if location == "United States":
                #     country = "United States"
                if location == "China" or location == "Iran" or location == "Russia":
                    continue
                elif location == "":
                    country = ""
                else:
                    country = location
            else:
                country = ""

            agency = json_to_text(each_study_data, [
                                  "ProtocolSection", "SponsorCollaboratorsModule", "LeadSponsor", "LeadSponsorName"])

            contact_module_list = json_to_text(each_study_data, [
                                               "ProtocolSection", "ContactsLocationsModule"])

            contact_list = json_to_text(
                contact_module_list, ["CentralContactList", "CentralContact"])
            investor_list = json_to_text(
                contact_module_list, ["OverallOfficialList", "OverallOfficial"])

            print("--------------------------------")
            print(nct_id)

            if type(contact_module_list) == str:
                name, phone, email, other_contact = "", "", "", ""

            else:

                # IF One Contact and no Investigators
                if len(contact_list) == 1 and len(investor_list) < 1:

                    for contact_idx, each_contact in enumerate(contact_list):

                        contact_name = json_to_text(
                            each_contact, ["CentralContactName"])
                        contact_email = json_to_text(
                            each_contact, ["CentralContactEMail"])
                        contact_phone_without_ext = json_to_text(
                            each_contact, ["CentralContactPhone"])
                        contact_phone_ext = json_to_text(
                            each_contact, ["CentralContactPhoneExt"])

                        if contact_phone_ext.strip() != "":
                            contact_phone = contact_phone_without_ext + \
                                f" ext {contact_phone_ext}"
                        else:
                            contact_phone = contact_phone_without_ext

                        other_contact = ""

                        data_list = [nct_id, url, posted_date, brief_title, official_title, enrollment,
                                     agency, contact_name, contact_phone, contact_email, other_contact, country, conditions]

                        save_csv(file_name, data_list)

                # IF More Than One Study Contacts and no Investigator
                elif len(contact_list) > 1 and len(investor_list) <= 0:

                    for contact_idx, each_contact in enumerate(contact_list):

                        contact_name = json_to_text(
                            each_contact, ["CentralContactName"])
                        contact_email = json_to_text(
                            each_contact, ["CentralContactEMail"])
                        contact_phone_without_ext = json_to_text(
                            each_contact, ["CentralContactPhone"])
                        contact_phone_ext = json_to_text(
                            each_contact, ["CentralContactPhoneExt"])

                        if contact_phone_ext.strip() != "":
                            contact_phone = contact_phone_without_ext + \
                                f" ext {contact_phone_ext}"
                        else:
                            contact_phone = contact_phone_without_ext

                        if contact_idx == 0:
                            other_contact = json_to_text(
                                contact_list[contact_idx+1], ["CentralContactName"])
                        else:
                            other_contact = json_to_text(
                                contact_list[0], ["CentralContactName"])

                        data_list = [nct_id, url, posted_date, brief_title, official_title, enrollment,
                                     agency, contact_name, contact_phone, contact_email, other_contact, country, conditions]

                        save_csv(file_name, data_list)

                # IF One or more investigators and one or more contacts
                elif len(contact_list) >= 1 and len(investor_list) >= 1:

                    uniq_list_of_contacts, duplicate_status = get_uniq_list_of_contacts(
                        contact_list, investor_list)

                    # IF ALL DUPLICATES FOUND
                    if duplicate_status == "all same":

                        for contact_idx, each_contact in enumerate(contact_list):
                            contact_name = json_to_text(
                                each_contact, ["CentralContactName"])
                            contact_email = json_to_text(
                                each_contact, ["CentralContactEMail"])
                            contact_phone_without_ext = json_to_text(
                                each_contact, ["CentralContactPhone"])
                            contact_phone_ext = json_to_text(
                                each_contact, ["CentralContactPhoneExt"])

                            if contact_phone_ext.strip() != "":
                                contact_phone = contact_phone_without_ext + \
                                    f" ext {contact_phone_ext}"
                            else:
                                contact_phone = contact_phone_without_ext

                            if contact_idx == 0:
                                try:
                                    other_contact = json_to_text(
                                        contact_list[contact_idx+1], ["CentralContactName"])
                                except:
                                    other_contact = ""
                            else:
                                other_contact = json_to_text(
                                    contact_list[0], ["CentralContactName"])
                            data_list = [nct_id, url, posted_date, brief_title, official_title, enrollment,
                                         agency, contact_name, contact_phone, contact_email, other_contact, country, conditions]

                            save_csv(file_name, data_list)

                    # IF NO DUPLICATES FOUND
                    elif duplicate_status == "none":

                        first_investor_name = json_to_text(
                            investor_list[0], ["OverallOfficialName"])

                        for each_contact in contact_list:
                            contact_name = json_to_text(
                                each_contact, ["CentralContactName"])
                            contact_email = json_to_text(
                                each_contact, ["CentralContactEMail"])
                            contact_phone_without_ext = json_to_text(
                                each_contact, ["CentralContactPhone"])
                            contact_phone_ext = json_to_text(
                                each_contact, ["CentralContactPhoneExt"])

                            if contact_phone_ext.strip() != "":
                                contact_phone = contact_phone_without_ext + \
                                    f" ext {contact_phone_ext}"
                            else:
                                contact_phone = contact_phone_without_ext

                            other_contact = first_investor_name
                            data_list = [nct_id, url, posted_date, brief_title, official_title, enrollment,
                                         agency, contact_name, contact_phone, contact_email, other_contact, country, conditions]

                            save_csv(file_name, data_list)

                        for investor_idx, each_investor in enumerate(investor_list):

                            investor_name = json_to_text(
                                each_investor, ["OverallOfficialName"])
                            investor_email = json_to_text(
                                each_investor, ["OverallOfficialEMail"])
                            investor_phone = json_to_text(
                                each_investor, ["OverallOfficialPhone"])
                            if investor_idx == 0:
                                try:
                                    other_contact = json_to_text(
                                        investor_list[1], ["OverallOfficialName"])
                                except:
                                    other_contact = json_to_text(
                                        contact_list[0], ["CentralContactName"])
                            else:
                                other_contact = first_investor_name
                            data_list = [nct_id, url, posted_date, brief_title, official_title, enrollment,
                                         agency, investor_name, investor_phone, investor_email, other_contact, country, conditions]

                            save_csv(file_name, data_list)

                    # IF PARTIAL DUPLICATES FOUND
                    elif duplicate_status == "partial":

                        first_investor_name = json_to_text(
                            investor_list[0], ["OverallOfficialName"])

                        try:
                            second_investor_name = json_to_text(
                                investor_list[1], ["OverallOfficialName"])
                        except:
                            second_investor_name = ""

                        new_contact_list, new_investor_list = remove_duplicate_from_contact_list(
                            investor_list, contact_list)

                        for each_contact in new_contact_list:
                            contact_name = json_to_text(
                                each_contact, ["CentralContactName"])
                            contact_email = json_to_text(
                                each_contact, ["CentralContactEMail"])
                            contact_phone_without_ext = json_to_text(
                                each_contact, ["CentralContactPhone"])
                            contact_phone_ext = json_to_text(
                                each_contact, ["CentralContactPhoneExt"])

                            if contact_phone_ext.strip() != "":
                                contact_phone = contact_phone_without_ext + \
                                    f" ext {contact_phone_ext}"
                            else:
                                contact_phone = contact_phone_without_ext

                            other_contact = first_investor_name

                            data_list = [nct_id, url, posted_date, brief_title, official_title, enrollment,
                                         agency, contact_name, contact_phone, contact_email, other_contact, country, conditions]

                            save_csv(file_name, data_list)

                        for idx_inv, each_investor in enumerate(new_investor_list):
                            # json_to_text(
                            # contact_list[0], ["CentralContactName"])

                            investor_name = json_to_text(
                                each_investor, ["OverallOfficialName"])

                            investor_email = json_to_text(
                                each_investor, ["OverallOfficialEMail"])
                            investor_phone = json_to_text(
                                each_investor, ["OverallOfficialPhone"])
                            if idx_inv == 0:
                                if second_investor_name == "":
                                    try:
                                        other_contact = json_to_text(
                                            new_contact_list[0], ["CentralContactName"])
                                    except:
                                        other_contact = ""
                                else:
                                    other_contact = second_investor_name
                            else:
                                other_contact = first_investor_name

                            data_list = [nct_id, url, posted_date, brief_title, official_title, enrollment,
                                         agency, investor_name, investor_phone, investor_email, other_contact, country, conditions]

                            save_csv(file_name, data_list)

        print(f"Completed: {min_rank}-{max_rank}")


def scraper():
    output_file_name = f"{(datetime.now(timezone.utc) - timedelta(hours=8, days=1)).strftime('%Y-%m-%d')}-clinicaltrials-gov_temp.csv"
    # output_file_name = f"2023-04-18-clinicaltrials-gov_temp.csv"

    enrollment_filter = 40
    reciever_email = "alia6783@gmail.com"
    sender_email = "broadbreada@gmail.com"
    password = "scxmzgfifsurfkgk"

    email_validation_api_key = "live_b5be4e7aa50d05d4a67b"
    # email_validation_api_key = "test_ec6969802851c6fefad8"

    API = "https://clinicaltrials.gov/api/query/full_studies"

    save_csv(output_file_name, ["nct_id", "url", "posted date", "brief_title", "official_title", "enrollment",
             "sponsor", "f_name", "l_name", "phone", "email", "Other Study Contact", "country", "sequence-category", "condition", "email_for_country"], isFirst=True)
    get_all_data(API, output_file_name, enrollment_filter=enrollment_filter)

    output_file_name_final = post_process(
        output_file_name, email_validation_api_key)

    send_email(output_file_name, reciever_email, sender_email, password)

    update_email_database(file_name=output_file_name_final)


def main():
    scraper()


if __name__ == "__main__":
    main()
