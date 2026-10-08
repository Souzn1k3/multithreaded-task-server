import socket
import sys

DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 5555


def read_message(reader): #Читает ответ сервера

    lines = []
    while True:
        line = reader.readline()
        if not line:
            return None
        line = line.rstrip("\n")
        if not line:
            break
        lines.append(line)
    return "\n".join(lines)


def parse_args(argv):
    host = argv[1] if len(argv) > 1 else DEFAULT_HOST
    port = DEFAULT_PORT
    if len(argv) > 2:
        try:
            port = int(argv[2])
        except ValueError:
            print(f"Ошибка: порт \"{argv[2]}\" должен быть целым числом")
            sys.exit(1)
    return host, port


def main():
    host, port = parse_args(sys.argv)
    try:
        client_socket = socket.create_connection((host, port))
    except OSError:
        print(f"Не удалось подключиться к серверу {host}:{port}")
        print("Убедитесь, что сервер запущен: python server.py")
        sys.exit(1)

    try:
        with client_socket:
            run_session(client_socket)
    except KeyboardInterrupt:
        print()
    print("Клиент остановлен")


def run_session(client_socket):
    reader = client_socket.makefile("r", encoding="utf-8")
    welcome = read_message(reader)
    if welcome is None:
        print("Сервер закрыл соединение сразу после подключения.")
        sys.exit(1)
    print(welcome)

    while True:
        try:
            request = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            request = "/quit"
            print()
        if not request:
            continue
        try:
            client_socket.sendall((request + "\n").encode("utf-8"))
        except OSError:
            print("Не удалось отправить команду: соединение прервано")
            break
        response = read_message(reader)
        if response is None:
            print("Соединение с сервером потеряно")
            break
        print(response)
        if request == "/quit":
            break


if __name__ == "__main__":
    main()
