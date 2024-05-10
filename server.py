from flask import Flask, request, jsonify
import pymysql

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

# Members API route
@app.route('/members')
def members():
    return {"members": ["member1", "member2", "member3"]}

@app.route('/api/nav_items')
def get_nav_items():
    return {"nav_items": ["Barber", "Salon kosmetyczny", "Paznokcie", "Masaż", "Zwierzęta", "Siłownia", "Więcej..."]}

def get_image_cards():
    return {"image_cards" : [
            {
                "imageSrc": "images/barber.jpg",
                "imageAlt": "Image 2",
                "description": "Lorem ipsum dolor sit amet, consectetur adipiscing elit. Ut pulvinar ipsum orci, eget ullamcorper lectus cursus nec."
            },
            {
                "imageSrc": "images/salon.jpg",
                "imageAlt": "Image 3",
                "description": "Lorem ipsum dolor sit amet, consectetur adipiscing elit. Ut pulvinar ipsum orci, eget ullamcorper lectus cursus nec."
            },
            {
                "imageSrc": "images/paznokcie.jpg",
                "imageAlt": "Image 4",
                "description": "Lorem ipsum dolor sit amet, consectetur adipiscing elit. Ut pulvinar ipsum orci, eget ullamcorper lectus cursus nec."
            },
            {
                "imageSrc": "https://cdn.builder.io/api/v1/image/assets/TEMP/b10e017e3fafc40f727425bb7f8f66387d777cb825bf4515f5163fb0909ca872?apiKey=d10d36f0508e433185a32e898689ca50&",
                "imageAlt": "Image 5",
                "description": "Lorem ipsum dolor sit amet, consectetur adipiscing elit. Ut pulvinar ipsum orci, eget ullamcorper lectus cursus nec."
            }
        ]
    }


# dekorator, wpisuje się to na froncie w funkcji fetch() i wtedy jest wywoływana ta funkcja poniżej
@app.route('/api/strona_logowania/user', methods=['POST']) # ogólnie metoda komuniakcji POST GET się nazywa REST-API podaje dla informacji
def logging_in():
    try:
        # pobranie danych z frontu poprzez JSON
        login = request.json.get('user_login') # pola podane przez front muszą nazywać się user_login i user_password
        password = request.json.get('user_password')

        # zwraca listę dobrych dopasowań
        answer = cursor.execute(f"SELECT * FROM users WHERE email = '{login}' AND password = '{password}';") 
        # jeśli 
        if len(answer) > 0:
            return jsonify({'message': 'Zalogowano pomyślnie!', 'username': login}), 200
        else:
            return jsonify({'message': 'Niepoprawne dane logowania!'}), 401
        
    except Exception as err:
        # gdy pojawi się jakiś błąd zwraca error
        return jsonify({'error': str(err)}), 500
    
@app.route('/api/strona_logowania/company', methods=['POST']) # ogólnie metoda komuniakcji POST GET się nazywa REST-API podaje dla informacji
def logging_in():
    try:
        # pobranie danych z frontu poprzez JSON
        login = request.json.get('company_login') # pola podane przez front muszą nazywać się company_login i company_password
        password = request.json.get('company_password')

        # zwraca listę dobrych dopasowań
        answer = cursor.execute(f"SELECT * FROM companies WHERE email = '{login}' AND password = '{password}';") 
        # jeśli 
        if len(answer) > 0:
            return jsonify({'message': 'Zalogowano pomyślnie!', 'username': login}), 200
        else:
            return jsonify({'message': 'Niepoprawne dane logowania!'}), 401
        
    except Exception as err:
        # gdy pojawi się jakiś błąd zwraca error
        return jsonify({'error': str(err)}), 500

if __name__ == '__main__':
    app.run(debug=True)