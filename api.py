from settings import *
from flask import Blueprint, request, make_response, jsonify, abort
import requests, random, io, ftplib
from datetime import date

api = Blueprint('api', __name__, template_folder='templates')
csrf.exempt(api)

@api.route('/api/v1/pokemon/<id>', methods=['GET'])
def api_pokemon_from_id(id):
    if id:
        url = f"https://pokeapi.co/api/v2/pokemon/{id}/"
        response = requests.get(url)

        if (response.status_code == 200):
            data = response.json()

            stats = data['stats']
            hp = next((x for x in stats if x['stat']['name'] == 'hp'), None)
            attack = next((x for x in stats if x['stat']['name'] == 'attack'), None)
            defense = next((x for x in stats if x['stat']['name'] == 'defense'), None)
            special_attack = next((x for x in stats if x['stat']['name'] == 'special-attack'), None)
            special_defense = next((x for x in stats if x['stat']['name'] == 'special-defense'), None)
            speed = next((x for x in stats if x['stat']['name'] == 'speed'), None)

            result = {
                'id': data['id'],
                'name': data['name'],
                'image': data['sprites']['front_default'],
                'hp': hp['base_stat'] if hp else 0,
                'attack': attack['base_stat'] if attack else 0,
                'defense': defense['base_stat'] if defense else 0,
                'special_attack': special_attack['base_stat'] if special_attack else 0,
                'special_defense': special_defense['base_stat'] if special_defense else 0,
                'speed': speed['base_stat'] if speed else 0,
            }
            return make_response(result, 200)
        else:
            return make_response({'error': 'Not Found'}, 404)
    return make_response({'error': 'Not Found'}, 404)


@api.route('/api/v1/pokemon/list', methods=['GET'])
def api_pokemon_list():
    page = request.args.get('page')
    page = int(page) if page and page.isdigit() else 1
    limit = request.args.get('limit')
    limit = int(limit) if limit and limit.isdigit() else 10
    search_string = request.args.get('search_string', '').strip()

    offset = (page - 1) * limit
    url = f"https://pokeapi.co/api/v2/pokemon/?offset={offset}&limit={limit}"
    response = requests.get(url)

    if response.status_code == 200:
        data = response.json()
        poke_list = data.get('results', [])
        poke_count = data['count']
        page_count = int(poke_count / limit + (1 if poke_count % limit > 0 else 0))

        print(search_string)
        if search_string != '':
            url = f"https://pokeapi.co/api/v2/pokemon/?limit={poke_count}"
            response = requests.get(url)
            
            if response.status_code == 200:
                data = response.json()
                poke_list = data.get('results', [])
                poke_list = [pkm for pkm in poke_list if search_string in pkm['name']]
                page_count = int(len(poke_list) / limit + (1 if len(poke_list) % limit > 0 else 0))
                poke_list = poke_list[offset : offset + limit]
            else:
                return make_response({'error': 'Not Found'}, 404)
        
        poke_list = [api_pokemon_from_id(pkm['name']).json for pkm in poke_list]
        return make_response({'page_count': page_count, 'list': poke_list}, 200)
    else:
        return make_response({'error': 'Not Found'}, 404)


@api.route('/api/v1/pokemon/random', methods=['GET'])
def api_pokemon_random():
    url = f"https://pokeapi.co/api/v2/pokemon/?limit=1"
    response = requests.get(url)

    if response.status_code == 200:
        data = response.json()
        poke_count = data['count']
        random_id = random.randint(1, poke_count)
        return make_response({'id': random_id}, 200)
    else:
        return make_response({'error': 'Not Found'}, 404)


@api.route('/api/v1/fight', methods=['GET'])
def api_fight():
    select_poke_id = request.args.get('select_poke_id')
    opponent_poke_id = request.args.get('opponent_poke_id')
    if select_poke_id and select_poke_id.isdigit() and opponent_poke_id and opponent_poke_id.isdigit():
        select_poke_info = api_pokemon_from_id(select_poke_id).json if api_pokemon_from_id(select_poke_id).status_code == 200 else None
        opponent_poke_info = api_pokemon_from_id(opponent_poke_id).json if api_pokemon_from_id(opponent_poke_id).status_code == 200 else None
        
        if select_poke_info and opponent_poke_info:
            result = {
                'select_poke': select_poke_info,
                'opponent_poke': opponent_poke_info,
            }
            return make_response(result, 200)
        else:
            return make_response({'error': 'Not Found'}, 404)
    else:
        return make_response({'error': 'Bad Request'}, 400)


