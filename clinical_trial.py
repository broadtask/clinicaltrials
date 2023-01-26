from functools import reduce  # forward compatibility for Python 3
import operator
import os
import requests
from lxml import html
import csv
import json


def read_scrapped_data(previous_data_file):
    f = open(previous_data_file)
    return json.load(f)


def save_csv(filename, data_list, isFirst=False):
    """Save data to csv file"""

    if isFirst:
        if os.path.isfile(filename):
            os.remove(filename)
        else:
            pass

    with open(f'{filename}', "a", newline='', encoding='utf-8-sig') as fp:
        wr = csv.writer(fp, dialect='excel')
        wr.writerow(data_list)


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


def getFromDict(dataDict, mapList):
    return reduce(operator.getitem, mapList, dataDict)


def json_to_text(json_data, keys):

    try:
        return getFromDict(json_data, keys)

    except:
        return ""


def get_all_data(API, file_name):

    for i in range(1, 100):
        min_rank = 1+(i-1)*5
        max_rank = i*5
        print(min_rank, max_rank)
        params = {
            'expr': '',
            'min_rnk': min_rank,
            'max_rnk': max_rank,
            'fmt': 'json', }

        response = requests.get(API, params=params)
        all_study_data = response.json()["FullStudiesResponse"]["FullStudies"]

        for each_study in all_study_data:
            each_study_data = json_to_text(each_study, ["Study"])

            posted_date = json_to_text(each_study_data, [
                                       "ProtocolSection", "StatusModule", "StudyFirstPostDateStruct", "StudyFirstPostDate"])

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
            enrollment = json_to_text(
                each_study_data, ["ProtocolSection", "DesignModule", "EnrollmentInfo", "EnrollmentCount"])
            contact_person_list = json_to_text(each_study_data, [
                                               "ProtocolSection", "ContactsLocationsModule", "CentralContactList", "CentralContact"])

            condition_list = json_to_text(each_study_data, [
                                          "ProtocolSection", "ConditionsModule", "ConditionList", "Condition"])
            conditions = "\n".join(condition_list)

            location_list = json_to_text(each_study_data, [
                "ProtocolSection", "ContactsLocationsModule", "LocationList", "Location"])
            if location_list != "":
                location = location_list[0]["LocationCountry"]

                if location == "United States":
                    country = "United States"
                elif location == "":
                    country = ""
                else:
                    country = "Not United States"
            else:
                country = ""

            agency = json_to_text(each_study_data, [
                                  "ProtocolSection", "SponsorCollaboratorsModule", "LeadSponsor", "LeadSponsorName"])

            contact_module_list = json_to_text(each_study_data, [
                                               "ProtocolSection", "ContactsLocationsModule"])

            for each_contact_module_key, each_contact_module_value in contact_module_list.items():

                for each_contact in each_contact_module_value:

                    email = json_to_text(each_contact, ["CentralContactEMail"])
                    name = json_to_text(each_contact, ["CentralContactName"])
                    phone = json_to_text(each_contact, ["CentralContactPhone"])

                    data_list = [nct_id, url, brief_title, official_title, enrollment,
                                 agency, name, phone, email, country, conditions]

                    save_csv(file_name, data_list)

        print(f"Completed: {min_rank}-{max_rank}")


def scraper():
    output_file_name = "output.csv"
    API = "https://clinicaltrials.gov/api/query/full_studies"

    save_csv(output_file_name, ["nct_id", "url", "brief_title", "official_title", "enrollment",
             "agency", "full_name", "phone", "email", "country", "condition"], isFirst=True)
    all_data = get_all_data(API, output_file_name)


def main():
    scraper()


if __name__ == "__main__":
    main()
