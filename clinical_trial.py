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
        data_set = data_list

    else:
        try:
            name = data_list[6].split(",")[0]
        except:
            name = ""
        try:
            other_name = data_list[9].strip().split(",")[0]

        except:
            other_name = ""

        name_splitted = name.split(" ")

        if len(name_splitted) > 1:
            name_splitted = [s.strip() for s in name_splitted if len(
                s.strip().replace(".", "")) != 1]

            first_name = name_splitted[0]
            name_splitted.pop(0)
            last_name = " ".join(name_splitted)
        elif len(name_splitted) == 1:
            first_name = name_splitted[0]
            last_name = ""
        else:
            return

        data_set = [data_list[0], data_list[1], data_list[2], data_list[3], data_list[4],
                    data_list[5], first_name, last_name, data_list[7], data_list[8], other_name, data_list[10], data_list[11]]

    with open(f'{filename}', "a", newline='', encoding='utf-8-sig') as fp:
        wr = csv.writer(fp, dialect='excel')
        wr.writerow(data_set)


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


def get_all_data(API, file_name, enrollment_filter=40):

    range_number = 100

    for i in range(1, range_number):
        min_rank = 1+(i-1)*range_number
        max_rank = i*range_number
        print(min_rank, max_rank)
        # params = {
        #     'expr': 'NCT05710224',

        #     'fmt': 'json', }
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

            isPostedDateGreater, prev_day = check_posted_date(posted_date)

            if isPostedDateGreater:
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

            contact_list = json_to_text(
                contact_module_list, ["CentralContactList", "CentralContact"])
            investor_list = json_to_text(
                contact_module_list, ["OverallOfficialList", "OverallOfficial"])

            print("--------------------------------")
            print(nct_id)

            if type(contact_module_list) == str:
                name, phone, email, other_contact = "", "", "", ""
                # data_list = [nct_id, url, brief_title, official_title, enrollment,
                #              agency, name, phone, email, other_contact, country, conditions]

                # save_csv(file_name, data_list)
            else:

                # NEED TO CHANGE HERE
                # IF One Contact and no Investigators
                if len(contact_list) == 1 and len(investor_list) < 1:

                    for contact_idx, each_contact in enumerate(contact_list):

                        contact_name = json_to_text(
                            each_contact, ["CentralContactName"])
                        contact_email = json_to_text(
                            each_contact, ["CentralContactEMail"])
                        contact_phone = json_to_text(
                            each_contact, ["CentralContactPhone"])
                        other_contact = ""

                        data_list = [nct_id, url, brief_title, official_title, enrollment,
                                     agency, contact_name, contact_phone, contact_email, other_contact, country, conditions]

                        save_csv(file_name, data_list)

                # IF More Than One Study Contacts and no Investigator
                elif len(contact_list) > 1 and len(investor_list) <= 0:

                    for contact_idx, each_contact in enumerate(contact_list):

                        contact_name = json_to_text(
                            each_contact, ["CentralContactName"])
                        contact_email = json_to_text(
                            each_contact, ["CentralContactEMail"])
                        contact_phone = json_to_text(
                            each_contact, ["CentralContactPhone"])
                        if contact_idx == 0:
                            other_contact = json_to_text(
                                contact_list[contact_idx+1], ["CentralContactName"])
                        else:
                            other_contact = json_to_text(
                                contact_list[0], ["CentralContactName"])

                        data_list = [nct_id, url, brief_title, official_title, enrollment,
                                     agency, contact_name, contact_phone, contact_email, other_contact, country, conditions]

                        save_csv(file_name, data_list)

                # IF One or more investigators and one or more contacts
                elif len(contact_list) >= 1 and len(investor_list) >= 1:

                    uniq_list_of_contacts, duplicate_status = get_uniq_list_of_contacts(
                        contact_list, investor_list)

                    if duplicate_status == "all same":

                        for contact_idx, each_contact in enumerate(contact_list):
                            contact_name = json_to_text(
                                each_contact, ["CentralContactName"])
                            contact_email = json_to_text(
                                each_contact, ["CentralContactEMail"])
                            contact_phone = json_to_text(
                                each_contact, ["CentralContactPhone"])
                            if contact_idx == 0:
                                try:
                                    other_contact = json_to_text(
                                        contact_list[contact_idx+1], ["CentralContactName"])
                                except:
                                    other_contact = ""
                            else:
                                other_contact = json_to_text(
                                    contact_list[0], ["CentralContactName"])
                            data_list = [nct_id, url, brief_title, official_title, enrollment,
                                         agency, contact_name, contact_phone, contact_email, other_contact, country, conditions]

                            save_csv(file_name, data_list)

                    elif duplicate_status == "none":

                        first_investor_name = json_to_text(
                            investor_list[0], ["OverallOfficialName"])

                        for each_contact in contact_list:
                            contact_name = json_to_text(
                                each_contact, ["CentralContactName"])
                            contact_email = json_to_text(
                                each_contact, ["CentralContactEMail"])
                            contact_phone = json_to_text(
                                each_contact, ["CentralContactPhone"])
                            other_contact = first_investor_name
                            data_list = [nct_id, url, brief_title, official_title, enrollment,
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
                            data_list = [nct_id, url, brief_title, official_title, enrollment,
                                         agency, investor_name, investor_phone, investor_email, other_contact, country, conditions]

                            save_csv(file_name, data_list)

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
                            contact_phone = json_to_text(
                                each_contact, ["CentralContactPhone"])
                            other_contact = first_investor_name

                            data_list = [nct_id, url, brief_title, official_title, enrollment,
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

                                    other_contact = json_to_text(
                                        new_investor_list[0], ["CentralContactName"])
                                else:
                                    other_contact = second_investor_name
                            data_list = [nct_id, url, brief_title, official_title, enrollment,
                                         agency, investor_name, investor_phone, investor_email, other_contact, country, conditions]

                            save_csv(file_name, data_list)

                # for each_contact_module_key, each_contact_module_value in contact_module_list.items():

                #     for each_contact_key, each_contact_value in each_contact_module_value.items():

                #         name, phone, email = "", "", ""
                #         for each_contact in each_contact_value:

                #             for key, val in each_contact.items():

                #                 if "name" in key.lower():
                #                     name = val

                #                 elif "phone" in key.lower() and "phoneext" not in key.lower():

                #                     phone = val

                #                 elif "mail" in key.lower():
                #                     email = val

                #             if email == "":
                #                 continue
                #             data_list = [nct_id, url, brief_title, official_title, f"{enrollment:,}",
                #                          agency, name, phone, email, country, conditions]

                #             save_csv(file_name, data_list)

        print(f"Completed: {min_rank}-{max_rank}")


def scraper():
    output_file_name = f"{datetime.today().strftime('%Y-%m-%d')}-clinicaltrials-gov.csv"
    enrollment_filter = 40
    API = "https://clinicaltrials.gov/api/query/full_studies"

    save_csv(output_file_name, ["nct_id", "url", "brief_title", "official_title", "enrollment",
             "agency", "f_name", "l_name", "phone", "email", "Other Study Contact", "country", "condition"], isFirst=True)
    get_all_data(API, output_file_name, enrollment_filter=enrollment_filter)


def main():
    scraper()


if __name__ == "__main__":
    main()
