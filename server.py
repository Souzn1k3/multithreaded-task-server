import socket
import sys
import threading

DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 5555

WELCOME = (
    "Добро пожаловать на сервер задач!\n"
    "Введите /help, чтобы увидеть список команд:"
)

HELP_TEXT = (
    "Доступные команды:\n"
    "/add <text> - добавить новую задачу\n"
    "/list - показать все задачи\n"
    "/done <number> - отметить задачу как выполненную\n"
    "/delete <number> - удалить задачу\n"
    "/help - показать справку по командам\n"
    "/quit - завершить работу клиента"
)

QUIT_MESSAGE = "Работа клиента завершена. До свидания!"


tasks = []
tasks_lock = threading.Lock()


def send_message(conn, text): #отправляет сообщение клиенту
    conn.sendall((text + "\n\n").encode("utf-8"))


def add_task(arg):
    text = arg.strip()
    if not text:
        return "Ошибка: команда /add без текста задачи. Пример: /add Купить кофе"
    with tasks_lock:
        tasks.append({"text": text, "done": False})
        number = len(tasks)
    return f"Задача №{number} добавлена: [ ] {text}"


def list_tasks():
    with tasks_lock:
        if not tasks:
            return "Список задач пуст"
        lines = []
        for number, task in enumerate(tasks, start=1):
            mark = "x" if task["done"] else " "
            lines.append(f"{number}. [{mark}] {task['text']}")
    return "\n".join(lines)


def parse_task_number(command, arg):
    if not arg:
        return None, f"Ошибка: после {command} должен идти номер задачи. Пример: {command} 2"
    try:
        number = int(arg)
    except ValueError:
        return None, (
            f"Ошибка: \"{arg}\" не является номером задачи. "
            f"Номер должен быть целым числом. Пример: {command} 2"
        )
    return number, None


def done_task(arg):
    number, error = parse_task_number("/done", arg)
    if error:
        return error
    with tasks_lock:
        if number < 1 or number > len(tasks):
            return f"Ошибка: задачи с номером {number} не существует. Всего задач: {len(tasks)}"
        task = tasks[number - 1]
        task["done"] = True
        text = task["text"]
    return f"Задача №{number} отмечена как выполненная: [x] {text}"


def delete_task(arg):
    number, error = parse_task_number("/delete", arg)
    if error:
        return error
    with tasks_lock:
        if number < 1 or number > len(tasks):
            return f"Ошибка: задачи с номером {number} не существует. Всего задач: {len(tasks)}"
        text = tasks.pop(number - 1)["text"]
    return f"Задача №{number} удалена: {text}"


def process_request(request): #разбирает команду клиента и возвращает ответ сервера
    parts = request.split(maxsplit=1)
    command = parts[0]
    arg = parts[1].strip() if len(parts) > 1 else ""

    if command == "/add":
        return add_task(arg)
    if command == "/list":
        if arg:
            return "Ошибка: команда /list не принимает аргументов"
        return list_tasks()
    if command == "/done":
        return done_task(arg)
    if command == "/delete":
        return delete_task(arg)
    if command == "/help":
        if arg:
            return "Ошибка: команда /help не принимает аргументов"
        return HELP_TEXT
    if command == "/quit":
        if arg:
            return "Ошибка: команда /quit не принимает аргументов"
        return QUIT_MESSAGE
    return f"Ошибка: неизвестная команда \"{command}\". Введите /help для списка команд"


def handle_client(conn, addr): #Обслуживание клиента в потоке
    print(f"[+] Подключился клиент: {addr}", flush=True)
    try:
        send_message(conn, WELCOME)
        reader = conn.makefile("r", encoding="utf-8")
        for raw_line in reader:
            request = raw_line.strip()
            if not request:
                continue
            try:
                response = process_request(request)
            except Exception:
                response = "Внутренняя ошибка сервера"
            send_message(conn, response)
            if request == "/quit":
                break
    except (ConnectionError, OSError, UnicodeDecodeError):
        pass  #клиент оборвал соединение
    finally:
        conn.close()
        print(f"[-] Отключился клиент: {addr}", flush=True)


def run_server(host, port):
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    if sys.platform != "win32":
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    try:
        server_socket.bind((host, port))
    except OSError as exc:
        print(f"Не удалось занять адрес {host}:{port}: {exc}")
        print("Возможно, сервер уже запущен. Укажите другой порт: python server.py 127.0.0.1 <порт>")
        sys.exit(1)
    server_socket.listen()
    print(f"Сервер задач запущен на {host}:{port}. Ожидаю подключения клиентов...")
    try:
        while True:
            conn, addr = server_socket.accept()
            client_thread = threading.Thread(target=handle_client, args=(conn, addr), daemon=True)
            client_thread.start()
    except KeyboardInterrupt:
        print("\nОстановка сервера (Ctrl+C).")
    finally:
        server_socket.close()


def main():
    host = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_HOST
    port = DEFAULT_PORT
    if len(sys.argv) > 2:
        try:
            port = int(sys.argv[2])
        except ValueError:
            print(f"Ошибка: порт \"{sys.argv[2]}\" должен быть целым числом")
            sys.exit(1)
    run_server(host, port)


if __name__ == "__main__":
    main()
