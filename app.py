from flask import Flask, render_template, request, redirect, url_for
import requests

app = Flask(__name__)

limit = 12


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

    return render_template('index.html', 
                           pokemons=poke_list, 
                           search_string=search_string,
                           current=page, 
                           end=page_count)


if __name__ == '__main__':
    app.run(debug=True)
