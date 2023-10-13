from db import *
from flask import Flask, render_template, request, redirect, url_for, session
import requests
import random
import json

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = connect_string
db.init_app(app)

with open('config.json', 'r') as file:
    data=file.read()
configs = json.loads(data)
app.config['SECRET_KEY'] = configs['SECRET_KEY']

limit = 10


def get_poke(offset=0, limit=limit):
    url = f"https://pokeapi.co/api/v2/pokemon/?offset={offset}&limit={limit}"
    response = requests.get(url)

    if response.status_code == 200:
        data = response.json()  
        poke_list = data.get("results", [])
        poke_count = data['count']
        return poke_list, int(poke_count / limit + (1 if poke_count % limit > 0 else 0))
    else:
        print(response.status_code)
        return [], 0
    

def get_poke_info(poke_name):
    if poke_name:
        url = f"https://pokeapi.co/api/v2/pokemon/{poke_name.strip()}/"
        response = requests.get(url)

        if response.status_code == 200:
            data = response.json()

            stats = data['stats']
            hp = next((x for x in stats if x['stat']['name'] == 'hp'), None)
            attack = next((x for x in stats if x['stat']['name'] == 'attack'), None)
            defense = next((x for x in stats if x['stat']['name'] == 'defense'), None)
            special_attack = next((x for x in stats if x['stat']['name'] == 'special-attack'), None)
            special_defense = next((x for x in stats if x['stat']['name'] == 'special-defense'), None)
            speed = next((x for x in stats if x['stat']['name'] == 'speed'), None)

            return {
                'name': data['name'],
                'image': data['sprites']['front_default'],
                'hp': hp['base_stat'] if hp else 0,
                'attack': attack['base_stat'] if attack else 0,
                'defense': defense['base_stat'] if defense else 0,
                'special_attack': special_attack['base_stat'] if special_attack else 0,
                'special_defense': special_defense['base_stat'] if special_defense else 0,
                'speed': speed['base_stat'] if speed else 0,
            }
    else:
        return {}


@app.route('/')
def poke():
    page = 1
    if request.args.get('page'):
        if request.args.get('page').isdigit():
            page = int(request.args.get('page'))

    offset = (page - 1) * limit 
    poke_list, page_count = get_poke(offset)

    search_string = request.args.get('search_string', '')
    if search_string and search_string.strip() != '':
        poke_list, page_count = get_poke(offset=0, limit=page_count * limit)
        poke_list = [pkm for pkm in poke_list if search_string.strip() in pkm['name']]

        page_count = int(len(poke_list) / limit + (1 if len(poke_list) % limit > 0 else 0))
        poke_list = poke_list[offset : offset + limit]

    poke_list = [get_poke_info(pkm['name']) for pkm in poke_list]

    return render_template('index.html', 
                           pokemons=poke_list, 
                           search_string=search_string,
                           current=page, 
                           end=page_count)


@app.route('/poke/<string:poke_name>')
def poke_page(poke_name):
    poke = get_poke_info(poke_name)
    return render_template('info.html', poke=poke)


@app.route('/battle', methods=['GET', 'POST'])
def battle():
    if request.method == 'POST' and 'select_poke_name' in request.form:
        select_poke_name = request.form['select_poke_name']
        
        # clear old data about battle 
        session.clear()
    
        # save info about select poke
        select_poke = get_poke_info(select_poke_name)
        session['select_poke_name'] = select_poke_name
        session['select_poke_hp'] = select_poke['hp']
        session['select_poke_attack'] = select_poke['attack']

        # get total quantity pokes
        poke_list, page_count = get_poke(offset=0, limit=1)
        # get all poke names
        poke_list, page_count = get_poke(offset=0, limit=page_count * limit)

        # get only poke names and randow choice opponent poke
        poke_list_name = [poke['name'] for poke in poke_list]
        poke_list_name.remove(select_poke_name)
        opponent_poke_name = random.choice(poke_list_name)

        # save info about opponent poke
        opponent_poke = get_poke_info(opponent_poke_name)
        session['opponent_poke_name'] = opponent_poke_name
        session['opponent_poke_hp'] = opponent_poke['hp']
        session['opponent_poke_attack'] = opponent_poke['attack']

        return render_template('battle.html',
                               select_poke=select_poke,
                               opponent_poke=opponent_poke)
    
    return redirect(url_for('poke'))


def attack(select_number, opponent_number, is_attack):
    # user win
    if select_number % 2 == opponent_number % 2:
        if is_attack:
            session['opponent_poke_hp'] -= session['select_poke_attack']
        return True
    # opponent win
    else:
        if is_attack:
            session['select_poke_hp'] -= session['opponent_poke_attack']
        return False
    

def get_winner():
    if session['opponent_poke_hp'] <= 0:
        return session['select_poke_name']
    elif session['select_poke_hp'] <= 0:
        return session['opponent_poke_name']
    else:
        return None


@app.route('/battle/round', methods=['GET', 'POST'])
def battle_round():
    if request.method == 'POST' and 'select_number' in request.form:
        select_number = request.form['select_number']

        if select_number.isdigit():
            if int(select_number) > 0 and int(select_number) < 11:
                # save select_number
                session['select_number'] = int(select_number)
                
                # get random opponent number (when the page is reloaded the number will remain the same)
                if 'opponent_number' not in session:
                    opponent_number = random.randint(1, 10)
                    session['opponent_number'] = opponent_number

                # get info about select and opponent poke
                select_poke = get_poke_info(session['select_poke_name'])
                opponent_poke = get_poke_info(session['opponent_poke_name'])

                # get winner in round
                round_result = attack(select_number=session['select_number'],
                                      opponent_number=session['opponent_number'],
                                      is_attack=False)

                return render_template('battle.html',
                                        select_poke=select_poke,
                                        opponent_poke=opponent_poke,
                                        round_result=round_result)

        # select_number is incorrent
        return render_template('battle.html',
                                select_poke=get_poke_info(session['select_poke_name']), 
                                opponent_poke=get_poke_info(session['opponent_poke_name']),
                                winner=get_poke_info(get_winner()))
    
    return redirect(url_for('poke'))


@app.route('/battle/next-round')
def next_battle_round():
    if 'select_number' in session:
            round_result = attack(session['select_number'],
                                  session['opponent_number'],
                                  is_attack=True)
            session.pop('select_number', None)
            session.pop('opponent_number', None)
    return render_template('battle.html',
                            select_poke=get_poke_info(session['select_poke_name']), 
                            opponent_poke=get_poke_info(session['opponent_poke_name']),
                            winner=get_poke_info(get_winner()))


@app.route('/battle/finish')
def finish_battle():
    try:
        battle = Battle(select_poke=session['select_poke_name'],
                        opponent_poke=session['opponent_poke_name'],
                        select_is_win=get_winner() == session['select_poke_name'])
        db.session.add(battle)
        db.session.commit()
    except Exception:
        print("ERROR DB: Battle failed to add")
        db.session.rollback()
    finally:
        return redirect(url_for('poke'))


@app.route('/result-battes')
def result_battes():
    all_battles = Battle.query.all()
    return render_template('results.html',
                           battles=all_battles)


if __name__ == '__main__':
    app.run(debug=True)
