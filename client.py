import socket
import threading
import time
import os
import numpy as np
import sounddevice as sd

class VoiceClient:
    def __init__(self, host, port, nickname, room_name="", password=""):
        self.host = host
        self.port = port
        self.nickname = nickname
        self.room_name = room_name
        self.password = password
        self.socket = None
        # Boolean
        self.authenticated = False
        self.audio_streams = []
        print(host)


    def start_client(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.bind((self.host, self.port))
        self.send_message(f"{self.nickname}*{self.room_name}*{self.password}")

        threading.Thread(target=self.listen_voice, daemon=True).start()
        threading.Thread(target=self.send_voice, daemon=True).start()

    def listen_voice(self):
        while True:
            try:
                message, server_address = self.socket.recvfrom(1024 * 10)
                try:
                    message = message.decode('utf-8')
                    decoded_message = True
                except UnicodeDecodeError:
                    decoded_message = False

                if message and decoded_message:
                    if message == "Invalid password":
                        print("Неверный пароль")
                        self.handle_invalid_password()

                elif not decoded_message:
                    # Добавляем аудиоданные в список активных потоков
                    audio_streams.append(message)

                    # Запускаем поток для воспроизведения
                    threading.Thread(target=self.play_audio_mixed_stream).start()

                else:
                    break
            except Exception as e:
                print(f"Error receiving message: {e}")
                break

    def play_audio_mixed_stream(self):
        while self.audio_streams:
            # Считаем среднее значение для всех аудиопотоков
            mixed_audio = sum(np.frombuffer(data, dtype=np.int16) for data in self.audio_streams) / len(self.audio_streams)

            # Ограничиваем диапазон значений, чтобы не было искажений
            mixed_audio = np.clip(mixed_audio, -32768, 32767).astype(np.int16)

            # Воспроизводим смешанный звук
            sd.play(mixed_audio, samplerate=44100)

            # Очищаем список активных потоков
            audio_streams.clear()


    def send_voice(self):
        print("213")
        #Принимаем звук, обрабатываем и отправляем

    def send_message(self, message):
        if self.socket:
            self.socket.sendto(message.encode('utf-8'), (self.host, self.port))

    def disconnect(self):
        # закрываем сокет
        if self.socket:
            try:
                self.socket.close()
            except:
                pass
            self.socket = None

    def handle_invalid_password(self):
        print("Invalid password")
        self.socket.close()
