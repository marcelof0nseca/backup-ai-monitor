import json
import queue
import re
import threading
from collections import Counter
from datetime import datetime

import ollama


MODEL_NAME = "llama3.2:1b"
OLLAMA_TIMEOUT_SECONDS = 20
REPORT_FILE = "reports.jsonl"
BRUTE_FORCE_LIMIT = 3
BRUTE_FORCE_WINDOW_SECONDS = 60


def parse_log(log_line):
    timestamp_match = re.search(r"\[(.*?)\]", log_line)
    event_match = re.search(r"\]\s+([A-Z_]+)", log_line)

    data = {
        "raw": log_line,
        "timestamp": None,
        "event": event_match.group(1) if event_match else "UNKNOWN",
        "ip": None,
        "user": None,
        "target": None,
    }

    if timestamp_match:
        try:
            data["timestamp"] = datetime.strptime(
                timestamp_match.group(1),
                "%Y-%m-%d %H:%M:%S",
            )
        except ValueError:
            pass

    ip_match = re.search(r"ip=([0-9.]+)", log_line)
    user_match = re.search(r"user=([A-Za-z0-9_.-]+)", log_line)

    if ip_match:
        data["ip"] = ip_match.group(1)

    if user_match:
        data["user"] = user_match.group(1)

    if data["event"] in {
        "DATABASE_ERROR",
        "FILE_DELETED",
        "UNAUTHORIZED_ACCESS",
        "UPLOAD_FAILED",
    }:
        target_match = re.search(r"\]\s+[A-Z_]+\s+(\S+)", log_line)
        if target_match:
            data["target"] = target_match.group(1)

    return data


def find_brute_force_source(parsed_logs):
    failed_by_ip = {}

    for log in parsed_logs:
        if log["event"] != "LOGIN_FAILED" or not log["ip"] or not log["timestamp"]:
            continue

        failed_by_ip.setdefault(log["ip"], []).append(log["timestamp"])

    for ip, timestamps in failed_by_ip.items():
        timestamps.sort()

        for index, start_time in enumerate(timestamps):
            attempts = [
                timestamp
                for timestamp in timestamps[index:]
                if (timestamp - start_time).total_seconds()
                <= BRUTE_FORCE_WINDOW_SECONDS
            ]

            if len(attempts) >= BRUTE_FORCE_LIMIT:
                return ip

    return None


def classify_logs(new_log_lines, context_lines):
    parsed_new = [parse_log(line) for line in new_log_lines]
    parsed_context = [parse_log(line) for line in context_lines]
    events = {log["event"] for log in parsed_new}
    explicit_brute_force = next(
        (
            log["ip"]
            for log in parsed_new
            if log["event"] == "MULTIPLE_FAILED_LOGINS"
        ),
        None,
    )
    detected_brute_force = find_brute_force_source(parsed_context)

    if explicit_brute_force or detected_brute_force:
        source = explicit_brute_force or detected_brute_force
        return {
            "severity": "CRITICAL",
            "diagnosis": "Possivel tentativa de brute force",
            "explanation": (
                f"Foram detectadas varias falhas de login do IP {source} "
                f"em ate {BRUTE_FORCE_WINDOW_SECONDS} segundos."
            ),
            "solution": (
                "Bloquear temporariamente o IP, revisar as contas afetadas, "
                "limitar tentativas e ativar autenticacao em dois fatores."
            ),
        }

    if "UNAUTHORIZED_ACCESS" in events:
        return {
            "severity": "HIGH",
            "diagnosis": "Acesso nao autorizado",
            "explanation": "Houve tentativa de acesso a uma area protegida.",
            "solution": (
                "Revisar permissoes, identificar a origem, bloquear o acesso "
                "suspeito e auditar atividades recentes."
            ),
        }

    if "FILE_DELETED" in events:
        return {
            "severity": "HIGH",
            "diagnosis": "Exclusao suspeita de arquivo",
            "explanation": "Um arquivo foi removido e a operacao deve ser confirmada.",
            "solution": (
                "Identificar o responsavel, revisar permissoes e restaurar o "
                "arquivo a partir do backup, se necessario."
            ),
        }

    if "DATABASE_ERROR" in events:
        return {
            "severity": "HIGH",
            "diagnosis": "Falha critica de banco de dados",
            "explanation": (
                "Foi detectado erro de conexao ou disponibilidade relacionado "
                "ao banco de dados."
            ),
            "solution": (
                "Verificar conectividade, credenciais, status do banco, "
                "servicos dependentes e impactos em cascata."
            ),
        }

    if "LOGIN_FAILED" in events or "UPLOAD_FAILED" in events:
        return {
            "severity": "WARNING",
            "diagnosis": "Falha que exige acompanhamento",
            "explanation": "Foi registrada uma falha de login ou de upload.",
            "solution": (
                "Verificar credenciais, conectividade, espaco em disco e repetir "
                "a operacao apenas depois de identificar a causa."
            ),
        }

    return {
        "severity": "INFO",
        "diagnosis": "Comportamento normal",
        "explanation": "Os eventos novos nao indicam uma ameaca clara.",
        "solution": "Continuar monitorando os logs.",
    }


