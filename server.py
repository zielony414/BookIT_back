from flask import Flask, request, jsonify
import pymysql
import base64

app = Flask(__name__)

#----------------------------------------------------------------------------------------------------------------------
# connection with database
db = pymysql.connect(
    charset = "utf8mb4",
    connect_timeout = 10,
    cursorclass = pymysql.cursors.DictCursor,
    db = "bookit_main",
    host = "bookit-bookit.f.aivencloud.com",
    password = "AVNS_lK1EnykcZ5J6TflOpru",
    read_timeout = 10,
    port = 22474,
    user = "avnadmin",
    write_timeout = 10,
)

# dzięki cursorowi będziemy wysyłać i odbierać zapytania do bazy danych
cursor = db.cursor()

#------------------------------------------------------------------------------------------------------------------------
public_email = ""

# Members API route
@app.route('/members')
def members():
    return {"members": ["member1", "member2", "member3"]}

@app.route('/api/nav_items')
def get_nav_items():
    return {"nav_items": ["Barber", "Salon kosmetyczny", "Paznokcie", "Masaż", "Zwierzęta", "Siłownia", "Więcej..."]}

@app.route('/api/image_cards')
def get_image_cards():
    try:
        cursor.execute("SELECT Name, Logo, description FROM companies;")
        companies = cursor.fetchall()

        # Pobierz nazwy kolumn z wyników zapytania SQL
        columns = [desc[0] for desc in cursor.description]

        # Przetwarzanie wyników
        result = []
        for company in companies:
            name = company['Name']
            logo = company['Logo']
            description = company['description'] 
            if logo:
                logo_bytes = bytes(logo)  # Konwertuj łańcuch znaków na bajty
                logo_base64 = base64.b64encode(logo_bytes).decode('utf-8')
                logo_url = f"data:image/png;base64,{logo_base64}"
            else:
                logo_url = None
            result.append({
                'name': name,
                'logo': logo_url,
                'description': description
            })
        return jsonify({'companies': result}), 200
    except Exception as err:
        # Gdy pojawi się jakiś błąd, zwraca error
        return jsonify({'error': str(err)}), 500

# dekorator, wpisuje się to na froncie w funkcji fetch() i wtedy jest wywoływana ta funkcja poniżej
@app.route('/api/strona_logowania/user', methods=['POST']) # ogólnie metoda komuniakcji POST GET się nazywa REST-API podaje dla informacji
def logging_in_user():
    try:
        # pobranie danych z frontu poprzez JSON
        login = request.json.get('user_login') # pola podane przez front muszą nazywać się user_login i user_password
        password = request.json.get('user_password')

        cursor.execute(f"SELECT * FROM users WHERE email = '{login}' AND password = '{password}';") 
        # zwraca listę dobrych dopasowań
        answer = cursor.fetchall()

        if len(answer) > 0:
            return jsonify({'message': 'Zalogowano pomyślnie!', 'username': login}), 200
        else:
            return jsonify({'message': 'Niepoprawne dane logowania!'}), 401
        
    except Exception as err:
        # gdy pojawi się jakiś błąd zwraca error
        return jsonify({'error': str(err)}), 500
    
@app.route('/api/strona_logowania/company', methods=['POST']) # ogólnie metoda komuniakcji POST GET się nazywa REST-API podaje dla informacji
def logging_in_company():
    try:
        # pobranie danych z frontu poprzez JSON
        login = request.json.get('company_login') # pola podane przez front muszą nazywać się company_login i company_password
        password = request.json.get('company_password')

        cursor.execute(f"SELECT * FROM companies WHERE email = '{login}' AND password = '{password}';") 
        # zwraca listę dobrych dopasowań
        answer = cursor.fetchall()

        if len(answer) > 0:
            return jsonify({'message': 'Zalogowano pomyślnie!', 'username': login}), 200
        else:
            return jsonify({'message': 'Niepoprawne dane logowania!'}), 401
        
    except Exception as err:
        # gdy pojawi się jakiś błąd zwraca error
        return jsonify({'error': str(err)}), 500

