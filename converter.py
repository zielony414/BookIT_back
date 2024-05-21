import mysql.connector

# Ustawienia połączenia
config = {
    'user': 'avnadmin',
    'password': 'AVNS_lK1EnykcZ5J6TflOpru',
    'host': 'bookit-bookit.f.aivencloud.com',
    'database': 'bookit_main',
    'port': '22474'
}

# Połączenie z bazą danych
connection = mysql.connector.connect(**config)
cursor = connection.cursor()

# Ścieżka do pliku
file_path = 'C:/Users/marci/Desktop/studia/sem IV/projekt wydzial gier i zabaw/zdjęcia/silka.png'

# Wczytanie pliku jako strumień bajtów
with open(file_path, 'rb') as file:
    binary_data = file.read()

# Zapytanie SQL do aktualizacji
update_query = "UPDATE companies SET Logo = %s WHERE ID = %s"
cursor.execute(update_query, (binary_data, 5))

# Zatwierdzenie zmian
connection.commit()

# Zamknięcie połączenia
cursor.close()
connection.close()
