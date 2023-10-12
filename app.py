from flask import Flask, render_template, request, redirect, url_for
import requests

app = Flask(__name__)

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
        print('404 poke info')
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


@app.route("/poke/<string:poke_name>")
def poke_page(poke_name):
    poke = get_poke_info(poke_name)
    return render_template('info.html', poke=poke)


@app.route('/battle', methods=['GET', 'POST'])
def battle():
    if request.method == 'POST':
        select_poke = request.form['select_poke']
        return render_template('battle.html',
                               select_poke=select_poke)
    
    return redirect(url_for('poke'))


if __name__ == '__main__':
    app.run(debug=True)
