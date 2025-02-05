# -*- coding: utf-8 -*-

import whisper
from PIL import Image
import requests
from io import BytesIO
import socket
import google.generativeai as genai

import paramiko
from scp import SCPClient

# Dettagli di connessione
#host = "143.225.85.145"
host = "143.225.85.168"
username = "nao"
password = "nao"
remote_file_path = "/home/nao/.local/share/naoqi/vision/prova.jpg"  # Percorso file sul robot
local_file_path = "C:/Users/mattr/Desktop/Progetto/Immagine/prova.jpg"  # Percorso di salvataggio locale

remote_audio_path = "/home/nao/audioprova.wav"
local_audio_path = "C:/Users/mattr/Desktop/Progetto/audioprova.wav"



# Configurazione dell'API
api_key = "AIzaSyAwTpk1XRpoTQwYplq5mbjGRibXdF4IFFg"  # Inserisci la tua API key
genai.configure(api_key=api_key)

# Modello Gemini per Vision
model = genai.GenerativeModel(model_name="gemini-1.5-flash")

def download_audio_from_pepper():
    """ Scarica il file audio dal robot al server."""
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        ssh.connect(host, username=username, password=password)
        with SCPClient(ssh.get_transport()) as scp:
            scp.get(remote_audio_path, local_audio_path)
            print("File audio scaricato correttamente su PC.")
            return True
    except Exception as e:
        print("Errore nel trasferimento dell'audio:", str(e))
        return False
    finally:
        ssh.close()

# Funzione per trasferire il file dal robot al computer locale
def download_image_from_pepper():
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())  # Accetta automaticamente chiavi non conosciute

    try:
        # Connessione al robot
        ssh.connect(host, username=username, password=password)
        print("Connesso al robot Pepper tramite SSH.")

        # Creazione di un client SCP per il trasferimento file
        with SCPClient(ssh.get_transport()) as scp:
            scp.get(remote_file_path, local_file_path)
            print("File scaricato correttamente in '{local_file_path}'.")
            return True
    except Exception as e:
        print(f"Errore durante il trasferimento del file: {e}")
        return False
    finally:
        # Chiusura della connessione SSH
        ssh.close()
        print("Connessione SSH chiusa.")

# Funzione per elaborare la domanda
def process_question(question):
    # Percorso immagine locale
    try:
        img = Image.open("C:/Users/mattr/Desktop/Progetto/Immagine/prova.jpg")
    except Exception as e:
        return f"Errore durante il caricamento dell'immagine: {e}"

    # Genera la risposta con il modello
    try:
        response = model.generate_content([question, img])
        response.resolve()
        return response.text
    except Exception as e:
        return f"Errore durante l'elaborazione della domanda: {e}"
    
def process_question_only(question):

    # Genera la risposta con il modello
    try:
        response = model.generate_content([question])
        response.resolve()
        return response.text
    except Exception as e:
        return f"Errore durante l'elaborazione della domanda: {e}"

# Configura il server socket
def start_server(host='143.225.85.137', port=8080): #IPv4 del mio pc
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((host, port))
    server_socket.listen(1)
    print(f"Server in ascolto su {host}:{port}")

    model = whisper.load_model("turbo")

    while True:
        client_socket, client_address = server_socket.accept()
        print(f"Connessione da: {client_address}")

        # Ricezione dati dal client (solo domanda)
        #question = client_socket.recv(4096).decode('utf-8')  # Riceve la domanda come stringa

        message = client_socket.recv(1024).decode('utf-8')

        if message == "audio_ready":
            print("Ricevuta notifica per il download dell'audio.")
            if download_audio_from_pepper():
                print("Audio pronto per l'elaborazione.")

                
                result = model.transcribe("audioprova.wav")
                print(result["text"])
                question = result["text"]

                print(f"Domanda ricevuta: {question}")

                # Scarica l'immagine dal robot
                if download_image_from_pepper():
                    # Processa la domanda e genera la risposta
                    try:
                        # modifica question
                        question="Analizza l'immagine che ti allego e rispondi alla domanda solamente in base alle informazioni di contesto: "+question+"rispondi senza fare riferimento al fatto che stai analizzando un'immagine. Utilizza alpiù 3 informazioni di contesto indicando eventualmente quali oggetti utilizzare."
                        
                        answer = process_question(question)

                        # question = "Rispondi alla domanda utilizzando alpiù 30 parole."+question
                        # answer = process_question_only(question)
                        print(f"Risposta generata: {answer}")
                    except Exception as e:
                        answer = f"Errore durante l'elaborazione: {e}"
                        print(answer)

                    # Invio della risposta al client
                    client_socket.send(answer.encode('utf-8'))

            else:
                print("Errore nel download del file audio.")

        # if question:
        #     print(f"Domanda ricevuta: {question}")

        #     # Scarica l'immagine dal robot
        #     if download_image_from_pepper():

        #         # Processa la domanda e genera la risposta
        #         try:
        #             # modifica question
        #             question = "Guarda questa immagine e rispondi alla seguente domanda: '"+question+"'. Sei un assistente su un robot umanoide chiamato Pepper, quindi rispondi in modo naturale e conciso, come se stessi parlando con un umano."
        #             answer = process_question(question)
        #             print(f"Risposta generata: {answer}")
        #         except Exception as e:
        #             answer = f"Errore durante l'elaborazione: {e}"
        #             print(answer)

        #         # Invio della risposta al client
        #         client_socket.send(answer.encode('utf-8'))

        client_socket.close()

if __name__ == "__main__":
    start_server()