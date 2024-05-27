import smtplib
from decouple import config
from datetime import datetime
import os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

def send_mail(receiver_email, title, message):


    # Dane do logowania (adres e-mail i hasło)
    sender_email = config('EMAIL_USER')
    password = config('EMAIL_PASS')

    # Konfiguracja serwera SMTP
    smtp_server = config('EMAIL_SERVER')
    smtp_port = config('EMAIL_PORT')

    # Tworzenie wiadomości
    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = receiver_email
    msg['Subject'] = title

    # Treść wiadomości
    body = message
    body += "\n\n Wiadomość wysłana automatycznie. Prosimy na nią nie odpowiadać."
    msg.attach(MIMEText(body))

    # Logowanie do serwera SMTP i wysyłka e-maila
    try:
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()  # Zabezpieczenie połączenia
        server.login(sender_email, password)
        text = msg.as_string()
        server.sendmail(sender_email, receiver_email, text)
        print("E-mail został wysłany pomyślnie!")
    except Exception as e:
        print(f"Nie udało się wysłać e-maila. Błąd: {e}")
    finally:
        server.quit()

# Funkcja do zapisywania zaplanowanych e-maili do pliku scheduled_emails.txt
def add_scheduled_email(receiver_email, title, message, date):
    # Formatowanie danych do zapisania
    log_entry = f"{date}*;*{receiver_email}*;*{title}*;*{message}\n"
    
    # Sprawdzanie, czy plik istnieje
    if not os.path.exists("scheduled_emails.txt"):
        # Tworzenie pliku i zapisywanie nagłówka, jeśli plik nie istnieje
        with open("scheduled_emails.txt", 'w') as file:
            file.write(log_entry)
    
    else:
        # Dopisywanie danych do pliku
        with open("scheduled_emails.txt", 'a') as file:
            file.write(log_entry)



# Wysyłanie zaplanowanych e-maili z pliku scheduled_emails.txt
def send_scheduled_emails():
    try:
        with open("scheduled_emails.txt", 'r') as file:
            for line in file:
                # Usunięcie ewentualnych białych znaków z końca linii
                line = line.strip()
                # Podział linii na części na podstawie znaków "*;*"
                parts = line.split('*;*')
                if len(parts) == 4:
                    date, recipient, subject, body = parts
                    print(f"Data: {date}, Odbiorca: {recipient}, Temat: {subject}, Treść: {body}")

                    if date == datetime.today().strftime('%Y-%m-%d'):
                        send_mail(recipient, subject, body)

                else:
                    print("Błąd przy czytaniu danych do wysyłki", line)

    except FileNotFoundError:
        print(f"Plik {"scheduled_emails.txt"} nie został znaleziony.")
    except Exception as e:
        print(f"Wystąpił błąd: {e}")