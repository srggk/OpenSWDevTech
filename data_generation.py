from settings import *
from db_models import Battle
import random, datetime
from faker import Faker
from dateutil.relativedelta import relativedelta

fake = Faker()


def generate_battles(quantity: int):
    poke_names = ['bulbasaur', 'ivysaur', 'venusaur', 'charmander', 'charmeleon', 'charizard', 'squirtle', 'wartortle', 'blastoise', 'caterpie']
    start_date = datetime.datetime.now() - relativedelta(months=1)

    for _ in range(quantity):
        battle = Battle(select_poke=random.choice(poke_names),
                        opponent_poke=random.choice(poke_names),
                        select_is_win=random.choice([True, False]),
                        quanity_rounds=random.randint(1, 20),
                        created_at=fake.date_time_between(start_date=start_date, end_date='now'))
        db.session.add(battle)
    
    try:
        db.session.commit()
        return 0
    except Exception as e:
        db.session.rollback()
        print('ERROR: generation random battles failed.')
        return -1
