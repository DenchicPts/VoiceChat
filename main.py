import time

import client
import server
import threading

print("Запуск сервера")
server_instance = server.VoiceServer('26.75.227.218', 32313, "Zalupa", "123")

# Запускаем сервер в отдельном потоке
server_thread = threading.Thread(target=server_instance.start, daemon=True)
server_thread.start()
print("Сервер запустился")

# Запускаем клиента
print("Запуск клиента")
time.sleep(1)
client_instance = client.VoiceClient('26.75.227.218', 32313, "Denc", "Zalupa", "123")
client_instance.start_client()
client_instance.send_message("TETETET")
print("Клиент запустился")

time.sleep(1)
client_instance.send_message("ABOBA Ne robit")

time.sleep(5)
print("LKE")
client_instance.send_message("KEK")
while True:
    pass