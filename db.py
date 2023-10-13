from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from db_models import *
import json

with open('config.json', 'r') as file:
    data=file.read()
configs = json.loads(data)

connect_string = f'postgresql://{configs["POSTGRESQL_USERNAME"]}:{configs["POSTGRESQL_PASSWORD"]}@{configs["POSTGRESQL_IP"]}:{configs["POSTGRESQL_PORT"]}/{configs["POSTGRESQL_DB_NAME"]}'

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = connect_string
db.init_app(app)


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
