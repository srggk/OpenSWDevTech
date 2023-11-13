import smtplib
from settings import *
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart


def send_email(to_email, title='Result of Poke Battle', results='Smth results of poke battle'):
    with open('templates/email_template.html', 'r') as file:
        html = str(file.read())
    html = html.format(title=title, results=results)
    part = MIMEText(html, "html")

    with open('static/images/vs.png', 'rb') as file:
        msgImage1 = MIMEImage(file.read(), name="battle.png")
    msgImage1.add_header('Content-ID', '<image1>')

    with open('static/images/pokemon.png', 'rb') as file:
        msgImage2 = MIMEImage(file.read(), name="pokelogo.png")
    msgImage2.add_header('Content-ID', '<image2>')

    message = MIMEMultipart()
    message['Subject'] = title
    message['From'] = MAIL_EMAIL
    message['To'] = to_email
    message.attach(part)
    message.attach(msgImage1)
    message.attach(msgImage2)

    try:
        server = smtplib.SMTP(MAIL_SERVER, int(MAIL_SMTP))
        server.starttls()
        server.login(MAIL_EMAIL, MAIL_PASSWORD)
        server.sendmail(MAIL_EMAIL, to_email, message.as_string())
        server.quit()
        print('email with result of the battle sent')
        return 0
    except Exception as e:
        print('error about email:', e)
        return e
