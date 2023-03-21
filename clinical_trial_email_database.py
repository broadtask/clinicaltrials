import csv
import pandas as pd
import datetime


def read_csv(file_name):

    with open(file_name, 'r', encoding="utf-8") as file:
        reader = csv.reader(file)
        rows = list(reader)
    return rows


def update_email_database(database_name="email_database.csv", file_name=""):

    today = datetime.datetime.now().strftime('%d-%m-%Y')

    email_database_data = read_csv(database_name)
    new_database = email_database_data.copy()

    recent_emails_all_datalist = read_csv(file_name)
    recent_emails_all_datalist.pop(0)

    for each_recent_email_data in recent_emails_all_datalist:
        matched = False
        each_recent_email = each_recent_email_data[11]
        if each_recent_email.strip() == "":
            continue

        for indx, each_email_on_database in enumerate(new_database):

            if each_recent_email.lower().strip() == each_email_on_database[0].lower().strip():

                matched = True
                email_database_data[indx][2] = today
                count_prev = each_email_on_database[3]
                email_database_data[indx][3] = int(count_prev)+1
                break
        if matched == False:
            data_list = [each_recent_email, today,
                         today, 1, each_recent_email_data[16]]
            email_database_data.append(data_list)

        with open(database_name, 'w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerows(email_database_data)
