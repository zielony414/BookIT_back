from flask import Flask, request, jsonify
import pymysql
import base64
import re

import traceback #do usunięcia
from datetime import timedelta
import datetime

app = Flask(__name__)

#----------------------------------------------------------------------------------------------------------------------
# connection with database
def get_db_connection():
    return pymysql.connect(
        charset="utf8mb4",
        connect_timeout=500,
        cursorclass=pymysql.cursors.DictCursor,
        db="bookit_main",
        host="bookit-bookit.f.aivencloud.com",
        password="AVNS_lK1EnykcZ5J6TflOpru",
        read_timeout=500,
        port=22474,
        user="avnadmin",
        write_timeout=500,
    )

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
        
        return jsonify({'message': 'Zalogowano pomyślnie!'}), 200
    
    except Exception as err:
        return jsonify({'error': str(err)}), 500

@app.route('/api/strona_logowania/company', methods=['POST']) # ogólnie metoda komuniakcji POST GET się nazywa REST-API podaje dla informacji
def logging_in_company():
    try:
        # pobranie danych z frontu poprzez JSON
        login = request.json.get('company_login') # pola podane przez front muszą nazywać się company_login i company_password
        password = request.json.get('company_password')
        db = get_db_connection()
        cursor = db.cursor()
        cursor.execute(f"SELECT * FROM companies WHERE email = '{login}' AND password = '{password}';") 
        # zwraca listę dobrych dopasowań
        answer = cursor.fetchall()
        db.close()

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
        db = get_db_connection()
        cursor = db.cursor()
        cursor.execute(f"""INSERT INTO companies (Name, Adress, #Sector, #Logo, Category, Site_link, Facebook_link, Linkedin_link, Instagram_link, X_link,
                    Tiktok_link, Reviews_no, Sum_of_reviews, NIP, tel_nr, description, email, type_of_service, password) 
                    VALUES ('{company_name}', '{city} {street_number} {post_code}', #Sector, #Logo, '{category}', '{link_page}', '{facebook}', '{linkedin}', 
                    '{instagram}', '{twitter}', '{tt}', 0, 0, '{nip}', '{phone}', '{description}', '{email}', '{type_of_servise}', '{password}');""")

        cursor.execute(f"""INSERT INTO opening_hours (company_id, monday_start, monday_end, tuesday_start, tuesday_end, wensday_start, wensday_end, thursday_start, thursday_end, friday_start, friday_end, saturday_start, saturday_end, sunday_start, sunday_end) 
              VALUES ( (SELECT ID FROM companies WHERE (email='{email}')), '{pon_start}', '{pon_stop}', '{wt_start}', '{wt_stop}', '{sr_start}', '{sr_stop}', '{czw_start}', '{czw_stop}', '{pt_start}', '{pt_stop}', '{sob_start}', '{sob_stop}', '{nd_start}', '{nd_stop}');""")
        db.close()

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
        db = get_db_connection()
        cursor = db.cursor()
        cursor.execute(f"""INSERT INTO services (company_ID, service_name, cost, #approximate_cost, execution_time, additional_info) 
                       VALUES ((SELECT ID FROM companies WHERE (email='{public_email}')), '{name}', '{price}', '#aproximate_cost', '{hours * 60 + minutes}', '{description}');""")
        db.close()

        return jsonify({'message': 'Usługa została dodana!'}), 200
    except Exception as err:
        return jsonify({'error': str(err)}), 500
    
@app.route('/api/strona_rejestracji_firmy/zdjecia', methods=['POST'])
def add_photos():
    try:
        files = request.files
        photo = files.get('file')
        db = get_db_connection()
        cursor = db.cursor()
        cursor.execute(f"INSERT INTO photos (company_ID, picture) VALUES ((SELECT ID FROM companies WHERE (email='{public_email}'), {photo});")
        
        db.close()
        return jsonify({'message': 'Zdjęcie zostało dodane!'}), 200
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
        cursor.execute("SELECT Name, Description, Logo, tel_nr, Site_link, Facebook_link, Linkedin_link, Instagram_link, X_link, Tiktok_link FROM companies WHERE ID = %s", (company_id,))
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
        result = ({
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

        cursor.execute(f"""SELECT monday_start, monday_end, tuesday_start, tuesday_end, wensday_start, wensday_end, thursday_start, thursday_end, friday_start, friday_end, saturday_start, saturday_end, sunday_start, sunday_end FROM bookit_main.opening_hours WHERE ID = {company_id}""")
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

        return jsonify(result), 200
    except Exception as err:
        print(err)
        traceback.print_exc()
        return jsonify({'error': str(err)}), 500


@app.route('/api/Strona_zarządzania_firmą/update', methods=['PUT'])
def update_company_details():
    try:
        data = request.json
        company_id = data.get('company_id')
        field = data.get('field')
        value = data.get('value')

        db = get_db_connection()
        cursor = db.cursor()

        # Dynamically create the SQL query
        sql_query = f"UPDATE companies SET {field} = %s WHERE ID = %s"
        cursor.execute(sql_query, (value, company_id))

        db.commit()
        db.close()

        return jsonify({'message': 'Company details updated successfully'}), 200
    except Exception as err:
        return jsonify({'error': str(err)}), 500


@app.route('/api/Strona_zarządzania_firmą/reservations', methods=['POST'])
def get_reservations():
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
            WHERE 
                b.company_ID = %s AND DATE(b.booking_time) = %s
            """,
            (company_id, date)
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
                'service_name': res['service_name'],
                'category': res['category'],
                'execution_time': execution_time_minutes,
                'opis': res['additional_info'],
                'email': res['email'],
                'sms': res['tel_nr']
            })

        return jsonify(result), 200
    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': 'Internal server error'}), 500



@app.route('/api/update_company_hours', methods=['POST'])
def update_company_hours():
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
            WHERE company_id = %s
        """
        values = (
            hours['monday_start'], hours['monday_end'],
            hours['tuesday_start'], hours['tuesday_end'],
            hours['wensday_start'], hours['wensday_end'],
            hours['thursday_start'], hours['thursday_end'],
            hours['friday_start'], hours['friday_end'],
            hours['saturday_start'], hours['saturday_end'],
            hours['sunday_start'], hours['sunday_end'],
            company_id
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


if __name__ == '__main__':
    app.run(debug=True)

