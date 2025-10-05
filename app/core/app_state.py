"""Estado global da aplicação."""

import time

# Timestamp global para cálculo de uptime
START_TIME = time.time()


def get_uptime() -> float:
    """Obter tempo de atividade da aplicação em segundos."""
    return time.time() - START_TIME


def get_uptime_formatted() -> str:
    """Obter tempo de atividade formatado."""
    uptime = get_uptime()
    hours, remainder = divmod(int(uptime), 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