def fight_logic(select_number, select_poke, opponent_poke, select_poke_hp, opponent_poke_hp):
    # get random number opponent
    opponent_number = random.randint(1, 10)

    # attack logic
    if select_poke_hp > 0 and opponent_poke_hp > 0:
        if select_number % 2 == opponent_number % 2:
            opponent_poke_hp -= select_poke['attack']
            round_winner_id = select_poke['id']
        else:
            select_poke_hp -= opponent_poke['attack']
            round_winner_id = opponent_poke['id']

    # checking winner battle
    winner = None
    if select_poke_hp <= 0:
        winner = opponent_poke['id']
    elif opponent_poke_hp <= 0:
        winner = select_poke['id']

    # result round
    result = {
        'select_poke': {
            'id': select_poke['id'],
            'hp': select_poke_hp,
            'attack': select_poke['attack'],
        },
        'opponent_poke': {
            'id': opponent_poke['id'],
            'hp': opponent_poke_hp,
            'attack': opponent_poke['attack'],
        },
        'round': {
            'winner_id': round_winner_id,
            'select_number': select_number,
            'opponent_number': opponent_number,
            'select_poke_hp': select_poke_hp,
            'opponent_poke_hp': opponent_poke_hp,
        },
        'winner': winner,
    }
    return result


@api.route('/api/v1/fight/<int:select_number>', methods=['POST'])
def api_fight_round(select_number):
    select_poke = request.json['select_poke']
    opponent_poke = request.json['opponent_poke']

    if select_poke and opponent_poke and select_number > 0 and select_number < 11:
        if {'id', 'hp', 'attack'}.issubset(set(select_poke)) and {'id', 'hp', 'attack'}.issubset(set(opponent_poke)):
            result = fight_logic(select_number=select_number,
                                 select_poke=select_poke,
                                 opponent_poke=opponent_poke,
                                 select_poke_hp=select_poke['hp'],
                                 opponent_poke_hp=opponent_poke['hp'])
            return make_response(result, 200)  
    return make_response({'error': 'Bad Request'}, 400)
    

@api.route('/api/v1/fight/fast', methods=['GET'])
def api_fight_fast():
    select_poke_id = request.args.get('select_poke_id')
    opponent_poke_id = request.args.get('opponent_poke_id')
    if select_poke_id and select_poke_id.isdigit() and opponent_poke_id and opponent_poke_id.isdigit():
        select_poke_info = api_pokemon_from_id(select_poke_id).json if api_pokemon_from_id(select_poke_id).status_code == 200 else None
        opponent_poke_info = api_pokemon_from_id(opponent_poke_id).json if api_pokemon_from_id(opponent_poke_id).status_code == 200 else None
        
        if select_poke_info and opponent_poke_info:
            select_poke_hp = select_poke_info['hp']
            opponent_poke_hp = opponent_poke_info['hp']
            rounds = []

            # start new rounds until a winner is found
            while select_poke_hp > 0 and opponent_poke_hp > 0:
                select_number = random.randint(1, 10)
                result = fight_logic(select_number=select_number,
                                     select_poke=select_poke_info,
                                     opponent_poke=opponent_poke_info,
                                     select_poke_hp=select_poke_hp,
                                     opponent_poke_hp=opponent_poke_hp)
                select_poke_hp = result['select_poke']['hp']
                opponent_poke_hp = result['opponent_poke']['hp']
                winner = result['winner']
                rounds.append(result['round'])

                if winner:
                    break
        
            result = {
                'select_poke': {
                    'id': select_poke_info['id'],
                    'hp': select_poke_hp,
                    'attack': select_poke_info['attack'],
                },
                'opponent_poke': {
                    'id': opponent_poke_info['id'],
                    'hp': opponent_poke_hp,
                    'attack': opponent_poke_info['attack'],
                },
                'rounds': rounds,
                'winner': winner,
            }
            return make_response(result, 200)  
        else:
            return make_response({'error': 'Not Found'}, 404)
    else:
        return make_response({'error': 'Bad Request'}, 400)


@api.route('/api/v1/pokemon/save/<int:id>', methods=['POST'])
def api_pokemon_save_from_id(id):
    poke_info = api_pokemon_from_id(id).json if api_pokemon_from_id(id).status_code == 200 else None
    if poke_info:
        folder_name = str(date.today()).replace('-', '').strip()
        text_markdown = f"# {poke_info['name']}\n\n### Poke Information:\n- hp: {poke_info['hp']}\n- attack: {poke_info['attack']}\n- defense: {poke_info['defense']}\n- special_attack: {poke_info['special_attack']}\n- special_defense: {poke_info['special_defense']}\n- speed: {poke_info['speed']}"
        byte_text_markdown = text_markdown.encode('utf-8')
        
        try:
            ftp = ftplib.FTP(host=FTP_HOST)
            ftp.login(user=FTP_USER, passwd=FTP_PASSWORD)

            files = ftp.nlst()
            if folder_name not in files:
                ftp.mkd(folder_name)
            ftp.cwd(folder_name)
            ftp.storbinary(f"STOR {poke_info['name']}.md", io.BytesIO(byte_text_markdown))
            return make_response({'result': 'file was successfully generated and saved',
                                  'poke_name': poke_info['name']}, 201) 
        except:
            return make_response({'error': 'Service Unavailable',
                                  'poke_name': poke_info['name']}, 503)
        finally:
            ftp.quit()
    return make_response({'error': 'Bad Request'}, 400)
