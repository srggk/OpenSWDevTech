from db import *
from api import api
from send_email import send_email
from flask import Flask, render_template, request, redirect, url_for, session, abort
import requests
import json
import re

app = Flask(__name__)
app.register_blueprint(api)
app.config['SQLALCHEMY_DATABASE_URI'] = connect_string
db.init_app(app)

with open('config.json', 'r') as file:
    data=file.read()
configs = json.loads(data)
app.config['SECRET_KEY'] = configs['SECRET_KEY']


@app.route('/')
def poke():
    page = request.args.get('page')
    page = int(page) if page and page.isdigit() else 1
    search_string = request.args.get('search_string', '').strip()

    response = requests.get(f'{request.host_url}/api/v1/pokemon/list?page={page}&search_string={search_string}')
    if response.status_code == 200:
        return render_template('index.html', 
                                pokemons=response.json()['list'], 
                                search_string=search_string,
                                current=page, 
                                end=response.json()['page_count'])
    else:
        return render_template('index.html', 
                                pokemons=[],
                                search_string='',
                                page=0,
                                end=0)


@app.route('/poke/<string:poke_name>')
def poke_page(poke_name):
    response = requests.get(f'{request.host_url}/api/v1/pokemon/{poke_name}')
    if response.status_code == 200:
        return render_template('info.html', poke=response.json())
    else:
        abort(404)


@app.route('/battle', methods=['GET', 'POST'])
def battle():
    if request.method == 'POST' and 'select_poke_id' in request.form:
        select_poke_id = request.form['select_poke_id']

        # clear old data about battle 
        session.clear()
    
        # get randow opponent poke & info about select and opponent poke
        response = requests.get(f'{request.host_url}/api/v1/pokemon/random')
        if response.status_code == 200:
            opponent_poke_id = response.json()['id']

            response = requests.get(f'{request.host_url}/api/v1/fight?select_poke_id={select_poke_id}&opponent_poke_id={opponent_poke_id}')
            if response.status_code == 200:
                select_poke_info = response.json()['select_poke']
                opponent_poke_info = response.json()['opponent_poke']

                # save info
                session['select_poke_id'] = select_poke_info['id']
                session['select_poke_hp'] = select_poke_info['hp']
                session['select_poke_attack'] = select_poke_info['attack']
                session['opponent_poke_id'] = opponent_poke_info['id']
                session['opponent_poke_hp'] = opponent_poke_info['hp']
                session['opponent_poke_attack'] = opponent_poke_info['attack']

                return render_template('battle.html',
                               select_poke=select_poke_info,
                               opponent_poke=opponent_poke_info)    
    return redirect(url_for('poke'))


@app.route('/battle/round', methods=['GET', 'POST'])
def battle_round():
    if request.method == 'POST' and 'select_number' in request.form:
        select_number = request.form['select_number']

        # someone has already won, there are no more rounds
        if session['select_poke_hp'] <= 0 or session['opponent_poke_hp'] <= 0:
            return redirect(url_for('poke'))

        # get info about select & opponent poke
        response = requests.get(f'{request.host_url}/api/v1/fight?select_poke_id={session["select_poke_id"]}&opponent_poke_id={session["opponent_poke_id"]}')
        if response.status_code == 200:
            select_poke_info = response.json()['select_poke']
            opponent_poke_info = response.json()['opponent_poke']
        else:
            abort(503)

        # checking valid selected number (from user)
        if select_number.isdigit() and int(select_number) > 0 and int(select_number) < 11:
            # next step & get new info about battle
            url = f'{request.host_url}/api/v1/fight/{select_number}'
            response = requests.post(url, json={
                'select_poke': {
                    'id': session['select_poke_id'],
                    'hp': session['select_poke_hp'],
                    'attack': session['select_poke_attack'],
                },
                'opponent_poke': {
                    'id': session['opponent_poke_id'],
                    'hp': session['opponent_poke_hp'],
                    'attack': session['opponent_poke_attack'],
                },
            })
            
            if response.status_code == 200:
                session['select_poke_hp'] = response.json()['select_poke']['hp']
                session['opponent_poke_hp'] = response.json()['opponent_poke']['hp']
                winner = response.json()['winner']

                # add info about round to history
                if 'history' not in session:
                    session['history'] = []
                session['history'].append(response.json()['round'])

                # check if the battle is over 
                if winner:
                    try:
                        battle = Battle(select_poke=session['select_poke_id'],
                                        opponent_poke=session['opponent_poke_id'],
                                        select_is_win=winner == session['select_poke_id'],
                                        quanity_rounds=len(session['history']))
                        db.session.add(battle)
                        db.session.commit()
                    except Exception:
                        print("ERROR DB: Battle failed to add")
                        db.session.rollback()

                print(winner)
                
                return render_template('battle.html',
                            select_poke=select_poke_info, 
                            opponent_poke=opponent_poke_info,
                            rounds_result=session['history'],
                            winner=winner)
            else:
                abort(503)
        else:
            return render_template('battle.html',
                                    select_poke=select_poke_info, 
                                    opponent_poke=opponent_poke_info)
    return redirect(url_for('poke'))


def is_valid_email(email):
    regex = r'\b[A-Za-z0-9._-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b'
    return True if re.fullmatch(regex, email) else False


@app.route('/battle/fast', methods=['GET', 'POST'])
def fast_battle():
    if request.method == 'POST':
        if 'res_battle_email' in request.form and is_valid_email(request.form['res_battle_email']):
            email = request.form['res_battle_email']
            abort(404)
        else:
            abort(404)
    return redirect(url_for('poke'))


@app.route('/result-battes')
def result_battes():
    try:
        all_battles = Battle.query.order_by(Battle.created_at.desc()).all()
        return render_template('results.html',
                                battles=all_battles)
    except:
        abort(503)


if __name__ == '__main__':
    app.run(debug=True)
