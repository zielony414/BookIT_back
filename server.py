from flask import Flask, request, jsonify, session
from datetime import datetime, timedelta
import pymysql
import base64
import re
import mail_sender
import free_day
#import schedule # pip install schedule - jest zastąpiony przez APScheduler
from apscheduler.schedulers.background import BackgroundScheduler #pip install APScheduler
from werkzeug.utils import secure_filename #pip install Werkzeug
from decouple import config
import traceback #do usunięcia
from datetime import timedelta
import datetime
from flask_cors import CORS #pip install flask-cors
from flask_session import Session #pip install Flask-Session
import redis

r = redis.Redis(
  host='redis-11724.c311.eu-central-1-1.ec2.redns.redis-cloud.com',
  port=11724,
  password='uyKTNkb77sspebUHT1SWyQ7XkQSiLu3F')

app = Flask(__name__)
CORS(app)

SESSION_TYPE = 'redis'
SESSION_REDIS = r
app.config.from_object(__name__)
Session(app)


#----------------------------------------------------------------------------------------------------------------------
# connection with database
def get_db_connection():
    return pymysql.connect(
        charset = "utf8mb4",
        connect_timeout = 500,
        cursorclass=pymysql.cursors.DictCursor,
        db = config('DB_DATABASE'),
        host = config('DB_HOST'),
        password = config('DB_PASS'),
        read_timeout = 500,
        port = int(config('DB_PORT')),
        user = config('DB_USER'),
        write_timeout = 500
    )

public_email_company_reg = "" # zmienna potrzebna do rejestracji firmy
log_as_company = False # True - zalogowano jako firma
log_as_user = False # True - zalogowano jako użytkownik
logged_email = "" # EMAIL ZALOGOWANEGO UŻYTKOWNIKA LUB FIRMY

# Members API route
@app.route('/members')
def members():
    return {"members": ["member1", "member2", "member3"]}

@app.route('/api/nav_items')
def get_nav_items():
    return {"nav_items": ["Fryzjer", "Uroda", "Masaż", "Zwierzęta", "Siłownia", "Więcej..."]}

@app.route('/api/image_cards')
def get_image_cards():
    try:
        db = get_db_connection()
        cursor = db.cursor()
        cursor.execute("SELECT Name, Logo, description FROM companies limit 5;")
        companies = cursor.fetchall()
        db.close()

        result = []
        for company in companies:
            name = company['Name']
            logo = company['Logo']
            description = company['description']
            if logo:
                logo_bytes = bytes(logo)
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
        print("Error:", str(err))
        return jsonify({'error': str(err)}), 500

@app.route('/api/strona_wyszukiwania_kategorie')
def get_categories():
    try:
        db = get_db_connection()
        cursor = db.cursor()
        cursor.execute("SELECT DISTINCT Category FROM companies;")
        categories = cursor.fetchall()
        db.close()

        result = [category['Category'] for category in categories]
        return jsonify({'categories': result}), 200
    except Exception as err:
        return jsonify({'error': str(err)}), 500

@app.route('/api/strona_wyszukiwania_miasta')
def get_cities():
    try:
        db = get_db_connection()
        cursor = db.cursor()
        cursor.execute("SELECT DISTINCT City FROM companies;")
        cities = cursor.fetchall()
        db.close()

        result = [city['City'] for city in cities]
        return jsonify({'cities': result}), 200
    except Exception as err:
        return jsonify({'error': str(err)}), 500
    
@app.route('/api/wyszukiwanie', methods=['POST'])
def return_search():
    try:
        # pobranie danych z frontu poprzez JSON
        kategoria = request.json.get('kategoria')
        miasto = request.json.get('miasto')
        sortowanie = request.json.get('sortowanie')
        
        db = get_db_connection()
        cursor = db.cursor()

        if miasto == 'Wszystkie':
            miasto = ''

        if kategoria == 'Wszystkie' or kategoria == 'Więcej...':
            kategoria = ''

        if sortowanie == 'Najwyższa ocena':
            cursor.execute(f"""
                SELECT *, 
                CASE
                    WHEN Reviews_no > 0 THEN Sum_of_reviews / Reviews_no
                    ELSE 0
                END AS srednia_ocena 
                FROM companies 
                WHERE City LIKE '%{miasto}%' AND Category LIKE '%{kategoria}%'
                ORDER BY srednia_ocena DESC; 
            """) 
        elif sortowanie == 'Najpopularniejsze':
            cursor.execute(f"""
                SELECT * 
                FROM companies 
                WHERE City LIKE '%{miasto}%' AND Category LIKE '%{kategoria}%'
                ORDER BY Reviews_no DESC; 
            """)
        elif sortowanie == 'Od najnowszych':
            cursor.execute(f"""
                SELECT * 
                FROM companies 
                WHERE City LIKE '%{miasto}%' AND Category LIKE '%{kategoria}%'
                ORDER BY ID DESC; 
            """)
        
        companies = cursor.fetchall()
        db.close()
        
        # Przetwarzanie wyników
        result = []
        for company in companies:
            name = company['Name']
            city = company['City']
            address = company['Address']
            category = company['Category']
            reviews_no = company['Reviews_no']
            sum_of_reviews = company['Sum_of_reviews']
            logo = company['Logo']
            description = company['description'] 
            avg_rating = round(sum_of_reviews / reviews_no, 2) if reviews_no > 0 else 0
            if logo:
                logo_bytes = bytes(logo)  # Konwertuj łańcuch znaków na bajty
                logo_base64 = base64.b64encode(logo_bytes).decode('utf-8')
                logo_url = f"data:image/png;base64,{logo_base64}"
            else:
                logo_url = None
            result.append({
                'name': name,
                'logo': logo_url,
                'description': description,
                'category': category,
                'address': city + ', ' + address,
                'reviews_no': reviews_no,
                'avg_rating': avg_rating
            })
        return jsonify({'companies': result}), 200
    except Exception as err:
        # Gdy pojawi się jakiś błąd, zwraca error
        return jsonify({'error': str(err)}), 500 

@app.route('/api/user-data')
def get_user_data():
    email = request.cookies.get('email')
    is_company = request.cookies.get('isCompany')
    is_user = request.cookies.get('isUser')
    
    # Użyj tych wartości w razie potrzeby
    user_data = {
        'email': email,
        'isCompany': is_company,
        'isUser': is_user
    }
    
    return jsonify(user_data)

