import smtplib
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email.utils import COMMASPACE
from email import encoders


def send_email(file_name, reciever_email, sender_email, password):
    smtp_server = "smtp.gmail.com"
    port = 587  # For starttls

    # Create a secure SSL context
    context = ssl.create_default_context()

    # Try to log in to server and send email
    try:
        server = smtplib.SMTP(smtp_server, port)
        server.ehlo()  # Can be omitted
        server.starttls(context=context)  # Secure the connection
        server.ehlo()  # Can be omitted
        server.login(sender_email, password)
        FILENAME = file_name
        FILEPATH = file_name

        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = reciever_email
        msg['Subject'] = "Generated CSV of Clinical Trial"

        part = MIMEBase('application', "octet-stream")
        part.set_payload(open(FILEPATH, "rb").read())
        encoders.encode_base64(part)
        part.add_header('Content-Disposition', 'attachment',
                        filename=FILENAME)  # or
        # part.add_header('Content-Disposition', 'attachment; filename="attachthisfile.csv"')
        msg.attach(part)

        server.sendmail(sender_email, reciever_email, msg.as_string())
        print("Email sent successfully!")
    except Exception as e:
        # Print any error messages to stdout
        print(e)
    finally:
        server.quit()
