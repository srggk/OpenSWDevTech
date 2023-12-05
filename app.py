from settings import *
from db_models import User, Battle
from api import api
from auth import auth
from send_email import send_email
from data_generation import generate_battles
from flask import Flask, render_template, request, redirect, url_for, session, abort, flash
from flask_login import current_user, login_required
import requests
import re

app = Flask(__name__)
app.register_blueprint(api)
app.register_blueprint(auth)
app.config['SECRET_KEY'] = SECRET_KEY

app.config['SQLALCHEMY_DATABASE_URI'] = f'postgresql://{POSTGRESQL_USERNAME}:{POSTGRESQL_PASSWORD}@{POSTGRESQL_IP}:{POSTGRESQL_PORT}/{POSTGRESQL_DB_NAME}'
db.init_app(app)

app.config['CACHE_TYPE'] = CACHE_TYPE
app.config['CACHE_REDIS_HOST'] = CACHE_REDIS_HOST
app.config['CACHE_REDIS_PORT'] = CACHE_REDIS_PORT
app.config['CACHE_REDIS_DB'] = CACHE_REDIS_DB
cache.init_app(app)

csrf.init_app(app)
bcrypt.init_app(app)
login_manager.init_app(app)
login_manager.login_view = 'auth.login'

@app.route('/')
@cache.cached(timeout=1, key_prefix='pokes', query_string=True)
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
@cache.cached(timeout=30, key_prefix='poke_info', query_string=True)
def poke_page(poke_name):
    response = requests.get(f'{request.host_url}/api/v1/pokemon/{poke_name}')
    if response.status_code == 200:
        return render_template('info.html', poke=response.json())
    else:
        abort(404)


@app.route('/poke/save', methods=['GET', 'POST'])
def poke_page_save():
    if request.method == 'POST' and 'poke_id' in request.form:
        poke_id = request.form['poke_id']
        if poke_id.isdigit():
            response = requests.post(f'{request.host_url}/api/v1/pokemon/save/{poke_id}')
            if response.status_code == 201:
                flash('File with info about Poke was successfully generated and saved.', 'info')
                return redirect(url_for('poke_page', poke_name=response.json()['poke_name']))
            elif response.status_code == 503:
                flash('File with info about Poke was not generated and saved.', 'error')
                return redirect(url_for('poke_page', poke_name=response.json()['poke_name']))
    return redirect(url_for('poke'))


@app.route('/battle', methods=['GET', 'POST'])
def battle():
    if request.method == 'POST' and 'select_poke_id' in request.form:
        select_poke_id = request.form['select_poke_id']

        # clear old data about battle 
        if 'data_battle' in session:
            session.pop('data_battle')
        if 'data_battle_history' in session:
            session.pop('data_battle_history')
    
        # get randow opponent poke & info about select and opponent poke
        response = requests.get(f'{request.host_url}/api/v1/pokemon/random')
        if response.status_code == 200:
            opponent_poke_id = response.json()['id']

            response = requests.get(f'{request.host_url}/api/v1/fight?select_poke_id={select_poke_id}&opponent_poke_id={opponent_poke_id}')
            if response.status_code == 200:
                select_poke_info = response.json()['select_poke']
                opponent_poke_info = response.json()['opponent_poke']

                # save info
                session['data_battle'] = {'select_poke_id': select_poke_info['id'],
                                          'select_poke_name': select_poke_info['name'],
                                          'select_poke_hp': select_poke_info['hp'],
                                          'select_poke_attack': select_poke_info['attack'],
                                          'opponent_poke_id': opponent_poke_info['id'],
                                          'opponent_poke_name': opponent_poke_info['name'],
                                          'opponent_poke_hp': opponent_poke_info['hp'],
                                          'opponent_poke_attack': opponent_poke_info['attack']}

                return render_template('battle.html',
                               select_poke=select_poke_info,
                               opponent_poke=opponent_poke_info)    
    return redirect(url_for('poke'))


