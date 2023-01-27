from datetime import datetime, timedelta
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


def check_posted_date(posted_date):

    prev_day = (datetime.today() - timedelta(days=1)).strftime("%B %d, %Y")
    FMT = "%B %d, %Y"
    posted_date_formatted = datetime.strptime(posted_date, FMT)
    prev_day_formatted = datetime.strptime(prev_day, FMT)
    # print(
    #     f"Posted Date: {posted_date_formatted} |||| Prev Day: {prev_day_formatted}")
    if posted_date_formatted < prev_day_formatted:
        return False
    else:
        return True


def get_all_data(API, file_name, enrollment_filter=40):

    for i in range(1, 100):
        min_rank = 1+(i-1)*100
        max_rank = i*100
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

            isPostedDateGreater = check_posted_date(posted_date)

            if isPostedDateGreater:
                pass
            else:
                print(f"Posted date: {posted_date} is not greater!")
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
                enrollment = int(json_to_text(
                    each_study_data, ["ProtocolSection", "DesignModule", "EnrollmentInfo", "EnrollmentCount"]))

            except:
                enrollment = 0

            # FILTER ENTROLLMENT
            if enrollment < enrollment_filter:
                continue
            # contact_person_list = json_to_text(each_study_data, [
            #                                    "ProtocolSection", "ContactsLocationsModule", "CentralContactList", "CentralContact"])

            condition_list = json_to_text(each_study_data, [
                                          "ProtocolSection", "ConditionsModule", "ConditionList", "Condition"])
            conditions = "\n".join(condition_list)

            location_list = json_to_text(each_study_data, [
                "ProtocolSection", "ContactsLocationsModule", "LocationList", "Location"])
            if location_list != "":
                location = location_list[0]["LocationCountry"]

                if location == "United States":
                    country = "United States"
                elif location == "China" or location == "Iran" or location == "Russia":
                    continue
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
            print("--------------------------------")
            print(nct_id)

            if type(contact_module_list) == str:
                name, phone, email = "", "", ""
                data_list = [nct_id, url, brief_title, official_title, enrollment,
                             agency, name, phone, email, country, conditions]

                save_csv(file_name, data_list)
            else:
                for each_contact_module_key, each_contact_module_value in contact_module_list.items():

                    for each_contact_key, each_contact_value in each_contact_module_value.items():

                        name, phone, email = "", "", ""
                        for each_contact in each_contact_value:

                            for key, val in each_contact.items():

                                if "name" in key.lower():
                                    name = val

                                elif "phone" in key.lower() and "phoneext" not in key.lower():

                                    phone = val

                                elif "mail" in key.lower():
                                    email = val

                            if email == "":
                                continue
                            data_list = [nct_id, url, brief_title, official_title, enrollment,
                                         agency, name, phone, email, country, conditions]

                            save_csv(file_name, data_list)

        print(f"Completed: {min_rank}-{max_rank}")


def scraper():
    output_file_name = "output.csv"
    enrollment_filter = 40
    API = "https://clinicaltrials.gov/api/query/full_studies"

    save_csv(output_file_name, ["nct_id", "url", "brief_title", "official_title", "enrollment",
             "agency", "full_name", "phone", "email", "country", "condition"], isFirst=True)
    get_all_data(API, output_file_name, enrollment_filter=enrollment_filter)


def main():
    scraper()


if __name__ == "__main__":
    main()
