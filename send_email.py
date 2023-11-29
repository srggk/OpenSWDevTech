import smtplib
from settings import *
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart


def send_email(to_email, theme, content, username=None):
    theme_valid = ['battle_result', 'confirm_login', 'change_password']
    if theme not in theme_valid:
        raise ValueError(f"theme can be only {theme_valid}")

    appeal = username if username else 'Pokemon lover'
    title = ''
    start = ''
    end = ''
    if theme == theme_valid[0]:
        title = 'Result of Poke Battle | PokeWebSite'
        start = 'You asked me to send this to you via email.'
        end = 'You received this letter because your email was listed on a Pokemon website. If you have not done this, just ignore this letter.'
    elif theme == theme_valid[1]:
        title = 'Confirm your login | PokeWebSite'
        start = 'Please confirm your login to your account on the Pokemon website. Enter this code in the authorization form field:'
        end = 'You received this letter because you filled out the registration form on the site. If you have not done this, just ignore this letter.'
    elif theme == theme_valid[2]:
        title = 'Change your password | PokeWebSite'
        start = 'You have forgotten the password to access your account on the Pokemon website and have applied to have it restored. You can change it by entering the verification code below and your new password.'
        end = 'You received this email because you filled out the password change form on the Pokemon website. If you have not done this, just ignore this letter.'

    # get html template
    with open('templates/email_template.html', 'r') as file:
        html = str(file.read())
    html = html.format(title=str(title),
                       appeal=str(appeal),
                       start=str(start),
                       content=str(content),
                       end=str(end))
    part = MIMEText(html, "html")

    # add images
    msgImage_down_pokelogo = None
    with open('static/images/pokemon.png', 'rb') as file:
        msgImage_down_pokelogo = MIMEImage(file.read(), name="pokelogo.png")
    msgImage_down_pokelogo.add_header('Content-ID', '<image2>')

    msgImage_up_battle = None
    with open('static/images/vs.png', 'rb') as file:
        msgImage_up_battle = MIMEImage(file.read(), name="battle.png")
    msgImage_up_battle.add_header('Content-ID', '<image1>')

    msgImage_up_pokelogomini = None
    with open('static/images/pokemon_mini.png', 'rb') as file:
        msgImage_up_pokelogomini = MIMEImage(file.read(), name="pokelogo_mini.png")
    msgImage_up_pokelogomini.add_header('Content-ID', '<image1>')
    
    # union message parts
    message = MIMEMultipart()
    message['Subject'] = title
    message['From'] = MAIL_EMAIL
    message['To'] = to_email
    message.attach(part)
    if theme == theme_valid[0]:
        message.attach(msgImage_up_battle)
    elif theme == theme_valid[1] or theme == theme_valid[2]:
        message.attach(msgImage_up_pokelogomini)
    message.attach(msgImage_down_pokelogo)

    # send email
    try:
        server = smtplib.SMTP(MAIL_SERVER, int(MAIL_SMTP))
        server.starttls()
        server.login(MAIL_EMAIL, MAIL_PASSWORD)
        server.sendmail(MAIL_EMAIL, to_email, message.as_string())
        server.quit()
        print(f"Email successfully send to {to_email}")
        return 0
    except Exception as e:
        print(f"Error with sending email to {to_email}: {e}")
        return e
