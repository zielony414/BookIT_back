from decouple import config
from datetime import datetime

import pymysql

def get_db_connection():
    return pymysql.connect(
        charset = "utf8mb4",
        connect_timeout = 500,
        cursorclass=pymysql.cursors.DictCursor,
        db = config('DB_DATABASE'),
        host = config('DB_HOST'),
        password = config('DB_PASS'),
        read_timeout = 500,
        port = config('DB_PORT'),
        user = config('DB_USER'),
        write_timeout = 500,
    )

# Dodaje dzień wolny do kalendarza
def add_free_day(company_ID, date):
    try:
        db = get_db_connection()
        cursor = db.cursor()
        cursor.execute(f"INSERT INTO free_days (company_ID, date) VALUES ('{company_ID}', '{date}');")
        result = cursor.fetchall()
        db.close()

    except Exception as err:
        # gdy pojawi się jakiś błąd zwraca 0
        return 0


#Sprawdza czy dany dzień jest dniem wolnym, zwraca 1 jeśli tak, 0 jeśli nie
def is_free_day(company_ID, date):
    try:
        db = get_db_connection()
        cursor = db.cursor()
        cursor.execute(f"SELECT count(company_ID) as res FROM free_days WHERE company_ID = {company_ID} AND data = '{date}';")
        result = cursor.fetchall()

        today = datetime.today()
        today = today.strftime('%Y-%m-%d')
        day_of_week = today.weekday()

        cursor.execute(f"SELECT * FROM opening_hours WHERE company_ID = {company_ID};")
        result2 = cursor.fetchall()
        db.close()

        temp1 = 0
        temp2 = 0

        if day_of_week == 0:
            temp1 = result2['monday_start']
            temp2 = result2['monday_end']
        elif day_of_week == 1:
            temp1 = result2['tuesday_start']
            temp2 = result2['tuesday_end']
        elif day_of_week == 2:
            temp1 = result2['wednesday_start']
            temp2 = result2['wednesday_end']
        elif day_of_week == 3:
            temp1 = result2['thursday_start']
            temp2 = result2['thursday_end']
        elif day_of_week == 4:
            temp1 = result2['friday_start']
            temp2 = result2['friday_end']
        elif day_of_week == 5:
            temp1 = result2['saturday_start']
            temp2 = result2['saturday_end']
        elif day_of_week == 6:
            temp1 = result2['sunday_start']
            temp2 = result2['sunday_end']


        if result['res'] > 0 or (temp1 == temp2):
            return 0
        else:
            return 1
    
    except Exception as err:
        # gdy pojawi się jakiś błąd zwraca 0
        return 0