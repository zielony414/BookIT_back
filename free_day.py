from decouple import config
from datetime import datetime, timedelta

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
        port = int(config('DB_PORT')),
        user = config('DB_USER'),
        write_timeout = 500,
    )

# Dodaje dzień wolny do kalendarza
def add_free_day(company_ID, date):
    try:
        db = get_db_connection()
        cursor = db.cursor()
        cursor.execute(f"INSERT INTO free_days (company_ID, date) VALUES ({company_ID}, '{date}');")
        result = cursor.fetchall()
        db.close()

    except Exception as err:
        # gdy pojawi się jakiś błąd zwraca -1
        return -1


#Sprawdza czy dany dzień jest dniem wolnym, zwraca 1 jeśli tak, 0 jeśli nie

def is_free_day(company_ID, date_str, start_time, end_time):
    try:        
        db = get_db_connection()
        cursor = db.cursor()
        
        booking_date = datetime.strptime(date_str, '%Y-%m-%d').date()
                                                
        cursor.execute(f"SELECT count(company_ID) as res FROM free_days WHERE company_ID = {company_ID} AND data = '{booking_date}';")
        result = cursor.fetchone()

        day_of_week = booking_date.weekday()

        cursor.execute(f"SELECT * FROM opening_hours WHERE company_ID = {company_ID};")
        result2 = cursor.fetchone()  

        temp1 = temp2 = None

        if day_of_week == 0:        
            temp1 = result2['monday_start']
            temp2 = result2['monday_end']

        elif day_of_week == 1:
            temp1 = result2['tuesday_start']
            temp2 = result2['tuesday_end']

        elif day_of_week == 2:
            temp1 = result2['wensday_start']
            temp2 = result2['wensday_end']

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

        temp1 = str(temp1)[:-3]
        temp2 = str(temp2)[:-3]

        temp1 = datetime.strptime(temp1, '%H:%M')
        temp2 = datetime.strptime(temp2, '%H:%M')

        #print("-------- Godziny rezerwacji ---------")
        #print("start: ", start_time, "end: ", end_time)   

        #print("----- Godziny otwarcia ------")
        #print("otwarcie: ", temp1, "  zamkniecie: ", temp2)

        if not ((temp1 <= start_time and start_time <= temp2) and (temp1 <= end_time and end_time <= temp2)):
            print("Rezerwacja niemozliwa - zmien godzinę rezerwacji")
            return 0        


        if result['res'] > 0 or (temp1 == temp2):
            return 0
        else:
            return 1
    
    except Exception as err:
        print("Błąd w is_free_day: ", err)
        return 0  # Zwraca 0 w przypadku błędu, aby błąd został potraktowany jako niedodanie do bazy danych
    finally:
        db.close()

    
# Sprawdza czy w danym terminie jest możliwość zarezerwowania wizyty, duration musi być w minutach

def is_booking_time_free(company_ID, date, time, duration):
    try:
        print("WYKONUJE BOOKING TIME FREE")
        db = get_db_connection()
        cursor = db.cursor()

        # Sprawdzenie, czy istnieje wpis dla podanej daty
        cursor.execute(f"SELECT * FROM bookit_main.day_schedule WHERE company_ID = {company_ID} AND Date = '{date}';")
        result = cursor.fetchone()
        print("time_free_result:", result)

        # Jeśli nie ma wyniku, to data jest wolna
        if result is None:
            db.close()
            return 1

        # Sprawdzenie, czy istnieje wpis dla podanej firmy
        cursor.execute(f"SELECT * FROM bookit_main.day_schedule WHERE company_ID = {company_ID};")
        company_exists = cursor.fetchone()

        if company_exists is None:
            db.close()
            return 1

        db.close()

        time_step = timedelta(minutes=30)
        repeat = 0

        # Obliczenie, ile razy trzeba przesunąć się o 30 minut
        while duration > 0:
            duration -= 30
            repeat += 1

        # Źle podany czas
        if repeat == 0:
            return -1

        # Przesuwanie się o 30 minut i sprawdzanie, czy w danym czasie serwis jest dostępny
        for i in range(repeat):
            if time in result and result[time] == 1: 
                return 0
            else:
                temp = datetime.strptime(time, "%H:%M")
                temp += time_step
                time = temp.strftime("%H:%M")

        return 1
        
    except Exception as err:
        print("Error w is_time_free:", err)
        return 0
