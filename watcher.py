import os
import queue
import subprocess
import sys
import threading
import time

from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

from analyzer import analyze_logs, format_report


LOG_FILE = "logs.txt"
WATCH_FOLDER = "."
HISTORY_LIMIT = 50


class LogFileHandler(FileSystemEventHandler):
    def __init__(self, log_file, analysis_queue):
        self.log_file = os.path.abspath(log_file)
        self.analysis_queue = analysis_queue
        self.last_position = 0
        self.recent_logs = []
        self.ensure_log_file_exists()
        self.load_recent_logs()
        self.move_to_end_of_file()

    def ensure_log_file_exists(self):
        if not os.path.exists(self.log_file):
            open(self.log_file, "w", encoding="utf-8").close()

    def move_to_end_of_file(self):
        with open(self.log_file, "r", encoding="utf-8") as file:
            file.seek(0, os.SEEK_END)
            self.last_position = file.tell()

    def load_recent_logs(self):
        with open(self.log_file, "r", encoding="utf-8") as file:
            lines = [line.strip() for line in file if line.strip()]

        self.recent_logs = lines[-HISTORY_LIMIT:]

    def queue_existing_logs(self):
        if self.recent_logs:
            print("Logs existentes enviados para a fila de analise.")
            self.analysis_queue.put(self.recent_logs.copy())

    def on_modified(self, event):
        if event.is_directory:
            return

        if os.path.abspath(event.src_path) != self.log_file:
            return

        new_logs = self.read_new_logs()

        if not new_logs:
            return

        self.recent_logs.extend(new_logs)
        self.recent_logs = self.recent_logs[-HISTORY_LIMIT:]
        self.analysis_queue.put(new_logs)

        for log in new_logs:
            print(f"Novo log recebido: {log}")

        print(
            f"Analise adicionada a fila. Pendentes: "
            f"{self.analysis_queue.qsize()}"
        )

    def read_new_logs(self):
        with open(self.log_file, "r", encoding="utf-8") as file:
            file.seek(self.last_position)
            new_lines = file.readlines()
            self.last_position = file.tell()

        return [line.strip() for line in new_lines if line.strip()]


def analysis_worker(analysis_queue, log_handler):
    while True:
        new_logs = analysis_queue.get()

        if new_logs is None:
            analysis_queue.task_done()
            break

        batches = [new_logs]
        stop_after_batch = False

        while True:
            try:
                pending = analysis_queue.get_nowait()
            except queue.Empty:
                break

            if pending is None:
                analysis_queue.task_done()
                stop_after_batch = True
                break

            batches.append(pending)
            analysis_queue.task_done()

        combined_logs = [
            log
            for batch in batches
            for log in batch
        ]

        print(f"\nAnalisando lote com {len(combined_logs)} evento(s)...")
        analysis = analyze_logs(combined_logs, log_handler.recent_logs.copy())

        if analysis:
            print("\nRelatorio:")
            print(format_report(analysis))
            print("\nRelatorio salvo em reports.jsonl")
            print("-" * 60)

        analysis_queue.task_done()

        if stop_after_batch:
            break


def start_generator():
    print("Iniciando generator.py...")
    return subprocess.Popen(
        [sys.executable, "generator.py"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def main():
    analysis_queue = queue.Queue()
    log_handler = LogFileHandler(LOG_FILE, analysis_queue)
    observer = Observer()
    generator_process = None
    worker = threading.Thread(
        target=analysis_worker,
        args=(analysis_queue, log_handler),
        daemon=True,
    )

    worker.start()
    observer.schedule(log_handler, WATCH_FOLDER, recursive=False)
    observer.start()

    print("Watcher iniciado. Pressione Ctrl+C para encerrar.")
    log_handler.queue_existing_logs()
    generator_process = start_generator()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nEncerrando watcher...")
    finally:
        observer.stop()
        observer.join()
        analysis_queue.put(None)
        worker.join(timeout=5)

        if generator_process is not None:
            generator_process.terminate()
            generator_process.wait()

        print("Generator e watcher encerrados.")


if __name__ == "__main__":
    main()