@app.route('/api/wyszukiwanie_po_nazwie', methods=['POST'])
def return_search_names():
    try:
        # pobranie danych z frontu poprzez JSON
        nazwa = request.json.get('nazwa')
        db = get_db_connection()
        cursor = db.cursor()
        cursor.execute(f"SELECT * FROM companies WHERE Name LIKE '%{nazwa}%';")
        companies = cursor.fetchall()
        db.close()
        
        # Przetwarzanie wyników
        result = []
        for company in companies:
            name = company['Name']
            city = company['City']
            address = company['Address']
            category = company['Category']
            reviews_no = company['Reviews_no']
            sum_of_reviews = company['Sum_of_reviews']
            logo = company['Logo']
            description = company['description'] 
            avg_rating = round(sum_of_reviews / reviews_no, 2) if reviews_no > 0 else 0
            if logo:
                logo_bytes = bytes(logo)  # Konwertuj łańcuch znaków na bajty
                logo_base64 = base64.b64encode(logo_bytes).decode('utf-8')
                logo_url = f"data:image/png;base64,{logo_base64}"
            else:
                logo_url = None
            result.append({
                'name': name,
                'logo': logo_url,
                'description': description,
                'category': category,
                'address': city + ',     ' + address,
                'reviews_no': reviews_no,
                'avg_rating': avg_rating
            })
        return jsonify({'companies': result}), 200
    except Exception as err:
        # Gdy pojawi się jakiś błąd, zwraca error
        print(err)
        return jsonify({'error': str(err)}), 500 

# dekorator, wpisuje się to na froncie w funkcji fetch() i wtedy jest wywoływana ta funkcja poniżej
@app.route('/api/strona_logowania/user', methods=['POST']) # ogólnie metoda komuniakcji POST GET się nazywa REST-API podaje dla informacji
def logging_in_user():
    
    print(logged_email)
    try:
        # pobranie danych z frontu poprzez JSON
        login = request.json.get('user_login') # pola podane przez front muszą nazywać się user_login i user_password
        password = request.json.get('user_password')

        db = get_db_connection()
        cursor = db.cursor()
        cursor.execute(f"SELECT * FROM users WHERE email = '{login}' AND password = '{password}';") 
        # zwraca listę dobrych dopasowań
        answer = cursor.fetchall()
        db.close()

        if len(answer) > 0:

            print(request.cookies.get('email'))
            return jsonify({'message': 'Zalogowano pomyślnie!', 'username': login}), 200
        else:
            return jsonify({'message': 'Niepoprawne dane logowania!'}), 401
        
    except Exception as err:
        # gdy pojawi się jakiś błąd zwraca error
        return jsonify({'error': str(err)}), 500

