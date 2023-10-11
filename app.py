from flask import Flask, render_template, request, redirect, url_for
import requests

app = Flask(__name__)

limit = 12


def get_poke(offset=0):
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


@app.route('/')
def poke():
    page = 1
    if request.args.get('page'):
        if request.args.get('page').isdigit():
            page = int(request.args.get('page'))

    offset = (page - 1) * limit 
    poke_list, page_count = get_poke(offset)

    return render_template('index.html', 
                           pokemons=poke_list, 
                           current=page, 
                           end=page_count)


@app.route('/search', methods=['POST'])
def search_pokemons():
    search_str = request.form['search_string']
    if search_str == '':
        return redirect(url_for('pokemons'))
    else:
        response = requests.get(f'https://pokeapi.co/api/v2/pokemon/{search_str}/')
        if response.status_code == 200:
            searched_pokemons = response.json()
            searched_name_pokemons = {
                'name': searched_pokemons['name']
            }
            searched_name_pokemons = [searched_name_pokemons['name']]
            return render_template('index.html', pokemons=searched_name_pokemons, search_string=search_str)
        else:
            return render_template('index.html', pokemons=[], search_string=search_str)


if __name__ == '__main__':
    app.run(debug=True)
