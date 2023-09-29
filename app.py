from flask import Flask, render_template, request, redirect, url_for
import requests

app = Flask(__name__)

@app.route('/')
def pokemons():
    response = requests.get('https://pokeapi.co/api/v2/pokemon/?limit=1')
    if response.status_code == 200:
        pokemons_count = response.json()['count']
        all_pokemons_data = requests.get(f'https://pokeapi.co/api/v2/pokemon/?limit={pokemons_count}').json()['results']
        pokemons_name = [poke['name'] for poke in all_pokemons_data]
    return render_template('index.html', pokemons=pokemons_name)


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
