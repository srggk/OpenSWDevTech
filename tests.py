from settings import *
from datetime import date
from io import StringIO
import requests, sys, json, ftplib
import unittest
import flask_unittest
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.firefox.webdriver import WebDriver


class TestApiMethods(unittest.TestCase):
    # initialization logic for the test suite declared in the test module
    # code that is executed before all tests in one test run
    @classmethod
    def setUpClass(cls):
        cls.ftp = ftplib.FTP(host=FTP_HOST)
        cls.ftp.login(user=FTP_USER, passwd=FTP_PASSWORD)

    # clean up logic for the test suite declared in the test module
    # code that is executed after all tests in one test run
    @classmethod
    def tearDownClass(cls):
        cls.ftp.quit() 

    # initialization logic
    # code that is executed before each test
    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True  

    # clean up logic
    # code that is executed after each test
    def tearDown(self):
        pass 

    # test methods below

    def test_get_info_about_poke(self):
        response = self.app.get('/api/v1/pokemon/1')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content_type, 'application/json')
        data = json.loads(response.data)
        self.assertEqual([data['id'], data['name'], data['attack'], data['defense'], data['hp']],
                          [1, 'bulbasaur', 49, 49, 45])

    def test_get_list_pokes_with_page(self):
        response = self.app.get('/api/v1/pokemon/list?page=1')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content_type, 'application/json')
        data = json.loads(response.data)
        self.assertEqual(data['page_count'], 130)
        self.assertEqual(len(data['list']), 10)
        self.assertEqual([poke['id'] for poke in data['list']], list(range(1, 11)))
    
    def test_get_list_pokes_with_search(self):
        response = self.app.get('/api/v1/pokemon/list?search_string=bu')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content_type, 'application/json')
        data = json.loads(response.data)
        self.assertEqual(data['page_count'], 4)
        self.assertEqual(len(data['list']), 10)
        self.assertEqual(data['list'][0]['name'], 'bulbasaur')

        response = self.app.get('/api/v1/pokemon/list?search_string=bu&page=4')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content_type, 'application/json')
        data = json.loads(response.data)
        self.assertEqual(data['page_count'], 4)
        self.assertEqual(len(data['list']), 6)

    def test_get_list_pokes_without_params(self):
        response = self.app.get('/api/v1/pokemon/list')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content_type, 'application/json')
        data = json.loads(response.data)

        response2 = self.app.get('/api/v1/pokemon/list?page=1')
        self.assertEqual(response2.status_code, 200)
        self.assertEqual(response2.content_type, 'application/json')
        data2 = json.loads(response2.data)

        self.assertDictEqual(data, data2)

    def test_get_random_poke_id(self):
        response = self.app.get('/api/v1/pokemon/random')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content_type, 'application/json')
        data = json.loads(response.data)

        response2 = requests.get('https://pokeapi.co/api/v2/pokemon/?limit=1')
        data2 = response2.json() if response2.status_code == 200 else {}

        self.assertTrue(type(data['id']) == type(1))
        self.assertTrue(0 < data['id'] < data2['count'])

    def test_get_create_fight(self):
        response = self.app.get('/api/v1/fight?select_poke_id=1&opponent_poke_id=2')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content_type, 'application/json')
        data = json.loads(response.data)

        response2 = self.app.get('/api/v1/pokemon/1')
        self.assertEqual(response2.status_code, 200)
        self.assertEqual(response2.content_type, 'application/json')
        data2 = json.loads(response2.data)

        response3 = self.app.get('/api/v1/pokemon/2')
        self.assertEqual(response3.status_code, 200)
        self.assertEqual(response3.content_type, 'application/json')
        data3 = json.loads(response3.data)

        self.assertDictEqual(data['select_poke'], data2)
        self.assertDictEqual(data['opponent_poke'], data3)
        self.assertEqual(data['select_poke']['name'], 'bulbasaur')
        self.assertEqual(data['opponent_poke']['name'], 'ivysaur')
    
    def test_post_fight_round(self):
        selected_poke_num = 2

        selected_poke_id = 1
        selected_poke_hp = 45
        selected_poke_attack = 49

        opponent_poke_id = 3
        opponent_poke_hp = 80
        opponent_poke_attack = 82

        response = self.app.post(f'/api/v1/fight/{selected_poke_num}', data=json.dumps({
            'select_poke': {
                'id': selected_poke_id,
                'hp': selected_poke_hp,
                'attack': selected_poke_attack,
            },
            'opponent_poke': {
                'id': opponent_poke_id,
                'hp': opponent_poke_hp,
                'attack': opponent_poke_attack,
            },
        }), content_type='application/json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content_type, 'application/json')
        data = json.loads(response.data)

        opponent_poke_num = data['round']['opponent_number']
        round_winner_id = None
        if selected_poke_num % 2 == opponent_poke_num % 2:
            opponent_poke_hp -= selected_poke_attack
            round_winner_id = selected_poke_id
        else:
            selected_poke_hp -= opponent_poke_attack
            round_winner_id = opponent_poke_id

        self.assertEqual(data['round'], {
            'opponent_number': opponent_poke_num,
            'opponent_poke_hp': opponent_poke_hp,
            'select_number': selected_poke_num,
            'select_poke_hp': selected_poke_hp,
            'winner_id': round_winner_id
        })
        self.assertEqual(data['opponent_poke'], {
            'attack': opponent_poke_attack,
            'hp': opponent_poke_hp,
            'id': opponent_poke_id
        })
        self.assertEqual(data['select_poke'], {
            'attack': selected_poke_attack,
            'hp': selected_poke_hp,
            'id': selected_poke_id
        })

        if data['round']['winner_id'] == selected_poke_id:
            self.assertEqual(data['winner'], None)
        elif data['round']['winner_id'] == opponent_poke_id:
            self.assertEqual(data['winner'], 3)

    def test_get_fast_fight_results(self):
        selected_poke_id = 1
        selected_poke_hp = 45
        selected_poke_attack = 49
        opponent_poke_id = 3
        opponent_poke_hp = 80
        opponent_poke_attack = 82

        response = self.app.get(f'/api/v1/fight/fast?select_poke_id={selected_poke_id}&opponent_poke_id={opponent_poke_id}')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content_type, 'application/json')
        data = json.loads(response.data)

        if data['winner'] == 3:
            if len(data['rounds']) == 1:
                # 'select_poke': {'attack': 49, 'hp': -37, 'id': 1}
                # 'opponent_poke': {'attack': 82, 'hp': 80, 'id': 3}
                # {'opponent_poke': {'attack': 82, 'hp': 80, 'id': 3}, 'rounds': [{'opponent_number': 5, 'opponent_poke_hp': 80, 'select_number': 10, 'select_poke_hp': -37, 'winner_id': 3}], 'select_poke': {'attack': 49, 'hp': -37, 'id': 1}, 'winner': 3}
                round1 = {'select_poke_hp': selected_poke_hp - opponent_poke_attack, 'opponent_poke_hp': opponent_poke_hp, 'winner_id': opponent_poke_id}
                
                self.assertEqual(data['opponent_poke'], {'attack': opponent_poke_attack, 'hp': round1['opponent_poke_hp'], 'id': opponent_poke_id})
                self.assertEqual(data['select_poke'], {'attack': selected_poke_attack, 'hp': round1['select_poke_hp'], 'id': selected_poke_id})
                self.assertEqual({
                    'opponent_poke_hp': data['rounds'][0]['opponent_poke_hp'],
                    'select_poke_hp': data['rounds'][0]['select_poke_hp'],
                    'winner_id': data['rounds'][0]['winner_id']
                }, {
                    'opponent_poke_hp': round1['opponent_poke_hp'],
                    'select_poke_hp': round1['select_poke_hp'],
                    'winner_id': round1['winner_id']
                })

            elif len(data['rounds']) == 2:
                # 'select_poke': {'attack': 49, 'hp': -37, 'id': 1}
                # 'opponent_poke': {'attack': 82, 'hp': 31, 'id': 3}
                # {'opponent_poke': {'attack': 82, 'hp': 31, 'id': 3}, 'rounds': [{'opponent_number': 8, 'opponent_poke_hp': 31, 'select_number': 10, 'select_poke_hp': 45, 'winner_id': 1}, {'opponent_number': 10, 'opponent_poke_hp': 31, 'select_number': 7, 'select_poke_hp': -37, 'winner_id': 3}], 'select_poke': {'attack': 49, 'hp': -37, 'id': 1}, 'winner': 3}
                round1 = {'select_poke_hp': selected_poke_hp, 'opponent_poke_hp': opponent_poke_hp - selected_poke_attack, 'winner_id': selected_poke_id}
                round2 = {'select_poke_hp': round1['select_poke_hp'] - opponent_poke_attack, 'opponent_poke_hp': round1['opponent_poke_hp'], 'winner_id': opponent_poke_id}
                
                self.assertEqual(data['opponent_poke'], {'attack': opponent_poke_attack, 'hp': round2['opponent_poke_hp'], 'id': opponent_poke_id})
                self.assertEqual(data['select_poke'], {'attack': selected_poke_attack, 'hp': round2['select_poke_hp'], 'id': selected_poke_id})
                self.assertEqual({
                    'opponent_poke_hp': data['rounds'][0]['opponent_poke_hp'],
                    'select_poke_hp': data['rounds'][0]['select_poke_hp'],
                    'winner_id': data['rounds'][0]['winner_id']
                }, {
                    'opponent_poke_hp': round1['opponent_poke_hp'],
                    'select_poke_hp': round1['select_poke_hp'],
                    'winner_id': round1['winner_id']
                })
                self.assertEqual({
                    'opponent_poke_hp': data['rounds'][1]['opponent_poke_hp'],
                    'select_poke_hp': data['rounds'][1]['select_poke_hp'],
                    'winner_id': data['rounds'][1]['winner_id']
                }, {
                    'opponent_poke_hp': round2['opponent_poke_hp'],
                    'select_poke_hp': round2['select_poke_hp'],
                    'winner_id': round2['winner_id']
                })

        elif data['winner'] == 1:
            # 'select_poke': {'attack': 49, 'hp': 45, 'id': 1}
            # 'opponent_poke': {'attack': 82, 'hp': -18, 'id': 3}
            # {'opponent_poke': {'attack': 82, 'hp': -18, 'id': 3}, 'rounds': [{'opponent_number': 9, 'opponent_poke_hp': 31, 'select_number': 5, 'select_poke_hp': 45, 'winner_id': 1}, {'opponent_number': 4, 'opponent_poke_hp': -18, 'select_number': 8, 'select_poke_hp': 45, 'winner_id': 1}], 'select_poke': {'attack': 49, 'hp': 45, 'id': 1}, 'winner': 1}
            round1 = {'select_poke_hp': selected_poke_hp, 'opponent_poke_hp': opponent_poke_hp - selected_poke_attack, 'winner_id': selected_poke_id}
            round2 = {'select_poke_hp': round1['select_poke_hp'], 'opponent_poke_hp': round1['opponent_poke_hp'] - selected_poke_attack, 'winner_id': selected_poke_id}
            
            self.assertEqual(data['opponent_poke'], {'attack': opponent_poke_attack, 'hp': round2['opponent_poke_hp'], 'id': opponent_poke_id})
            self.assertEqual(data['select_poke'], {'attack': selected_poke_attack, 'hp': round2['select_poke_hp'], 'id': selected_poke_id})
            self.assertEqual({
                'opponent_poke_hp': data['rounds'][0]['opponent_poke_hp'],
                'select_poke_hp': data['rounds'][0]['select_poke_hp'],
                'winner_id': data['rounds'][0]['winner_id']
            }, {
                'opponent_poke_hp': round1['opponent_poke_hp'],
                'select_poke_hp': round1['select_poke_hp'],
                'winner_id': round1['winner_id']
            })
            self.assertEqual({
                'opponent_poke_hp': data['rounds'][1]['opponent_poke_hp'],
                'select_poke_hp': data['rounds'][1]['select_poke_hp'],
                'winner_id': data['rounds'][1]['winner_id']
            }, {
                'opponent_poke_hp': round2['opponent_poke_hp'],
                'select_poke_hp': round2['select_poke_hp'],
                'winner_id': round2['winner_id']
            })

    def test_post_save_poke_info_ftp(self):
        poke_id = 1
        response = self.app.post(f'/api/v1/pokemon/save/{poke_id}')
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.content_type, 'application/json')
        data = json.loads(response.data)
        poke_name = 'bulbasaur'
        self.assertEqual(data['poke_name'], poke_name)

        folder_name = str(date.today()).replace('-', '').strip()
        self.assertTrue(folder_name in self.ftp.nlst())
        self.ftp.cwd(folder_name)
        self.assertTrue(f'{poke_name}.md' in self.ftp.nlst())

        tmp = sys.stdout
        res = StringIO()
        sys.stdout = res
        self.ftp.retrlines(f'RETR {poke_name}.md')
        sys.stdout = tmp
        text = res.getvalue()
        self.assertTrue(f'# {poke_name}' in text)