@app.route('/api/user_registration', methods=['POST'])
def register_user():
    try:
        # Pobierz dane z żądania
        #name = request.json.get('name')
        #print(name)
        email = request.json.get('email')
        #print(email)
        password = request.json.get('password')
        #print(password)
        tel_nr = request.json.get('phone')
        #print(tel_nr)
        gender = request.json.get('gender')
        #print(gender)
        address = request.json.get('city')
        #print(address)

        # Sprawdź, czy wszystkie pola są obecne
        if not all([email, password, tel_nr, gender, address]):
            return jsonify({'error': 'Wszystkie pola są obowiązkowe.'}), 400

        # Walidacja emaila
        if not re.match(r'^[a-zA-Z][a-zA-Z0-9._%+-]*@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
            return jsonify({'error': 'Nieprawidłowy format emaila.'}), 400

        # Walidacja numeru telefonu (musi mieć 9 cyfr)
        if not re.match(r"^\d{9}$", tel_nr):
            return jsonify({'error': 'Numer telefonu musi posiadać 9 cyfr.'}), 400

        # Walidacja hasła (musi mieć od 8 do 45 znaków)
        if not (8 <= len(password) <= 45):
            return jsonify({'error': 'Hasło musi mieć od 8 do 45 znaków.'}), 400

        # Walidacja adresu (maksymalnie 255 znaków)
        if len(address) > 255:
            return jsonify({'error': 'Adres może mieć maksymalnie 255 znaków.'}), 400

        # Mapowanie genderu
        gender_mapping = {'Mezczyzna': 0, 'Kobieta': 1}
        if gender not in gender_mapping:
            return jsonify({'error': 'Nieprawidłowa wartość gender.'}), 400

        gender_value = gender_mapping[gender]

        # Wstawianie danych do bazy danych
        db = get_db_connection()
        cursor = db.cursor()
        cursor.execute(f"""
            INSERT INTO users (email, password, tel_nr, gender, address)
            VALUES ('{email}', '{password}', {tel_nr}, {gender_value}, '{address}');
        """)
        
        db.commit()  
        db.close()
        
        return jsonify({'message': 'Zarejestrowano użytkownika pomyślnie!'}), 200
    
    except Exception as err:
        return jsonify({'error': str(err)}), 500

@app.route('/api/strona_logowania/company', methods=['POST']) # ogólnie metoda komuniakcji POST GET się nazywa REST-API podaje dla informacji
def logging_in_company():
    global log_as_user, log_as_company, logged_email
    try:
        # pobranie danych z frontu poprzez JSON
        login = request.json.get('company_login') # pola podane przez front muszą nazywać się company_login i company_password
        password = request.json.get('company_password')
        db = get_db_connection()
        cursor = db.cursor()
        cursor.execute(f"SELECT * FROM companies WHERE email = '{login}' AND password = '{password}';") 
        # zwraca listę dobrych dopasowań
        answer = cursor.fetchall()
        db.commit()
        db.close()

        if len(answer) > 0:
            log_as_company = request.cookies.get('isCompany')
            log_as_user = request.cookies.get('isUser')
            logged_email = request.cookies.get('email')
            return jsonify({'message': 'Zalogowano pomyślnie jako firma!', 'username': login}), 200
        else:
            return jsonify({'message': 'Niepoprawne dane logowania!'}), 401
        
    except Exception as err:
        # gdy pojawi się jakiś błąd zwraca error
        return jsonify({'error': str(err)}), 500

@app.route('/api/strona_rejestracji_firmy/create', methods=['POST'])
def registration_company():
    global public_email_company_reg
    try:
        email = request.json.get('email')
        
        public_email_company_reg = email

        password = request.json.get('password')

        password_repeat = request.json.get('password_repeat')

        company_name = request.json.get('company_name')

        phone = request.json.get('phone')

        description = request.json.get('description')

        nip = request.json.get('nip')
        
        category = request.json.get('type')

        if request.json.get('stacjonarnie') == True:
            type_of_servise = 0
        else:
            type_of_servise = 1

        street_number = request.json.get('street_number')

        city = request.json.get('city')

        post_code = request.json.get('post_code')

        link_page = request.json.get('link_page')

        facebook = request.json.get('facebook')

        tt = request.json.get('tiktok')

        linkedin = request.json.get('linkedin')

        instagram = request.json.get('instagram')

        twitter = request.json.get('twitter')

        pon_start = request.json.get('monday_open')
        pon_stop = request.json.get('monday_close')
        wt_start = request.json.get('tuesday_open')
        wt_stop = request.json.get('tuesday_close')
        sr_start = request.json.get('wednesday_open')
        sr_stop = request.json.get('wednesday_close')
        czw_start = request.json.get('thursday_open')
        czw_stop = request.json.get('thursday_close')
        pt_start = request.json.get('friday_open')
        pt_stop = request.json.get('friday_close')
        sob_start = request.json.get('saturday_open')
        sob_stop = request.json.get('saturday_close')
        nd_start = request.json.get('sunday_open')
        nd_stop = request.json.get('sunday_close')




         # Sprawdź, czy wszystkie pola są obecne
        if not all(email):
            return jsonify({'error': 'Musisz podać adres email by się zarejestrować'}), 400
            

        # Walidacja emaila
        if not re.match(r'^[a-zA-Z][a-zA-Z0-9._%+-]*@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
            return jsonify({'error': 'Nieprawidłowy format adresu email.'}), 400

        if not all(password):
            return jsonify({'error': 'Podaj hasło'}), 400
        
        # Walidacja hasła (musi mieć od 8 do 45 znaków)
        if not (8 <= len(password) <= 45):
            return jsonify({'error': 'Hasło musi mieć od 8 do 45 znaków.'}), 400

        if not password == password_repeat:
            return jsonify({'error': 'Hasła nie są takie same'}), 400

        # Walidacja numeru telefonu (musi mieć 9 cyfr)
        if not re.match(r"^\d{9}$", phone):
            return jsonify({'error': 'Numer telefonu musi posiadać 9 cyfr.'}), 400

        if not re.match(r"^\d{10}$", nip):
             return jsonify({'error': 'Numer NIP musi posiadać 10 cyfr.'}), 400

        if not category:
            return jsonify({'error': 'Podaj kategorię firmy'}), 400
        
        if not street_number:
            return jsonify({'error': 'Podaj ulicę i numer'}), 400
        
        if not city:
            return jsonify({'error': 'Podaj miasto'}), 400
        
        if not post_code:
            return jsonify({'error': 'Podaj kod pocztowy'}), 400


        db = get_db_connection()
        cursor = db.cursor()
        cursor.execute(f"""INSERT INTO companies (Name, City, Address, Logo, Category, Site_link, Facebook_link, Linkedin_link, Instagram_link, X_link,
                   Tiktok_link, Reviews_no, Sum_of_reviews, NIP, tel_nr, description, email, type_of_service, password) 
                   VALUES ('{company_name}', '{city}', '{post_code} {street_number}', '0', '{category}', '{link_page}', '{facebook}', '{linkedin}', 
                   '{instagram}', '{twitter}', '{tt}', 0, 0, {nip}, {phone}, '{description}', '{email}', {type_of_servise}, '{password}');""")
        

        cursor.execute(f"""INSERT INTO opening_hours (company_id, monday_start, monday_end, tuesday_start, tuesday_end, wensday_start, wensday_end, thursday_start, thursday_end, friday_start, friday_end, saturday_start, saturday_end, sunday_start, sunday_end) 
              VALUES ( (SELECT ID FROM companies WHERE (email='{email}')), '{pon_start}:00', '{pon_stop}:00', '{wt_start}:00', '{wt_stop}:00', '{sr_start}:00', '{sr_stop}:00', '{czw_start}:00', '{czw_stop}:00', '{pt_start}:00', '{pt_stop}:00', '{sob_start}:00', '{sob_stop}:00', '{nd_start}:00', '{nd_stop}:00');""")
        db.commit()
        db.close()

        return jsonify({'message': 'Firma została stworzona!'}), 200
    except Exception as err:
        # gdy pojawi się jakiś błąd zwraca error
        return jsonify({'error': str(err)}), 500 
 
@app.route('/api/strona_rejestracji_firmy/usługa', methods=['POST'])
def add_service():
    global public_email_company_reg
    try:
        name = request.json.get('name')

        type = request.json.get('type')

        description = request.json.get('description')

        minuts = request.json.get('duration')
        hours = minuts // 60
        minuty = minuts % 60
        sekundy = 0

        price = request.json.get('price')

        if request.json.get('isApproximate') == True:
            isAprox = 0
        else:
            isAprox = 1

        if not name:
            return jsonify({'error': 'Podaj nazwę usługi'}), 400
        
        if not type:
            return jsonify({'error': 'Podaj typ usługi'}), 400
        
        if price == None or price >= 0:
            return jsonify({'error': 'Usługa musi mieć cenę większą niż 0'}), 400

        db = get_db_connection()
        cursor = db.cursor()
        cursor.execute(f"""INSERT INTO services (company_ID, category, service_name, cost, approximate_cost, execution_time, additional_info) 
                       VALUES ((SELECT ID FROM companies WHERE (email='{request.cookies.get('email')}')), '{type}', '{name}', {price}, {isAprox}, '{hours:02}:{minuty:02}:{sekundy:02}', '{description}');""")
        db.commit()
        db.close()

        return jsonify({'message': 'Usługa została dodana!'}), 200
    except Exception as err:
        return jsonify({'error': str(err)}), 500

@app.route('/api/firma', methods=['POST'])
def return_company():
    try:
        # pobranie danych z frontu poprzez JSON
        firma = request.json.get('firma')

        db = get_db_connection()
        cursor = db.cursor()
        cursor.execute(f"""SELECT ID, Name, City, Address, Logo, Category,
                        Site_link, Facebook_link, Linkedin_link,
                        Instagram_link, X_link, Tiktok_link, Reviews_no,
                        Sum_of_reviews, tel_nr, description 
                       FROM companies WHERE Name = '{firma}';""") 
                
        company = cursor.fetchall()
        
        cursor.execute(f"SELECT picture FROM bookit_main.photos WHERE company_ID = '{company['ID']}';") 

        photos = cursor.fetchall()

        cursor.execute(f"SELECT picture FROM bookit_main.photos WHERE company_ID = '{company['ID']}';") 


        db.close()

        # Przetwarzanie wyników
        result = []
        name = company['Name']
        city = company['City']
        address = company['Address']
        category = company['Category']
        reviews_no = company['Reviews_no']
        sum_of_reviews = company['Sum_of_reviews']
        logo = company['Logo']
        description = company['description']
        photos_no = photos['pics_no']
        if logo:
            logo_bytes = bytes(logo)  # Konwertuj łańcuch znaków na bajty
            logo_base64 = base64.b64encode(logo_bytes).decode('utf-8')
            logo_url = f"data:image/png;base64,{logo_base64}"
        else:
            logo_url = None
        
        result.append({
            'name': name,
            'logo': logo_url,
            'description': description,
            'category': category,
            'address': city + ', ' + address,
            'reviews_no': reviews_no,
            'avg_rating': sum_of_reviews / reviews_no if reviews_no > 0 else 0,
            'photos_no': photos_no
        })

        for photo in photos:
            picture = photo['picture'] 
            if picture:
                picture_bytes = bytes(picture)  # Konwertuj łańcuch znaków na bajty
                picture_base64 = base64.b64encode(picture_bytes).decode('utf-8')
                picture_url = f"data:image/png;base64,{picture_base64}"
            else:
                logo_url = None
            result.append({
                'picture': picture_url
            })

        
        return jsonify({'company': result}), 200
    except Exception as err:
        # Gdy pojawi się jakiś błąd, zwraca error
        return jsonify({'error': str(err)}), 500


@app.route('/api/Strona_zarzadzania_firma', methods=['POST'])
def return_company_details():
    try:
        data = request.json
        email = data.get('email')
        if not email:
            return jsonify({'error': 'No email provided'}), 398

        # Nawiązanie połączenia z bazą danych
        db = get_db_connection()
        cursor = db.cursor()

        # Wykonanie zapytania SQL do pobrania nazwy firmy na podstawie ID
        cursor.execute(f"SELECT Name, Description, Logo, tel_nr, Site_link, Facebook_link, Linkedin_link, Instagram_link, X_link, Tiktok_link FROM companies WHERE email = '{email}';")
        company = cursor.fetchone()

        # Zamknięcie połączenia z bazą danych
        db.close()

        # Jeśli nie ma takiej firmy, zwróć błąd 404
        if not company:
            return jsonify({'error': 'Company not found'}), 399

        result = []
        name = company['Name']
        description = company['Description']
        logo = company['Logo']
        numer = company['tel_nr']
        strona = company['Site_link']
        facebook = company['Facebook_link']
        linkedin = company['Linkedin_link']
        instagram = company['Instagram_link']
        x = company['X_link']
        tiktok = company['Tiktok_link']

        if logo:
            logo_bytes = bytes(logo)  # Konwertuj łańcuch znaków na bajty
            logo_base64 = base64.b64encode(logo_bytes).decode('utf-8')
            logo_url = f"data:image/png;base64,{logo_base64}"
        else:
            logo_url = None


        # Utwórz słownik z nazwą firmy
        result = {
            'name': name,
            'description': description,
            'logo': logo_url,
            'tel_nr': numer,
            'Site_link': strona,
            'Facebook_link': facebook,
            'Linkedin_link': linkedin,
            'Instagram_link': instagram,
            'X_link': x,
            'Tiktok_link': tiktok
        }

        # Zwróć nazwę firmy w formacie JSON
        return jsonify({'data': result}), 200

    except Exception as err:
        # Gdy pojawi się jakiś błąd, zwróć błąd 500
        return jsonify({'error': str(err)}), 500


@app.route('/api/Strona_zarzadzania_firma2', methods=['POST'])
def return_company_hours():
    global logged_email
    try:
        company_id = request.json.get('company_id')
        db = get_db_connection()
        cursor = db.cursor()

        cursor.execute(f"""SELECT o.monday_start, o.monday_end, o.tuesday_start, o.tuesday_end, o.wensday_start, o.wensday_end, o.thursday_start, o.thursday_end, o.friday_start, o.friday_end, o.saturday_start, o.saturday_end, o.sunday_start, o.sunday_end 
                        FROM bookit_main.opening_hours o
                        INNER JOIN bookit_main.companies c ON o.company_ID = c.ID
                        WHERE c.email = %s""", (request.cookies.get('email'),))
        hours = cursor.fetchone()
        db.commit()
        db.close()

        if not hours:
            return jsonify({'error': 'Company not found'}), 404

        mon_start = divmod(hours['monday_start'].seconds // 60, 60)
        mon_start = "{:02d}:{:02d}".format(mon_start[0], mon_start[1])

        mon_end = divmod(hours['monday_end'].seconds // 60, 60)
        mon_end = "{:02d}:{:02d}".format(mon_end[0], mon_end[1])

        tue_start = divmod(hours['tuesday_start'].seconds // 60, 60)
        tue_start = "{:02d}:{:02d}".format(tue_start[0], tue_start[1])

        tue_end = divmod(hours['tuesday_end'].seconds // 60, 60)
        tue_end = "{:02d}:{:02d}".format(tue_end[0], tue_end[1])

        wen_start = divmod(hours['wensday_start'].seconds // 60, 60)
        wen_start = "{:02d}:{:02d}".format(wen_start[0], wen_start[1])

        wen_end = divmod(hours['wensday_end'].seconds // 60, 60)
        wen_end = "{:02d}:{:02d}".format(wen_end[0], wen_end[1])

        thu_start = divmod(hours['thursday_start'].seconds // 60, 60)
        thu_start = "{:02d}:{:02d}".format(thu_start[0], thu_start[1])

        thu_end = divmod(hours['thursday_end'].seconds // 60, 60)
        thu_end = "{:02d}:{:02d}".format(thu_end[0], thu_end[1])

        fri_start = divmod(hours['friday_start'].seconds // 60, 60)
        fri_start = "{:02d}:{:02d}".format(fri_start[0], fri_start[1])

        fri_end = divmod(hours['friday_end'].seconds // 60, 60)
        fri_end = "{:02d}:{:02d}".format(fri_end[0], fri_end[1])

        sat_start = divmod(hours['saturday_start'].seconds // 60, 60)
        sat_start = "{:02d}:{:02d}".format(sat_start[0], sat_start[1])

        sat_end = divmod(hours['saturday_end'].seconds // 60, 60)
        sat_end = "{:02d}:{:02d}".format(sat_end[0], sat_end[1])

        sun_start = divmod(hours['sunday_start'].seconds // 60, 60)
        sun_start = "{:02d}:{:02d}".format(sun_start[0], sun_start[1])

        sun_end = divmod(hours['sunday_end'].seconds // 60, 60)
        sun_end = "{:02d}:{:02d}".format(sun_end[0], sun_end[1])


        result = {
            'monday_start': mon_start,
            'monday_end': mon_end,
            'tuesday_start': tue_start,
            'tuesday_end': tue_end,
            'wensday_start': wen_start,
            'wensday_end': wen_end,
            'thursday_start': thu_start,
            'thursday_end': thu_end,
            'friday_start': fri_start,
            'friday_end': fri_end,
            'saturday_start': sat_start,
            'saturday_end': sat_end,
            'sunday_start': sun_start,
            'sunday_end': sun_end
        }

        return jsonify({'data': result}), 200
    except Exception as err:
        print(err)
        traceback.print_exc()
        return jsonify({'error': str(err)}), 500


@app.route('/api/Strona_zarzadzania_firma/update', methods=['PUT'])
def update_company_details():
    global logged_email
    try:
        data = request.json
        company_id = data.get('company_id')
        field = data.get('field')
        value = data.get('value')

        db = get_db_connection()
        cursor = db.cursor()

        # Dynamically create the SQL query
        sql_query = f"UPDATE companies SET {field} = %s WHERE email = %s"
        cursor.execute(sql_query, (value, request.cookies.get('email')))

        db.commit()
        db.close()

        return jsonify({'message': 'Company details updated successfully'}), 200
    except Exception as err:
        return jsonify({'error': str(err)}), 500


@app.route('/api/Strona_zarzadzania_firma/reservations', methods=['POST'])
def get_reservations():
    global logged_email
    try:
        data = request.json
        company_id = data.get('company_id')
        date = data.get('date')

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT 
                b.booking_time,
                b.ID,
                s.service_name,
                s.category,
                s.execution_time,
                s.additional_info,
                u.email,
                u.tel_nr
            FROM 
                bookit_main.bookings b
            INNER JOIN 
                bookit_main.services s ON b.service_ID = s.ID
            INNER JOIN
                bookit_main.users u ON b.user_ID = u.ID
            INNER JOIN
                bookit_main.companies c ON b.company_ID = c.ID
            WHERE 
                c.email = %s AND DATE(b.booking_time) = %s
            """,
            (request.cookies.get('email'), date)
        )
        reservations = cursor.fetchall()
        conn.close()

        if not reservations:
            return jsonify({'error': 'Reservations not found'}), 404

        result = []
        for res in reservations:
            booking_time = res['booking_time']
            godzina = f"{booking_time.hour:02}:{booking_time.minute:02}"

            execution_time = res['execution_time']
            if isinstance(execution_time, timedelta):
                execution_time_minutes = execution_time.total_seconds() / 60
            else:
                execution_time_minutes = execution_time / 60

            result.append({
                'booking_time': godzina,
                'id_rezerwacji': res['ID'],
                'service_name': res['service_name'],
                'category': res['category'],
                'execution_time': execution_time_minutes,
                'opis': res['additional_info'],
                'email': res['email'],
                'sms': res['tel_nr']
            })

        return jsonify({'data': result}), 200
    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': 'Internal server error'}), 500



@app.route('/api/update_company_hours', methods=['POST'])
def update_company_hours():
    global logged_email
    try:
        data = request.json
        company_id = data.get('company_id')
        hours = data.get('hours')

        print('Received data:', data)  # Dodaj ten wiersz
        if not company_id or not hours:
            return jsonify({'error': 'Missing company_id or hours data'}), 400

        db = get_db_connection()
        cursor = db.cursor()

        query = """
            UPDATE bookit_main.opening_hours
            INNER JOIN  bookit_main.companies ON bookit_main.opening_hours.company_ID = bookit_main.companies.ID
            SET monday_start = %s,
                monday_end = %s,
                tuesday_start = %s,
                tuesday_end = %s,
                wensday_start = %s,
                wensday_end = %s,
                thursday_start = %s,
                thursday_end = %s,
                friday_start = %s,
                friday_end = %s,
                saturday_start = %s,
                saturday_end = %s,
                sunday_start = %s,
                sunday_end = %s
            WHERE bookit_main.companies = %s
        """
        values = (
            hours['monday_start'], hours['monday_end'],
            hours['tuesday_start'], hours['tuesday_end'],
            hours['wensday_start'], hours['wensday_end'],
            hours['thursday_start'], hours['thursday_end'],
            hours['friday_start'], hours['friday_end'],
            hours['saturday_start'], hours['saturday_end'],
            hours['sunday_start'], hours['sunday_end'],
            request.cookies.get('email')
        )

        print('Executing query:', query % values)  # Dodaj ten wiersz

        cursor.execute(query, values)
        db.commit()
        db.close()

        return jsonify({'message': 'Company hours updated successfully'}), 200
    except Exception as err:
        print(err)
        traceback.print_exc()
        return jsonify({'error': str(err)}), 500

@app.route('/api/update_reservation', methods=['POST'])
def update_reservation():
    try:
        data = request.json
        db = get_db_connection()
        reservation = data.get('reservation')
        if not reservation:
            return jsonify({'error': 'No reservation data provided'}), 400

        cursor = db.cursor()

        query = """
                    UPDATE bookit_main.bookings
                    SET booking_time = %s
                    WHERE ID = %s
                """
        values = (
                reservation['booking_time'],
                reservation['id_rezerwacji']
        )

        # Find the reservation in the database
        cursor.execute(query, values)
        db.commit()
        db.close()

        return jsonify({'message': 'Reservation updated successfully'}), 200
    except Exception as e:
        print(e)
        return jsonify({'error': str(e)}), 500

@app.route('/api/delete_reservation', methods=['DELETE'])
def delete_reservation():
    try:
        data = request.json
        db = get_db_connection()
        reservation_id = data.get('id_rezerwacji')
        if not reservation_id:
            return jsonify({'error': 'No reservation ID provided'}), 400

        cursor = db.cursor()

        query = """
                    DELETE FROM bookit_main.bookings
                    WHERE ID = %s
                """
        values = (reservation_id,)

        # Delete the reservation from the database
        cursor.execute(query, values)
        db.commit()
        db.close()

        return jsonify({'message': 'Reservation deleted successfully'}), 200
    except Exception as e:
        print(e)
        return jsonify({'error': str(e)}), 500


ALLOWED_EXTENSIONS = set(['png', 'jpg',  'jpeg'])

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
  
@app.route('/api/strona_rejestracji_firmy/zdjecia', methods=['POST'])
def upload_file():
    global public_email_company_reg
    if 'files[]' not in request.files:
        resp = jsonify({
                "message":'No file part in the request',
                "status": 'failed'          
            })
        return resp
    
    i = 0
    files = request.files.getlist('files[]')
    for file in files:
        if (i==0 and file and allowed_file(file.filename)):
            filedata = file.read()
            db = get_db_connection()
            cursor = db.cursor()
            sql = """UPDATE companies SET Logo=%s WHERE id=(SELECT c.ID FROM (SELECT ID FROM companies WHERE email=%s) AS c)"""
            cursor.execute(sql, (filedata, request.cookies.get('email')))
            db.commit()
            db.close()
        elif i > 0 and file and allowed_file(file.filename):
            filedata = file.read()
            db = get_db_connection()
            cursor = db.cursor()
            sql = """INSERT INTO photos (company_ID, picture) VALUES ((SELECT ID FROM companies WHERE email=%s), %s)"""
            cursor.execute(sql, (request.cookies.get('email'), filedata))
            db.commit()
            db.close()
        else:
            resp = jsonify({
            "message":'Nie dodano zdjęc',
            "status": 'unsuccess'          
            })
            return resp
        i=i+1
    resp = jsonify({
            "message":'Files successfully uploaded filename',
            "status": 'success'          
        })
    return resp

@app.route('/api/edit_profile', methods=['POST'])
def edit_profile():
    if not log_as_user:
      return jsonify({'error': 'Nie zalogowany.'}), 401

    global logged_email

    db = get_db_connection()
    cursor = db.cursor()

    print(request.cookies.get('email'))
    email = request.json.get('email')
    nrTelefonu = request.json.get('nrTelefonu')
    miasto = request.json.get('miasto')
    plec = request.json.get('plec')
    stareHaslo = request.json.get('stareHaslo')
    noweHaslo = request.json.get('noweHaslo')
    powtorzNoweHaslo = request.json.get('powtorzNoweHaslo')

    def update_numer_telefonu():
        if not re.match(r"^\d{9}$", nrTelefonu):
            return jsonify({'error': 'Nieprawidłowy format numeru telefonu.'}), 400

        query = "UPDATE users SET tel_nr = %s WHERE email = %s"
        cursor.execute(query, (nrTelefonu, request.cookies.get('email')))
        db.commit()
        print("zaktualizowano numer telefonu!")

    def update_miasto():
        if not re.match(r"^[a-zA-ZąćęłńóśźżĄĆĘŁŃÓŚŹŻ\- ]+$", miasto):
            return jsonify({'error': 'Nieprawidłowa nazwa miasta.'}), 400

        query = "UPDATE users SET address = %s where email = %s"
        cursor.execute(query, (miasto, request.cookies.get('email')))
        db.commit()
        print("zaktualizowano miasto!")

    def update_plec():
        if len(plec) == 0:
            return jsonify({'error': 'Nieprawidłowa plec.'}), 400

        nowaPlec = 0 if plec == "Mezczyzna" else 1
        query = "UPDATE users SET gender = %s where email = %s"
        cursor.execute(query, (nowaPlec, request.cookies.get('email')))
        db.commit()

        print("Plec została zaktualizowana!")

    def update_haslo():
        if not(len(stareHaslo) > 0 and len(noweHaslo) > 0 and len(powtorzNoweHaslo) > 0):
            return jsonify({'error': 'Nieprawidłowe hasła.'}), 400

        #wyciaganie starego hasla z bazy
        query = "SELECT password FROM users WHERE email = %s"
        cursor.execute(query, (request.cookies.get('email')))
        rawData = cursor.fetchall()
        haslo = rawData[0]['password']

        #jesli stareHaslo sie zgadza z haslem w bazie
        if not (stareHaslo == haslo and noweHaslo == powtorzNoweHaslo):
            return jsonify({'error': 'Hasla są niepoprawne.'}), 400

        query = "UPDATE users SET password = %s WHERE email = %s"
        cursor.execute(query, (noweHaslo, request.cookies.get('email')))
        db.commit()
        print("zaktualizowano haslo!")

    def update_email():
        if not re.match(r'^[a-zA-Z][a-zA-Z0-9._%+-]*@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
            return jsonify({'error': 'Nieprawidłowy format emaila.'}), 400

        query = "UPDATE users SET email = %s where email = %s"
        cursor.execute(query, (email, request.cookies.get('email')))
        db.commit()
        print("Email zaktualizowany pomyślnie")

    def printUsersTable():
        query = 'select * from users'
        cursor.execute(query)

        db.close()
        rows = cursor.fetchall()
        for row in rows:
            print(row)

    try:
        update_numer_telefonu()

        update_miasto()

        update_plec()

        update_haslo()

        update_email()

        return jsonify({'message': 'Profil zaktualizowany pomyślnie.'}), 200

    except Exception as err:
        print("Nie udało się zaktualizować profilu:", str(err))
        return jsonify({'error': 'Wystąpił błąd.'}), 500

@app.route('/api/user_reservations', methods=['GET', 'POST'])
def get_user_reservations():
    def send_bookings_query(user_email):
        db = get_db_connection()
        cursor = db.cursor()

        query = """SELECT companies.name AS businessName, companies.Address AS location, services.service_name AS service, services.cost AS price, bookings.booking_time AS date, companies.email AS company_email, bookings.recensed AS user_rating, bookings.id as booking_id
                   FROM users
                   JOIN bookings ON users.id = bookings.user_ID
                   JOIN services ON services.id = bookings.service_ID
                   JOIN companies ON companies.id = services.company_ID
                   WHERE users.email = %s
                   """

        cursor.execute(query, (user_email,))
        all_bookings = cursor.fetchall()
        db.close()

        # Zmiana nazw kluczy i formatowanie daty
        formatted_bookings = []
        for booking in all_bookings:
            formatted_booking = {
                'businessName': booking['businessName'],
                'location': booking['location'],
                'service': booking['service'],
                'price': booking['price'],
                'date': booking['date'].strftime('%Y-%m-%d %H:%M:%S'),  # Formatowanie daty do stringa
                'company_email': booking['company_email'],
                'user_rating': booking['user_rating'],
                'booking_id': booking['booking_id']
            }
            formatted_bookings.append(formatted_booking)
        return formatted_bookings

    try:
        user_email = request.headers.get('User-Email')  # Pobierz email z nagłówków
        if not user_email:
            return jsonify({'error': 'User email is required'}), 400

        all_bookings = send_bookings_query(user_email)
        return jsonify(all_bookings), 200

    except Exception as err:
        return jsonify({'error': str(err)}), 500


@app.route('/api/services')
def get_services_by_company_id():
    try:
        db = get_db_connection()
        cursor = db.cursor()

        company_id = request.args.get('company_id')
        if not company_id:
            return jsonify({"error": "Missing company_id"}), 400

        query = "SELECT ID, service_name, cost, execution_time, approximate_cost, additional_info FROM services WHERE company_ID = %s"
        cursor.execute(query, (company_id,))
        services = cursor.fetchall()

        service_list = [{
            "id": service['ID'],
            "name": service['service_name'], 
            "cost": service['cost'], 
            "time": str(service['execution_time']),
            "time_minutes": service['execution_time'].total_seconds() // 60,
            "approximate_cost": service['approximate_cost'],
            "additional_info": service['additional_info']
            } 
            
            for service in services
        ]
        return jsonify(service_list)
        

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        db.close()

@app.route('/api/user_info')
def get_user_info_by_id():
    try:
        db = get_db_connection()
        cursor = db.cursor()

        user_id = request.args.get('user_id')
        if not user_id:
            return jsonify({"error": "Missing user_id"}), 400

        query = "SELECT ID, email, password, tel_nr, gender, address FROM users WHERE ID = %s"
        cursor.execute(query, (user_id,))
        
        user = cursor.fetchone()
        if not user:
            return jsonify({"error": "User not found"}), 404

        user_info = {
            "id": user['ID'],
            "email": user['email'], 
            "password": user['password'], 
            "tel_nr": user['tel_nr'],
            "gender": user['gender'],
            "address": user['address']
        }

        return jsonify(user_info)
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        db.close()

@app.route('/api/add_booking', methods=['POST'])
def add_booking():
    try:
        print("TERAZ WYKONUJE ADD BOOKING")
        db = get_db_connection()
        cursor = db.cursor()

        data = request.json

        company_id = data['company_id']
        user_id = data['user_id']
        service_id = data['service_id']
        booking_datetime = data['booking_datetime']
        booking_date = data['booking_date']
        confirm_mail = data['confirm_mail']
        reminder_mail = data['reminder_mail']
        confirm_sms = data['confirm_sms']
        reminder_sms = data['reminder_sms']
        booking_time = data['time'] 
        total_time_minutes = data['totalTime'] 

        start_time = datetime.strptime(booking_time, '%H:%M')
        end_time = start_time + timedelta(minutes=total_time_minutes)
                
        if free_day.is_free_day(company_id, booking_date, start_time, end_time) and free_day.is_booking_time_free(company_id, booking_date, booking_time, total_time_minutes):
            query = """
                INSERT INTO bookings (company_id, user_id, service_id, booking_time, confirm_mail, reminder_mail, confirm_sms, reminder_sms, 0)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """
            cursor.execute(query, (company_id, user_id, service_id, booking_datetime, confirm_mail, reminder_mail, confirm_sms, reminder_sms))
            db.commit()

            print("Executing query booking: ", query)

            return jsonify({"message": "Booking added successfully"}), 201
        else:
            print("Not a free day for booking")
            return jsonify({"message": "That day is not free"}), 201

    except Exception as e:
        print("Error in booking:", str(e))
        return jsonify({"error": str(e)}), 500
    finally:
        db.close()

@app.route('/api/add_to_day_schedule', methods=['POST'])
def add_to_day_schedule():
    try:        
        db = get_db_connection()
        cursor = db.cursor()

        data = request.json    

        company_id = data['company_id']
        booking_date = data['date']  # 'YYYY-MM-DD' format    
        booking_time = data['time']  # 'HH:MM' format
        total_time_minutes = data['totalTime']  # Total time in minutes

        booking_datetime = datetime.strptime(booking_date, "%Y-%m-%d")
        reminder_date = booking_datetime - timedelta(days=1) #Data do przesłania do scheduled_email jako reminder email
        feedback_date = booking_datetime + timedelta(days=1) #Data do przesłania do scheduled_email jako email feedbackowy
        reminder_date_str = reminder_date.strftime("%Y-%m-%d")
        feedback_date_str = feedback_date.strftime("%Y-%m-%d")
        
        email = data['email']
        service_ids = data['service_ids']
        total_cost = data['total_cost']        

        # Calculate the number of slots to fill
        slots_to_fill = total_time_minutes // 30
        if total_time_minutes % 30 != 0:
            slots_to_fill += 1
        
        # Calculate the start and end slots
        start_time = datetime.strptime(booking_time, '%H:%M')
        end_time = start_time + timedelta(minutes=total_time_minutes)
        
        # Check if the record for the given date already exists
        cursor.execute("SELECT id FROM day_schedule WHERE company_id = %s AND Date = %s", (company_id, booking_date))
        record = cursor.fetchone()

        if free_day.is_free_day(company_id, booking_date, start_time, end_time) and free_day.is_booking_time_free(company_id, booking_date, booking_time, total_time_minutes):
            if record:
                # Update existing record
                current_time = start_time                
                while current_time < end_time:                        
                    slot_column = current_time.strftime('%H:%M')
                    query = f"""
                        UPDATE day_schedule
                        SET `{slot_column}` = 1
                        WHERE company_ID = {company_id} AND Date = '{booking_date}'
                    """
                    
                    cursor.execute(query)                    
                    record = cursor.fetchone()                    
                    current_time += timedelta(minutes=30)        
                db.commit()                            
                
                
            else:
                # Insert new record
                columns = ["company_id", "Date"] + [start_time.strftime('`%H:%M`')]
                values = [company_id, f"'{booking_date}'", 1]
                current_time = start_time + timedelta(minutes=30)

                while current_time < end_time:
                    columns.append(current_time.strftime('`%H:%M`'))
                    values.append(1)
                    current_time += timedelta(minutes=30)

                query = f"""
                    INSERT INTO day_schedule ({', '.join(columns)})
                    VALUES ({', '.join(map(str, values))})
                """
                print("Executing query schedule: ", query)
                cursor.execute(query)
                print("Insertion successful")  
                db.commit()                      
                
            format_strings = ','.join(['%s'] * len(service_ids))
            query = f"SELECT service_name, cost FROM services WHERE ID IN ({format_strings})"
            cursor.execute(query, tuple(service_ids))
            service_names = cursor.fetchall()
            service_names_str = ', '.join([service['service_name'] for service in service_names])        

            query = "SELECT name, address, city FROM companies WHERE %s"
            cursor.execute(query, (company_id,))
            company = cursor.fetchone()            

            message = (
                f"Szanowny Użytkowniku,\n\n"
                f"Dziękujemy za skorzystanie z naszego serwisu Bookit!\n\n"
                f"Potwierdzamy, że zarezerwował(a) Pan(i) usługę(i) {service_names_str} oferowaną(e) przez firmę {company['name']}. Poniżej znajdują się szczegóły rezerwacji:\n\n"                
                f"Usługa(i): {service_names_str}\n"
                f"Firma: {company['name']}\n"
                f"Data: {booking_date}\n"
                f"Godzina: {booking_time}\n"
                f"Adres: {company['address']}, {company['city']}\n"
                f"Koszt: {total_cost}.00 złotych\n\n"
                f"Prosimy o przybycie na miejsce na kilka minut przed umówioną godziną, aby zapewnić sprawne przeprowadzenie usługi.\n\n"
                f"W razie jakichkolwiek pytań lub wątpliwości, prosimy o kontakt z firmą przez numer telefonu: 512958315.\n"
                f"Jeśli chcesz odwołać wizytę lub podejrzeć szczegóły, udaj się na stronę Bookit.great-site.net. Informacja będzie dostępna w twoim profilu.\n"
                f"Pozdrawiamy, \n\nZespół Bookit"
            )

            message = message.replace("\n", "<br>")

            mail_sender.send_mail(
                email,
                "Potwierdzenie rezerwacji usługi w serwisie Bookit",
                message
            )

            message = (
                f"Szanowny Użytkowniku,\n\n"
                f"Przypominamy, że jutro odbędzie się Twoja zarezerwowana usługa w serwisie Bookit. Poniżej znajdują się szczegóły rezerwacji: {company['name']}.\n"
                f"Szczegóły wizyty:\n"
                f"Usługa(i): {service_names_str}\n"
                f"Firma: {company['name']}\n"
                f"Data: {booking_date}\n"
                f"Godzina: {booking_time}\n"
                f"Adres: {company['address']}, {company['city']}\n"
                f"Koszt: {total_cost}.00 złotych\n\n"
                f"Prosimy o przybycie na miejsce na kilka minut przed umówioną godziną, aby zapewnić sprawne przeprowadzenie usługi.\n"
                f"W razie jakichkolwiek pytań lub wątpliwości, prosimy o kontakt z firmą przez numer telefonu: 512958315.\n"
                f"Jeśli chcesz odwołać wizytę lub podejrzeć szczegóły, udaj się na stronę Bookit.great-site.net. Informacja będzie dostępna w twoim profilu.\n"
                f"Pozdrawiamy, \nZespół Bookit"
            )

            message = message.replace('\n', '<br>')
            mail_sender.add_scheduled_email(
                email, 
                "Przypomnienie o jutrzejszej wizycie w serwisie Bookit",
                message,
                reminder_date_str                            
            )

            message = (
                f"Szanowny Użytkowniku,\n\n"
                f"Dziękujemy za skorzystanie z usługi w serwisie Bookit! Mamy nadzieję, że Twoja wizyta w firmie {company['name']} była satysfakcjonująca\n\n"
                f"Chcielibyśmy poprosić o chwilę Twojego czasu, abyś podzielił się swoją opinią na temat świadczonych przez nas usług. Twoja opinia jest dla nas niezwykle ważna i pomoże nam ciągle doskonalić nasze usługi.\n\n"
                f"Ocenić swoje wizyty możesz w profilu użytkownika, na platformie Bookit.great-site.net\n\n"
                f"Dziękujemy za współpracę i mamy nadzieję, że będziemy mieli przyjemność obsługiwać Cię ponownie w przyszłości.\n\n"        
                f"Pozdrawiamy, \nZespół Bookit"
            )
            
            message = message.replace('\n', '<br>')
            mail_sender.add_scheduled_email(
                email, 
                f"Ocena usługi firmy {company['name']}",
                message,
                feedback_date_str
            )


            return jsonify({"message": "Day schedule updated successfully", "is_free": 1}), 201

        else:            
            return jsonify({"message": "That day is not free", "is_free": 0}), 201

    except Exception as e:
        print("Error schedule: ", str(e))
        return jsonify({"error": str(e)}), 500
    finally:
        db.close()

@app.route('/api/Strona_firmy', methods=['POST'])
def return_company_info():
    try:
        # Pobranie danych z przesłanego żądania POST
        company_name = request.json.get('company_name')

        # Nawiązanie połączenia z bazą danych
        db = get_db_connection()
        cursor = db.cursor()

        # Wykonanie zapytania SQL do pobrania nazwy firmy na podstawie ID
        cursor.execute("SELECT Name, Description, Logo, tel_nr, city, address FROM companies WHERE Name = '%s'", (company_name,))
        company = cursor.fetchone()

        # Zamknięcie połączenia z bazą danych
        db.close()

        # Jeśli nie ma takiej firmy, zwróć błąd 404
        if not company:
            return jsonify({'error': 'Company not found'}), 404

        result = []
        name = company['Name']
        description = company['Description']
        logo = company['Logo']
        numer = company['tel_nr']
        city = company['city']
        address = company['address']

        if logo:
            logo_bytes = bytes(logo)  # Konwertuj łańcuch znaków na bajty
            logo_base64 = base64.b64encode(logo_bytes).decode('utf-8')
            logo_url = f"data:image/png;base64,{logo_base64}"
        else:
            logo_url = None


        # Utwórz słownik z nazwą firmy
        result = ({
            'name': name,
            'description': description,
            'logo': logo_url,
            'numer': numer,
            'city': city,
            'address': address
        })

        # Zwróć nazwę firmy w formacie JSON
        return jsonify(result), 200
    except Exception as err:
        # Gdy pojawi się jakiś błąd, zwróć błąd 500
        return jsonify({'error': str(err)}), 500

@app.route('/api/user_page/oceny', methods=['POST'])
def ocenianie():
    try:
        email = request.json.get("email")
        ocena = request.json.get("ocena")
        booking_id = request.json.get("booking_id")

        db = get_db_connection()
        cursor = db.cursor()

        cursor.execute(f"SELECT Reviews_no, Sum_of_reviews FROM companies WHERE (email='{email}');")
        dane = cursor.fetchone()
        db.commit()

        ocenka = dane['Sum_of_reviews']
        liczba = dane['Reviews_no']
        ocenka = ocenka + ocena
        liczba = liczba + 1

        cursor.execute(f"UPDATE companies SET Reviews_no={liczba}, Sum_of_reviews={ocenka} WHERE ID=(SELECT c.ID FROM (SELECT ID FROM companies WHERE email='{email}') AS c);")

        db.commit()

        cursor.execute(f"UPDATE bookings SET recensed=1 WHERE ID={booking_id};")
        db.commit()

        db.close()

        return jsonify("dzialam"), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
""""   
@app.route('/api/czy_zalogowano')
def czy_zalogowano():
    global session, log_as_user, log_as_company, logged_email
    company_or_user = 0 # 0 - zalogowano jako uzytkownik 1 - zalogowano jako firma
    try:
        company_or_user = 0 # 0 - zalogowano jako uzytkownik 1 - zalogowano jako firma
        if request.cookies.get('isCompany') == True or request.cookies.get('isUser') == True:
            company_or_user = 1
        else:
            company_or_user = 0
        info = {
            "email": request.cookies.get('email'), 
            "company_or_user": company_or_user
        }

        print(info + 'dupa')
        return jsonify(info)
    except Exception as e:
        print('dupa nie dziala')
        return jsonify({"error": str(e)}), 500
    

@app.route('/api/wyloguj')
def wyloguj():
    global session, log_as_user, log_as_company, logged_email
    try:
        session['logged_email'] = ""
        session['log_as_company'] = False
        session['log_as_user'] = False

        return jsonify({'message': 'Zalogowano pomyślnie!'}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
"""
#Zmiany tutaj wynikaja z uzycia APSchedulera
if __name__ == '__main__':
    scheduler = BackgroundScheduler()
    # Tworzenie procesów dla Flask i schedulera
    scheduler.add_job(func=mail_sender.send_scheduled_emails, trigger="cron", hour=6, minute=00, second=10)
    scheduler.add_job(func=mail_sender.delete_old_logs, trigger="cron", day_of_week='mon')

    scheduler.start()

    try:
        #Zeby scheduler nie wywoływał funkcji dwukrotnie, trzeba wyłączyć reloader. 
        #reloader automatycznie odpalał serwer po kazdej zmianie przy ctrl+s
        app.run(debug=False, use_reloader=False)
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()
