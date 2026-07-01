import random
import time
from datetime import datetime


LOG_FILE = "logs.txt"
INTERVAL_SECONDS = 3

EVENTS = [
    "LOGIN_SUCCESS user=admin",
    "LOGIN_SUCCESS user=backup",
    "LOGIN_FAILED user=root ip=192.168.0.25",
    "LOGIN_FAILED user=admin ip=10.0.0.8",
    "FILE_DELETED backup.zip",
    "FILE_DELETED system_config.json",
    "UPLOAD_SUCCESS backup enviado",
    "UPLOAD_FAILED backup.zip",
    "UNAUTHORIZED_ACCESS /secure-folder",
    "UNAUTHORIZED_ACCESS /admin-panel",
    "MULTIPLE_FAILED_LOGINS ip=45.66.12.9",
    "MULTIPLE_FAILED_LOGINS ip=201.45.88.10",
]


def generate_log():
    """Cria uma linha de log com data, hora e um evento aleatorio."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    event = random.choice(EVENTS)
    return f"[{timestamp}] {event}"


def save_log(log_line):
    """Salva uma linha de log no arquivo logs.txt."""
    with open(LOG_FILE, "a", encoding="utf-8") as file:
        file.write(log_line + "\n")


def main():
    print("Gerador de logs iniciado. Pressione Ctrl+C para encerrar.")

    try:
        while True:
            log_line = generate_log()
            save_log(log_line)
            print(f"Log gerado: {log_line}", flush=True)
            time.sleep(INTERVAL_SECONDS)
    except KeyboardInterrupt:
        print("\nGerador de logs encerrado.")


if __name__ == "__main__":
    main()
