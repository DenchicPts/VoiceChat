import socket
import threading
import os
import time
import asyncio
from logging import fatal

import select

BUFFER_SIZE = 1024

class VoiceServer:
    def __init__(self, host, port, room_name, password):
        self.host = host
        self.port = port
        self.room_name = room_name
        self.clients = {}
        self.addresses = {}
        self.room_password = password
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.stop_event = threading.Event()


    def start(self):
        self.server_socket.setblocking(False)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((self.host, self.port))
        print(f"###Server listening on {self.host}:{self.port}")
        # Запуск асинхронной функции accept_connections
        asyncio.run(self.accept_connections())


    def stop(self):
        self.stop_event.set()
        self.server_socket.close()
        print("Server is shutdown")
        for client_socket in list(self.clients.keys()):
            self.remove_client(client_socket)

    async def accept_connections(self):
        # Сначала ставим сервер в блокирующий режим для аутентификации первого клиента
        self.server_socket.setblocking(True)

        while not self.stop_event.is_set():
            try:
                # Ожидаем получения данных от клиента
                #print('Ожидание сообщения от клиента...')
                message, client_address = self.server_socket.recvfrom(BUFFER_SIZE)
                print(f"SERVER Принято сообщение от {client_address}")
                self.server_socket.setblocking(False)

                # Обрабатываем полученное сообщение (можно запустить новый поток)
                threading.Thread(target=self.handle_client, args=(message, client_address), daemon=True).start()

            except BlockingIOError:
                # Ошибка, когда данных нет — просто пропускаем, это нормально для неблокирующего режима
                time.sleep(0.5)  # Добавляем небольшую задержку перед следующей проверкой

            except Exception as e:
                print(f"SERVER Ошибка при обработке клиента: {e}")
                time.sleep(0.1)  # Увеличенная задержка на случай непредвиденной ошибки

    def handle_client(self, message, client_address):
        try:
            # Декодируем сообщение от клиента
            welcome_message = message.decode('utf-8')
            print("Получено сообщение:", welcome_message)

            if welcome_message:
                parts = welcome_message.split('*')
                if len(parts) < 2:
                    print(f"SERVER Неверное приветственное сообщение от {client_address}")
                    return

                nickname = parts[0]
                client_room_name = parts[1]
                password = parts[2] if len(parts) > 2 else ""

                # Проверяем пароль
                if self.room_password != password:
                    print(f"SERVER Неверный пароль от {client_address}")
                    self.server_socket.sendto("Invalid password".encode('utf-8'), client_address)
                    return

                # Проверяем, не хост ли это (по IP)
                if client_address[0] in {self.host, "127.0.0.1"}:
                    self.room_name = client_room_name

                print(f"SERVER Имя комнаты: {self.room_name}, Пароль: {password}")
                # Добавляем клиента в список (для UDP, можно хранить их адреса)
                self.clients[client_address] = nickname

            # Основной цикл обработки сообщений
            while not self.stop_event.is_set():
                try:
                    # Проверяем доступность данных на сокете с помощью select
                    ready = select.select([self.server_socket], [], [], 0.5)  # 0.5 секунды ожидания

                    if ready[0]:  # Если данные доступны
                        print(f"Столько потоков задействовано: {threading.active_count()}")
                        message, address = self.server_socket.recvfrom(BUFFER_SIZE)

                        # Проверяем, что сообщение пришло от того же клиента
                        if address == client_address:
                            try:
                                message = message.decode('utf-8')
                                decoded_message = True
                            except UnicodeDecodeError:
                                decoded_message = False

                            if message and decoded_message:
                                print(f"SERVER Получено сообщение от {client_address}: {message}")
                            elif message and not decoded_message:
                                #перекидывание звука другим клиентам


                                del message
                            else:
                                print(f"###Клиент {client_address} отключился")
                                break
                        else:
                            print("Сообщение от неизвестного клиента")
                    else:
                        # Если данных нет, просто переходим к следующей итерации
                        time.sleep(0.01)

                except BlockingIOError:
                    # Неблокирующий режим; если нет данных, продолжаем без ошибки
                    continue

                except Exception as e:
                    print(f"{message}\n")
                    print(f"Ошибка при получении сообщения: {e}")
                    break

        finally:
            print(f"###Клиент {client_address} отключился")
            if client_address in self.clients:
                del self.clients[client_address]

    def remove_client(self, client_socket):
        client_socket.close()
        if client_socket in self.clients:
            del self.clients[client_socket]
        if client_socket in self.addresses:
            del self.addresses[client_socket]

    def broadcast(self, message, source_socket=None):
        for client_socket in list(self.clients.keys()):
            if client_socket != source_socket:
                try:
                    client_socket.send(message.encode('utf-8'))
                except Exception as e:
                    print(f"###Error sending message: {e}")
                    self.remove_client(client_socket)


