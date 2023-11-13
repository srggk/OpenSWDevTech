from settings import *
from db_models import *
from api import api
from send_email import send_email
from flask import Flask, render_template, request, redirect, url_for, session, abort, flash
from flask_caching import Cache
import redis
import requests
import re

app = Flask(__name__)
app.register_blueprint(api)
app.config['SQLALCHEMY_DATABASE_URI'] = f'postgresql://{POSTGRESQL_USERNAME}:{POSTGRESQL_PASSWORD}@{POSTGRESQL_IP}:{POSTGRESQL_PORT}/{POSTGRESQL_DB_NAME}'
db.init_app(app)
app.config['SECRET_KEY'] = SECRET_KEY
app.config['CACHE_TYPE'] = CACHE_TYPE
app.config['CACHE_REDIS_HOST'] = CACHE_REDIS_HOST
app.config['CACHE_REDIS_PORT'] = CACHE_REDIS_PORT
app.config['CACHE_REDIS_DB'] = CACHE_REDIS_DB
cache = Cache(app=app)
cache.init_app(app)
redis_client = redis.Redis(host=CACHE_REDIS_HOST,
                           port=CACHE_REDIS_PORT,
                           db=CACHE_REDIS_DB)


@app.route('/')
@cache.cached(timeout=60, key_prefix='pokes', query_string=True)
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
@cache.cached(timeout=60, key_prefix='poke_info', query_string=True)
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


def results_battle_to_string(select_poke, opponent_poke, rounds, winner):
    res = f'\nBATTLE {select_poke["name"]} VS {opponent_poke["name"]}\nRESULT: {select_poke["name"] if winner == select_poke["id"] else opponent_poke["name"]} wins.\n\nROUNDS:'
    for i, round in enumerate(rounds):
        round_winner = select_poke["name"] if round['winner_id'] == select_poke["id"] else opponent_poke["name"]
        res += f'\n\n#{i+1}: WIN {round_winner}\nY-N={round["select_number"]}   Y-HP={round["select_poke_hp"]}   O-N={round["opponent_number"]}   O-HP={round["opponent_poke_hp"]}'
    return res + '\n\n'


@app.route('/battle/fast', methods=['GET', 'POST'])
def fast_battle():
    if request.method == 'POST':
        if 'select_poke_id' in session and 'opponent_poke_id' in session:

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

            # get result of the battle (fast)
            response = requests.get(f'{request.host_url}/api/v1/fight/fast?select_poke_id={session["select_poke_id"]}&opponent_poke_id={session["opponent_poke_id"]}')
            if response.status_code == 200:
                session['select_poke_hp'] = response.json()['select_poke']['hp']
                session['opponent_poke_hp'] = response.json()['opponent_poke']['hp']
                rounds = response.json()['rounds']
                winner = response.json()['winner']
                
                # record result of the battle to db
                try:
                    battle = Battle(select_poke=session['select_poke_id'],
                                    opponent_poke=session['opponent_poke_id'],
                                    select_is_win=winner == session['select_poke_id'],
                                    quanity_rounds=len(rounds))
                    db.session.add(battle)
                    db.session.commit()
                except Exception:
                    print("ERROR DB: Battle failed to add")
                    db.session.rollback()
                
                # send result to email if need
                if 'res_battle_email' in request.form and is_valid_email(request.form['res_battle_email']):
                    email = request.form['res_battle_email']
                    battle_result = results_battle_to_string(select_poke=select_poke_info,
                                                             opponent_poke=opponent_poke_info,
                                                             rounds=rounds,
                                                             winner=winner)
                    send_email(to_email=email,
                               results=battle_result.replace('\n', '<br/>'))

                return render_template('battle.html',
                            select_poke=select_poke_info, 
                            opponent_poke=opponent_poke_info,
                            rounds_result=rounds,
                            winner=winner)
            else:
                abort(503)
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
    with app.app_context():
        db.create_all()
    app.run(host=WEB_IP, port=WEB_PORT, debug=DEBUG)