class TestBySelenium(flask_unittest.LiveTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.selenium = WebDriver()
        cls.selenium.implicitly_wait(10)

    @classmethod
    def tearDownClass(cls):
        cls.selenium.quit()
        super().tearDownClass()

    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True  

    def tearDown(self):
        pass 

    def test_index_page(self):
        self.selenium.get(f'http://{WEB_IP}:{WEB_PORT}/')
        WebDriverWait(self.selenium, 10).until(
            lambda driver: driver.find_element(By.TAG_NAME, "body")
        )
        response = self.app.get('/api/v1/pokemon/list?page=1')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content_type, 'application/json')
        data = json.loads(response.data)

        cards = self.selenium.find_elements(By.CLASS_NAME, "card")
        self.assertTrue(len(cards) == len(data['list']))
        pagions_elements = self.selenium.find_elements(By.CLASS_NAME, "page-item")
        self.assertTrue(pagions_elements[1].text == f"Page 1 in {data['page_count']}")

    def test_poke_page(self):
        self.selenium.get(f'http://{WEB_IP}:{WEB_PORT}/poke/bulbasaur')
        WebDriverWait(self.selenium, 10).until(
            lambda driver: driver.find_element(By.TAG_NAME, "body")
        )
        response = self.app.get('/api/v1/pokemon/bulbasaur')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content_type, 'application/json')
        data = json.loads(response.data)

        cards_body = self.selenium.find_elements(By.CLASS_NAME, "card-body")
        poke_name = cards_body[0].find_element(By.TAG_NAME, "h4").text
        poke_info_spans = cards_body[0].find_elements(By.TAG_NAME, "span")
        poke_info = [poke_ch.text for poke_ch in poke_info_spans]

        self.assertEqual(poke_name, data['name'])
        self.assertEqual(poke_info, [
            f"hp: {data['hp']}", f"attack: {data['attack']}", f"defense: {data['defense']}",
            f"special-attack: {data['special_attack']}", f"special-defense: {data['special_defense']}",
            f"speed: {data['speed']}"
        ])

    def test_poke_search(self):
        self.selenium.get(f'http://{WEB_IP}:{WEB_PORT}/')
        WebDriverWait(self.selenium, 10).until(
            lambda driver: driver.find_element(By.TAG_NAME, "body")
        )
        search_input = self.selenium.find_element(By.NAME, "search_string")
        search_input.send_keys('bu')
        self.selenium.find_element(By.XPATH, '//button[text()="Search"]').click()
        WebDriverWait(self.selenium, 10).until(
            lambda driver: driver.find_element(By.TAG_NAME, "body")
        )

        response = self.app.get('/api/v1/pokemon/list?search_string=bu')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content_type, 'application/json')
        data = json.loads(response.data)

        cards = self.selenium.find_elements(By.CLASS_NAME, "card")
        self.assertTrue(len(cards) == len(data['list']))
        pagions_elements = self.selenium.find_elements(By.CLASS_NAME, "page-item")
        self.assertTrue(pagions_elements[1].text == f"Page 1 in {data['page_count']}")

    def test_move_player_in_fight(self):
        self.selenium.get(f'http://{WEB_IP}:{WEB_PORT}/')
        WebDriverWait(self.selenium, 10).until(
            lambda driver: driver.find_element(By.TAG_NAME, "body")
        )
        self.selenium.find_element(By.XPATH, '//button[text()="To battle"]').click()
        WebDriverWait(self.selenium, 10).until(
            lambda driver: driver.find_element(By.TAG_NAME, "body")
        )
        select_number_input = self.selenium.find_element(By.NAME, "select_number")
        select_number_input.send_keys(2)
        self.selenium.find_element(By.XPATH, '//button[text()="Enter"]').click()
        WebDriverWait(self.selenium, 10).until(
            lambda driver: driver.find_element(By.TAG_NAME, "body")
        )
        table = self.selenium.find_element(By.TAG_NAME, "table")
        self.assertTrue(type(table) == type(select_number_input))
        td1 = table.find_element(By.TAG_NAME, "td")
        self.assertTrue(td1.text == "2")


if __name__ == '__main__':
    suite = flask_unittest.LiveTestSuite(app)
    suite.addTest(unittest.makeSuite(TestApiMethods))
    suite.addTest(unittest.makeSuite(TestBySelenium))
    unittest.TextTestRunner(verbosity=2).run(suite)