@app.route('/api/strona_rejestracji_firmy/create', methods=['POST'])
def registration_company():
    global public_email
    try:
        email = request.json.get('email')
        public_email = email
        password = request.json.get('password')
        company_name = request.json.get('company_name')
        phone = request.json.get('phone')
        description = request.json.get('description')
        nip = request.json.get('nip')
        category = request.json.get('category')
        type_of_servise = request.json.get('type_of_servise')
        street_number = request.json.get('street_number')
        city = request.json.get('city')
        post_code = request.json.get('post_code')
        link_page = request.json.get('link_page')
        facebook = request.json.get('facebook')
        tt = request.json.get('tt')
        linkedin = request.json.get('linkedin')
        instagram = request.json.get('instagram')
        twitter = request.json.get('twitter')
        pon_start = request.json.get('pon_start')
        pon_stop = request.json.get('pon_stop')
        wt_start = request.json.get('wt_start')
        wt_stop = request.json.get('wt_stop')
        sr_start = request.json.get('sr_start')
        sr_stop = request.json.get('sr_stop')
        czw_start = request.json.get('czw_start')
        czw_stop = request.json.get('czw_stop')
        pt_start = request.json.get('pt_start')
        pt_stop = request.json.get('pt_stop')
        sob_start = request.json.get('sob_start')
        sob_stop = request.json.get('sob_stop')
        nd_start = request.json.get('nd_start')
        nd_stop = request.json.get('nd_stop')

        # poprawić #Logo i #Sector bo też nie wiem co to
        cursor.execute(f"""INSERT INTO companies (Name, Adress, #Sector, #Logo, Category, Site_link, Facebook_link, Linkedin_link, Instagram_link, X_link,
                    Tiktok_link, Reviews_no, Sum_of_reviews, NIP, tel_nr, description, email, type_of_service, password) 
                    VALUES ('{company_name}', '{city} {street_number} {post_code}', #Sector, #Logo, '{category}', '{link_page}', '{facebook}', '{linkedin}', 
                    '{instagram}', '{twitter}', '{tt}', 0, 0, '{nip}', '{phone}', '{description}', '{email}', '{type_of_servise}', '{password}');""")

        cursor.execute(f"""INSERT INTO opening_hours (company_id, monday_start, monday_end, tuesday_start, tuesday_end, wensday_start, wensday_end, thursday_start, thursday_end, friday_start, friday_end, saturday_start, saturday_end, sunday_start, sunday_end) 
              VALUES ( (SELECT ID FROM companies WHERE (email='{email}')), '{pon_start}', '{pon_stop}', '{wt_start}', '{wt_stop}', '{sr_start}', '{sr_stop}', '{czw_start}', '{czw_stop}', '{pt_start}', '{pt_stop}', '{sob_start}', '{sob_stop}', '{nd_start}', '{nd_stop}');""")
        return jsonify({'message': 'Firma została stworzona!'}), 200
    except Exception as err:
        # gdy pojawi się jakiś błąd zwraca error
        return jsonify({'error': str(err)}), 500
 
@app.route('/api/strona_rejestracji_firmy/usługa', methods=['POST'])
def add_service():
    global public_email
    try:
        name = request.json.get('name')
        type = request.json.get('type')
        description = request.json.get('description')
        hours = request.json.get('hours')
        minutes = request.json.get('minutes')
        price = request.json.get('price')

        # poprawić approximate_cost bo niewiem co to jest i dodać typ usługi 
        cursor.execute(f"""INSERT INTO services (company_ID, service_name, cost, #approximate_cost, execution_time, additional_info) 
                       VALUES ((SELECT ID FROM companies WHERE (email='{public_email}')), '{name}', '{price}', '#aproximate_cost', '{hours * 60 + minutes}', '{description}');""")
        
        return jsonify({'message': 'Usługa została dodana!'}), 200
    except Exception as err:
        return jsonify({'error': str(err)}), 500
    
@app.route('/api/strona_rejestracji_firmy/zdjecia', methods=['POST'])
def add_photos():
    try:
        files = request.files
        photo = files.get('file')
        cursor.execute(f"INSERT INTO photos (company_ID, picture) VALUES ((SELECT ID FROM companies WHERE (email='{public_email}'), {photo});")
        
        return jsonify({'message': 'Zdjęcie zostało dodane!'}), 200
    except Exception as err:
        return jsonify({'error': str(err)}), 500



if __name__ == '__main__':
    app.run(debug=True)