@app.route('/battle/round', methods=['GET', 'POST'])
def battle_round():
    if request.method == 'POST' and 'select_number' in request.form and 'data_battle' in session:
        select_number = request.form['select_number']

        # someone has already won, there are no more rounds
        if session['data_battle']['select_poke_hp'] <= 0 or session['data_battle']['opponent_poke_hp'] <= 0:
            return redirect(url_for('poke'))

        # get info about select & opponent poke
        response = requests.get(f'{request.host_url}/api/v1/fight?select_poke_id={session["data_battle"]["select_poke_id"]}&opponent_poke_id={session["data_battle"]["opponent_poke_id"]}')
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
                    'id': session['data_battle']['select_poke_id'],
                    'hp': session['data_battle']['select_poke_hp'],
                    'attack': session['data_battle']['select_poke_attack'],
                },
                'opponent_poke': {
                    'id': session['data_battle']['opponent_poke_id'],
                    'hp': session['data_battle']['opponent_poke_hp'],
                    'attack': session['data_battle']['opponent_poke_attack'],
                },
            })
            
            if response.status_code == 200:
                session['data_battle']['select_poke_hp'] = response.json()['select_poke']['hp']
                session['data_battle']['opponent_poke_hp'] = response.json()['opponent_poke']['hp']
                winner = response.json()['winner']

                # add info about round to history
                if 'data_battle_history' not in session:
                    session['data_battle_history'] = []
                session['data_battle_history'].append(response.json()['round'])

                # check if the battle is over 
                if winner:                    
                    record_battle_result_to_db(user_id=current_user.id if current_user.is_authenticated else None,
                                               select_poke=session['data_battle']['select_poke_name'],
                                               opponent_poke=session['data_battle']['opponent_poke_name'],
                                               select_is_win=winner == session['data_battle']['select_poke_id'],
                                               quanity_rounds=len(session['data_battle_history']))

                print(winner)
                
                return render_template('battle.html',
                            select_poke=select_poke_info, 
                            opponent_poke=opponent_poke_info,
                            rounds_result=session['data_battle_history'],
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


def results_battle_to_string(select_poke, opponent_poke, rounds, winner):
    res = f'\nBATTLE {select_poke["name"]} VS {opponent_poke["name"]}\nRESULT: {select_poke["name"] if winner == select_poke["id"] else opponent_poke["name"]} wins.\n\nROUNDS:'
    for i, round in enumerate(rounds):
        round_winner = select_poke["name"] if round['winner_id'] == select_poke["id"] else opponent_poke["name"]
        res += f'\n\n#{i+1}: WIN {round_winner}\nY-N={round["select_number"]}   Y-HP={round["select_poke_hp"]}   O-N={round["opponent_number"]}   O-HP={round["opponent_poke_hp"]}'
    return res + '\n\n'


@app.route('/battle/fast', methods=['GET', 'POST'])
def fast_battle():
    if request.method == 'POST':
        if 'data_battle' in session and 'select_poke_id' in session['data_battle'] and 'opponent_poke_id' in session['data_battle']:

            # someone has already won, there are no more rounds
            if session['data_battle']['select_poke_hp'] <= 0 or session['data_battle']['opponent_poke_hp'] <= 0:
                return redirect(url_for('poke'))

            # get info about select & opponent poke
            response = requests.get(f'{request.host_url}/api/v1/fight?select_poke_id={session["data_battle"]["select_poke_id"]}&opponent_poke_id={session["data_battle"]["opponent_poke_id"]}')
            if response.status_code == 200:
                select_poke_info = response.json()['select_poke']
                opponent_poke_info = response.json()['opponent_poke']
            else:
                abort(503)

            # get result of the battle (fast)
            response = requests.get(f'{request.host_url}/api/v1/fight/fast?select_poke_id={session["data_battle"]["select_poke_id"]}&opponent_poke_id={session["data_battle"]["opponent_poke_id"]}')
            if response.status_code == 200:
                session['data_battle']['select_poke_hp'] = response.json()['select_poke']['hp']
                session['data_battle']['opponent_poke_hp'] = response.json()['opponent_poke']['hp']
                rounds = response.json()['rounds']
                winner = response.json()['winner']
                
                # record result of the battle to db
                record_battle_result_to_db(user_id=current_user.id if current_user.is_authenticated else None,
                                           select_poke=session['data_battle']['select_poke_name'],
                                           opponent_poke=session['data_battle']['opponent_poke_name'],
                                           select_is_win=winner == session['data_battle']['select_poke_id'],
                                           quanity_rounds=len(rounds))
                
                # send result to email if need
                if 'res_battle_email' in request.form and is_valid_email(request.form['res_battle_email']) and MAIL_ENABLED:
                    email = request.form['res_battle_email']
                    battle_result = results_battle_to_string(select_poke=select_poke_info,
                                                             opponent_poke=opponent_poke_info,
                                                             rounds=rounds,
                                                             winner=winner)
                    send_email(to_email=email,
                               theme='battle_result',
                               content=battle_result.replace('\n', '<br/>'), 
                               username=current_user.name if current_user.is_authenticated else None)

                return render_template('battle.html',
                            select_poke=select_poke_info, 
                            opponent_poke=opponent_poke_info,
                            rounds_result=rounds,
                            winner=winner)
            else:
                abort(503)
    return redirect(url_for('poke'))


def record_battle_result_to_db(user_id, select_poke, opponent_poke, select_is_win, quanity_rounds):
    try:
        battle = Battle(user_id=user_id,
                        select_poke=select_poke,
                        opponent_poke=opponent_poke,
                        select_is_win=select_is_win,
                        quanity_rounds=quanity_rounds)
        db.session.add(battle)
        db.session.commit()
    except Exception as e:
        print("ERROR DB: Battle failed to add\n", e)
        db.session.rollback()


@app.route('/result-battes')
def result_battes():
    try:
        all_battles = Battle.query.order_by(Battle.created_at.desc()).all()
        return render_template('results.html',
                                battles=all_battles)
    except:
        abort(503)


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        if Battle.query.count() < 1000:
            generate_battles(1000)
    app.run(host=WEB_IP, port=WEB_PORT, debug=DEBUG)
