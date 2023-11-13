from os import environ
from dotenv import load_dotenv
load_dotenv(dotenv_path=".env.docker")
# load_dotenv(dotenv_path=".env.local")

SECRET_KEY = environ.get('SECRET_KEY')
DEBUG = environ.get('WEB_DEBUG') == "True"
WEB_IP= environ.get('WEB_IP')
WEB_PORT= environ.get('WEB_PORT')

POSTGRESQL_IP = environ.get('POSTGRESQL_IP')
POSTGRESQL_PORT = environ.get('POSTGRESQL_PORT')
POSTGRESQL_USERNAME =  environ.get('POSTGRESQL_USERNAME')
POSTGRESQL_PASSWORD = environ.get('POSTGRESQL_PASSWORD')
POSTGRESQL_DB_NAME = environ.get('POSTGRESQL_DB_NAME')

MAIL_SERVER = environ.get('MAIL_SERVER')
MAIL_EMAIL = environ.get('MAIL_EMAIL')
MAIL_PASSWORD = environ.get('MAIL_PASSWORD')
MAIL_SMTP = environ.get('MAIL_SMTP')

FTP_HOST = environ.get('FTP_HOST')
FTP_USER = environ.get('FTP_USER')
FTP_PASSWORD = environ.get('FTP_PASSWORD')

CACHE_TYPE = environ.get('CACHE_TYPE')
CACHE_REDIS_HOST = environ.get('CACHE_REDIS_HOST')
CACHE_REDIS_PORT = environ.get('CACHE_REDIS_PORT')
CACHE_REDIS_DB = environ.get('CACHE_REDIS_DB')