def collect_values(parsed_logs, field):
    return sorted({log[field] for log in parsed_logs if log[field]})


def build_local_analysis(new_log_lines, context_lines):
    parsed_logs = [parse_log(line) for line in new_log_lines]
    classification = classify_logs(new_log_lines, context_lines)
    timestamps = [log["timestamp"] for log in parsed_logs if log["timestamp"]]

    analysis = {
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "severity": classification["severity"],
        "diagnosis": classification["diagnosis"],
        "explanation": classification["explanation"],
        "solution": classification["solution"],
        "event_start": min(timestamps).isoformat(sep=" ") if timestamps else None,
        "event_end": max(timestamps).isoformat(sep=" ") if timestamps else None,
        "ips": collect_values(parsed_logs, "ip"),
        "users": collect_values(parsed_logs, "user"),
        "targets": collect_values(parsed_logs, "target"),
        "events": dict(Counter(log["event"] for log in parsed_logs)),
        "evidence": new_log_lines,
        "ai_model": MODEL_NAME,
        "ai_report": None,
    }

    return analysis


def should_use_enriched_context(analysis):
    return analysis["severity"] in {"HIGH", "CRITICAL"}


def get_enriched_context(analysis, context_lines):
    if not should_use_enriched_context(analysis):
        return None

    try:
        from enriched_context import build_enriched_context

        return build_enriched_context(analysis, context_lines)
    except Exception as error:
        return f"Contexto RAG/grafo indisponivel: {error}"


def build_prompt(analysis, context_lines, enriched_context=None):
    extra_context = ""

    if enriched_context:
        extra_context = f"""

Contexto interno recuperado:
{enriched_context}
"""

    return f"""
Voce e uma IA local que complementa um relatorio de seguranca.
Responda em portugues, em no maximo 12 linhas. Nao invente informacoes.

Diagnostico local: {analysis["diagnosis"]}
Severidade: {analysis["severity"]}
IPs: {analysis["ips"]}
Usuarios: {analysis["users"]}
Alvos: {analysis["targets"]}

Logs recentes:
{chr(10).join(context_lines)}
{extra_context}

Explique o risco, possiveis causas, impactos em cascata quando houver contexto, e acoes praticas.
"""


def call_ollama(prompt, result_queue):
    try:
        response = ollama.chat(
            model=MODEL_NAME,
            messages=[{"role": "user", "content": prompt}],
        )
        result_queue.put(response["message"]["content"].strip())
    except Exception as error:
        result_queue.put(f"Ollama indisponivel: {error}")


def add_ai_analysis(analysis, context_lines):
    result_queue = queue.Queue()
    enriched_context = get_enriched_context(analysis, context_lines)
    prompt = build_prompt(analysis, context_lines, enriched_context)
    thread = threading.Thread(
        target=call_ollama,
        args=(prompt, result_queue),
        daemon=True,
    )
    thread.start()

    try:
        analysis["ai_report"] = result_queue.get(
            timeout=OLLAMA_TIMEOUT_SECONDS
        )
    except queue.Empty:
        analysis["ai_report"] = (
            "O Ollama nao respondeu dentro do limite. "
            "O diagnostico local continua valido."
        )

    return analysis


def save_report(analysis):
    with open(REPORT_FILE, "a", encoding="utf-8") as file:
        file.write(json.dumps(analysis, ensure_ascii=False) + "\n")


def format_report(analysis):
    origins = (
        analysis["ips"] + analysis["users"] + analysis["targets"]
    )
    origin_text = ", ".join(origins) if origins else "nao informado"
    period = analysis["event_start"] or "nao informado"

    if analysis["event_end"] and analysis["event_end"] != analysis["event_start"]:
        period += f" ate {analysis['event_end']}"

    evidence = "\n".join(f"- {line}" for line in analysis["evidence"])

    return f"""[{analysis["severity"]}] {analysis["diagnosis"]}

Quando aconteceu:
{period}

Origem / alvo:
{origin_text}

Como aconteceu:
{analysis["explanation"]}

Evidencias:
{evidence}

Como resolver:
{analysis["solution"]}

Complemento da IA ({analysis["ai_model"]}):
{analysis["ai_report"]}"""


def analyze_logs(new_log_lines, context_lines=None):
    if not new_log_lines:
        return None

    context_lines = context_lines or new_log_lines
    analysis = build_local_analysis(new_log_lines, context_lines)
    analysis = add_ai_analysis(analysis, context_lines)
    save_report(analysis)
    return analysis


if __name__ == "__main__":
    sample_logs = [
        "[2026-06-25 10:00:00] LOGIN_FAILED user=root ip=192.168.0.25",
        "[2026-06-25 10:00:20] LOGIN_FAILED user=root ip=192.168.0.25",
        "[2026-06-25 10:00:40] LOGIN_FAILED user=root ip=192.168.0.25",
    ]

    print(format_report(analyze_logs(sample_logs)))
