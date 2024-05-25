import smtplib
from decouple import config
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