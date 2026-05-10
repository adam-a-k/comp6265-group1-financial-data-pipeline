import os
from datetime import datetime

os.makedirs("logs", exist_ok=True)

def _write(logfile, message):
    timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    with open(f"logs/{logfile}", "a") as f:
        f.write(f"{timestamp} | INFO | {message}\n")

def log_etl_run(stage, source, user, input_rows, output_rows, nulls_dropped):
    _write("etl_audit.log", f"stage={stage} | source={source} | user={user} | usage=etl_transform | input_rows={input_rows} | output_rows={output_rows} | nulls_dropped={nulls_dropped}")