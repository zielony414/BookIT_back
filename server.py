from flask import Flask, request, jsonify
import pymysql
import base64
import re
from werkzeug.utils import secure_filename #pip install Werkzeug

app = Flask(__name__)

#----------------------------------------------------------------------------------------------------------------------
# connection with database
def get_db_connection():
    return pymysql.connect(
        charset = "utf8mb4",
        connect_timeout = 500,
        cursorclass=pymysql.cursors.DictCursor,
        # db = config('DB_DATABASE'),
        # host = config('DB_HOST'),
        # password = config('DB_PASS'),
        # read_timeout = 500,
        # port = config('DB_PORT'),
        # user = config('DB_USER'),
        # write_timeout = 500,
        db="bookit_main",
        host="bookit-bookit.f.aivencloud.com",
        password="AVNS_lK1EnykcZ5J6TflOpru",
        read_timeout=500,
        port=22474,
        user="avnadmin",
        write_timeout=500,
    )

public_email_company_reg = "contact@bury.com" # zmienna potrzebna do rejestracji firmy
log_as_company = False # True - zalogowano jako firma
log_as_user = False # True - zalogowano jako użytkownik
logged_email = "" # EMAIL ZALOGOWANEGO UŻYTKOWNIKA LUB FIRMY

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
        db = get_db_connection()
        cursor = db.cursor()
        cursor.execute("SELECT Name, Logo, description FROM companies;")
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
        
    
# dekorator, wpisuje się to na froncie w funkcji fetch() i wtedy jest wywoływana ta funkcja poniżej
@app.route('/api/strona_logowania/user', methods=['POST']) # ogólnie metoda komuniakcji POST GET się nazywa REST-API podaje dla informacji
def logging_in_user():
    global log_as_user, log_as_company, logged_email
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
            log_as_user = True
            log_as_company = False
            logged_email = login
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
        name = request.json.get('name')
        email = request.json.get('email')
        password = request.json.get('password')
        tel_nr = request.json.get('phone')
        gender = request.json.get('gender')
        address = request.json.get('address')

        # Sprawdź, czy wszystkie pola są obecne
        if not all([name, email, password, tel_nr, gender, address]):
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
        cursor.execute("""
            INSERT INTO users (name, email, password, tel_nr, gender, address) 
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (name, email, password, tel_nr, gender, address))
        
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
            log_as_company = True
            log_as_user = False
            logged_email = login
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
        if not re.match(r'^[a-zA-Z][a-zA-Z0-9._%+-]*@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
            return jsonify({'error': 'Nieprawidłowy format emaila.'}), 401
        public_email_company_reg = email
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
        db = get_db_connection()
        cursor = db.cursor()
        cursor.execute(f"""INSERT INTO companies (Name, City, Address, Logo, Category, Site_link, Facebook_link, Linkedin_link, Instagram_link, X_link,
                    Tiktok_link, Reviews_no, Sum_of_reviews, NIP, tel_nr, description, email, type_of_service, password) 
                    VALUES ('{company_name}', '{city}', '{post_code} {street_number}', '0', '{category}', '{link_page}', '{facebook}', '{linkedin}', 
                    '{instagram}', '{twitter}', '{tt}', 0, 0, '{nip}', '{phone}', '{description}', '{email}', '{type_of_servise}', '{password}');""")

        cursor.execute(f"""INSERT INTO opening_hours (company_id, monday_start, monday_end, tuesday_start, tuesday_end, wensday_start, wensday_end, thursday_start, thursday_end, friday_start, friday_end, saturday_start, saturday_end, sunday_start, sunday_end) 
              VALUES ( (SELECT ID FROM companies WHERE (email='{email}')), '{pon_start}', '{pon_stop}', '{wt_start}', '{wt_stop}', '{sr_start}', '{sr_stop}', '{czw_start}', '{czw_stop}', '{pt_start}', '{pt_stop}', '{sob_start}', '{sob_stop}', '{nd_start}', '{nd_stop}');""")
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
        hours = request.json.get('hours')
        minutes = request.json.get('minutes')
        price = request.json.get('price')

        # poprawić approximate_cost bo niewiem co to jest i dodać typ usługi 
        db = get_db_connection()
        cursor = db.cursor()
        cursor.execute(f"""INSERT INTO services (company_ID, category, service_name, cost, approximate_cost, execution_time, additional_info) 
                       VALUES ((SELECT ID FROM companies WHERE (email='{public_email_company_reg}')), '{type}', '{name}', '{price}', '0', '{hours * 60 + minutes}', '{description}');""")
        db.commit()
        db.close()

        return jsonify({'message': 'Usługa została dodana!'}), 200
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

        if kategoria == 'Wszystkie':
            kategoria = ''

        if sortowanie == 'Najwyższa ocena':
            
            cursor.execute(f"""SELECT * 
                            CASE
                                WHEN Reviews_no > 0 THEN Sum_of_reviews / Reviews_no
                                ELSE 0
                            END AS srednia_ocena 
                            FROM companies WHERE City = '{miasto}' AND Category = '{kategoria}' 
                            ORDER BY srednia_ocena DESC ;""") 
            
        elif sortowanie == 'Najpopularniejsze':
            cursor.execute(f"""SELECT * 
                            FROM companies WHERE City = '{miasto}' AND Category = '{kategoria}' 
                            ORDER BY Reviews_no DESC ;""")
        
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
                'avg_rating': sum_of_reviews / reviews_no if reviews_no > 0 else 0
            })
        return jsonify({'companies': result}), 200
    except Exception as err:
        # Gdy pojawi się jakiś błąd, zwraca error
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

@app.route('/api/Strona_zarządzania_firmą', methods=['POST'])
def return_company_details():
    try:
        # Pobranie danych z przesłanego żądania POST
        company_id = request.json.get('company_id')

        # Nawiązanie połączenia z bazą danych
        db = get_db_connection()
        cursor = db.cursor()

        # Wykonanie zapytania SQL do pobrania nazwy firmy na podstawie ID
        cursor.execute("SELECT Name, Description, Logo, tel_nr FROM companies WHERE ID = %s", (company_id,))
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
            'numer': numer
        })

        # Zwróć nazwę firmy w formacie JSON
        return jsonify(result), 200
    except Exception as err:
        # Gdy pojawi się jakiś błąd, zwróć błąd 500
        return jsonify({'error': str(err)}), 500


@app.route('/api/Strona_zarządzania_firmą2', methods=['POST'])
def return_company_hours():
    try:
        company_id = request.json.get('company_id')
        db = get_db_connection()
        cursor = db.cursor()

        #TODO może ktoś ogarnie dlaczego to nie cziała

        cursor.execute(f"""SELECT monday_start FROM opening_hours WHERE ID = {company_id}""")
        hours = cursor.fetchone()
        db.commit()
        db.close()


        if not hours:
            return jsonify({'error': 'Company not found'}), 404

        time_value = hours[0]
        formatted_time = time_value.strftime('%H:%M')
        #monday_start = hours['monday_start']
        result = {
            'monday_start': formatted_time
        }


        return jsonify(result), 200
    except Exception as err:
        print(err)
        return jsonify({'error': str(err)}), 500

 
ALLOWED_EXTENSIONS = set(['png', 'jpg',  'jpeg'])

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
  
@app.route('/api/strona_rejestracji_firmy/zdjecia', methods=['POST'])
def upload_file():
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
            cursor.execute(sql, (filedata, public_email_company_reg))
            db.commit()
            db.close()
        elif i > 0 and file and allowed_file(file.filename):
            filedata = file.read()
            db = get_db_connection()
            cursor = db.cursor()
            sql = """INSERT INTO photos (company_ID, picture) VALUES ((SELECT ID FROM companies WHERE email=%s), %s)"""
            cursor.execute(sql, (public_email_company_reg, filedata))
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

@app.route('/edit_profile', methods=['POST'])
def edit_profile():

    if not log_as_user:
        return jsonify({'error': 'Nie zalogowany.'}), 401

    email = request.json.get('email')
    nrTelefonu = request.json.get('nrTelefonu')
    miasto = request.json.get('miasto')
    plec = request.json.get('plec')
    stareHaslo = request.json.get('stareHaslo')
    noweHaslo = request.json.get('noweHaslo')
    powtorzNoweHaslo = request.json.get('powtorzNoweHaslo')

    db = get_db_connection()
    cursor = db.cursor()

    try:
        if len(nrTelefonu) > 0:
            if not re.match(r"^\+\d{11}$", nrTelefonu):
                return jsonify({'error': 'Nieprawidłowy format numeru telefonu.'}), 400

            else:
                query = 'UPDATE users SET tel_nr = ? WHERE email = ?', (nrTelefonu, logged_email)
                cursor.execute(query)
                print("zaktualizowano numer telefonu!")

        if miasto and len(miasto) > 0:
            if not re.match(r"^[a-zA-ZąćęłńóśźżĄĆĘŁŃÓŚŹŻ\- ]+$", miasto):
                return jsonify({'error': 'Nieprawidłowa nazwa miasta.'}), 400
            cursor.execute('UPDATE users SET city = ? WHERE email = ?', (miasto, logged_email))
            print("zaktualizowano miasto!")

        if len(plec) == 0:
            query = f'UPDATE users SET gender = {plec} WHERE email = {logged_email};'
            db = get_db_connection()
            cursor = db.cursor()
            cursor.execute(query)
            db.close()
            print("zaktualizowano plec, jestes chlopem!")
        else:
            query = f'UPDATE users SET gender = {plec} WHERE email = {logged_email};'
            db = get_db_connection()
            cursor = db.cursor()
            cursor.execute(query)
            db.close()
            print("zaktualizowano plec, jestes baba!")

        if len(stareHaslo) > 0 and len(noweHaslo) > 0 and len(powtorzNoweHaslo) > 0:
            #wyciaganie starego hasla z bazy
            query = f'SELECT password FROM users WHERE email = {logged_email};'
            db = get_db_connection()
            cursor = db.cursor()
            cursor.execute(query)
            haslo = cursor.fetchone()
            db.close()

            #jesli stareHaslo sie zgadza z haslem w bazie
            if stareHaslo == haslo and noweHaslo == powtorzNoweHaslo:
                query = f'UPDATE users SET password = {noweHaslo} WHERE email = {logged_email};'
                db = get_db_connection()
                cursor = db.cursor()
                cursor.execute(query)
                db.close()
                print("zaktualizowano haslo!")

        ##sprawdzanie czy pola są dobre
        if email and len(email) > 0:
            if not re.match(r'^[a-zA-Z][a-zA-Z0-9._%+-]*@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
                return jsonify({'error': 'Nieprawidłowy format emaila.'}), 400
            cursor.execute('UPDATE users SET email = ? WHERE email = ?', (email, logged_email))
            print("Email zaktualizowany pomyślnie")
            logged_email = email

        db.commit()
        db.close()
        return jsonify({'message': 'Profil zaktualizowany pomyślnie.'}), 200


    except Exception as err:
        print("Błąd zapytania SQL:", str(err))
        return jsonify({'error': 'Wystąpił błąd.'}), 500

@app.route('/api/services')
def get_services_by_company_id():
    try:
        db = get_db_connection()
        cursor = db.cursor()

        company_id = request.args.get('company_id')
        if not company_id:
            return jsonify({"error": "Missing company_id"}), 400

        query = "SELECT ID, service_name, cost, execution_time, approximate_cost FROM services WHERE company_ID = %s"
        cursor.execute(query, (company_id,))
        services = cursor.fetchall()

        service_list = [{
            "id": service['ID'],
            "name": service['service_name'], 
            "cost": service['cost'], 
            "time": str(service['execution_time']),
            "time_minutes": service['execution_time'].total_seconds() // 60,
            "approximate_cost": service['approximate_cost']
            } 
            
            for service in services
        ]
        return jsonify(service_list)
        

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        db.close()

@app.route('/api/add_booking', methods=['POST'])
def add_booking():
    try:
        db = get_db_connection()
        cursor = db.cursor()

        data = request.json
        print("Received data:", data)

        company_id = data['company_id']
        user_id = data['user_id']
        service_id = data['service_id']
        booking_time = data['booking_time']
        confirm_mail = data['confirm_mail']
        reminder_mail = data['reminder_mail']
        confirm_sms = data['confirm_sms']
        reminder_sms = data['reminder_sms']

        query = """
            INSERT INTO bookings (company_id, user_id, service_id, booking_time, confirm_mail, reminder_mail, confirm_sms, reminder_sms)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """
        cursor.execute(query, (company_id, user_id, service_id, booking_time, confirm_mail, reminder_mail, confirm_sms, reminder_sms))
        db.commit()

        return jsonify({"message": "Booking added successfully"}), 201
    except Exception as e:
        print("Error:", str(e))
        return jsonify({"error": str(e)}), 500
    finally:
        db.close()

if __name__ == '__main__':
    app.run(debug=True)
