# -*- coding: utf-8 -*-
import sys
sys.path.append('C:\pynaoqi-python2.7-2.5.5.5-win32-vs2013\pynaoqi-python2.7-2.5.5.5-win32-vs2013\lib')

import threading
import socket
import os
import time
from naoqi import ALProxy

# Configurazione NAOqi
robot_ip = "143.225.85.168"
robot_port = 9559

# Percorsi file
AUDIO_FILE_PATH = "/home/nao/audioprova.wav"

# Funzione per registrare l'audio su Pepper
def record_audio():
    try:
        audio_recorder = ALProxy("ALAudioRecorder", robot_ip, robot_port)
        audio_recorder.stopMicrophonesRecording()
        samplerate = 16000
        channels = [0, 0, 1, 0]  # Solo il microfono frontale
        
        print("Inizio registrazione audio...")
        audio_recorder.startMicrophonesRecording(AUDIO_FILE_PATH, "wav", samplerate, channels)
        time.sleep(7)  # Registra per 5 secondi
        audio_recorder.stopMicrophonesRecording()
        print("Registrazione terminata.")
        
        return True
    except Exception as e:
        print("Errore nella registrazione audio:", str(e))
        return False

# Funzione per inviare un segnale al server per scaricare l'audio
def notify_server(host='143.225.85.137', port=8080):
    try:
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect((host, port))
        client_socket.send(b"audio_ready")
        client_socket.close()
        print("Notificato il server per il download dell'audio.")
    except Exception as e:
        print("Errore nella notifica al server:", str(e))

# Funzione per scattare una foto con Pepper
def take_picture():
    try:
        photo_capture_proxy = ALProxy("ALPhotoCapture", robot_ip, robot_port)
        photo_capture_proxy.setResolution(2)  # Risoluzione VGA (640x480)
        photo_capture_proxy.setPictureFormat("jpg")  # Formato immagine
        photo_capture_proxy.takePictures(1, "/home/nao/.local/share/naoqi/vision", "prova")
        print("Foto scattata e salvata sul robot.")
        return True
    except Exception as e:
        print("Errore durante la cattura della foto:", str(e))
        return False

# Funzione per inviare la domanda al server
def send_question_to_server(host='143.225.85.137', port=8080): #ipv4 del pc (ipconfig da terminale)
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        # Connessione al server
        client_socket.connect((host, port))

        # # Invio della domanda
        # client_socket.send(question.encode('utf-8'))
        # print("Domanda inviata al server:", question)


        client_socket.send(b"audio_ready")

        # Ricezione della risposta
        answer = client_socket.recv(4096).decode('utf-8').strip()  # Decodifica correttamente in UTF-8
        print("Risposta ricevuta dal server:", answer)
        return answer
    except Exception as e:
        print("Errore nella comunicazione con il server:", str(e))
        return None
    finally:
        # Chiusura della connessione
        client_socket.close()

# Funzione per far parlare Pepper con Animated Speech (gestione UTF-8)
def speak_text(text):
    try:
        # Assicura che il testo sia in formato Unicode
        if not isinstance(text, unicode):  
            text = unicode(text, "utf-8")

        text = text.strip()

        # Se la risposta è vuota, usa un messaggio di fallback
        if not text:
            text = u"Non ho ricevuto una risposta valida."

        # Formattazione per Animated Speech
        animated_text = u"\\rspd=85\\ " + text # Regola la velocità e inserisce una pausa

        # Imposta la lingua con ALTextToSpeech
        tts = ALProxy("ALTextToSpeech", robot_ip, robot_port)
        tts.setLanguage("Italian")  # Imposta la lingua in italiano

        # Usa ALAnimatedSpeech per l'output
        animated_speech = ALProxy("ALAnimatedSpeech", robot_ip, robot_port)
        animated_speech.say(animated_text.encode("utf-8"))  # Codifica in UTF-8 per evitare errori
    except Exception as e:
        print("Errore nel Text-To-Speech:", str(e))

# Punto di ingresso principale
if __name__ == "__main__":

    # Scatta una foto con Pepper
    if take_picture():
        if record_audio():

            # Invia la domanda e ricevi la risposta
            # response = notify_server()
            response = send_question_to_server()
            print("debug", repr(response))

            if response:
                print("Risposta per Pepper:", response)

                # Far parlare Pepper con la risposta ricevuta
                speak_text(response)
            else:
                print("Non e stato possibile ottenere una risposta dal server.")
    else:
        print("Errore nella registrazione audio.")

    



