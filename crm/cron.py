from datetime import datetime
import requests


def log_crm_heartbeat():
    timestamp = datetime.now().strftime("%d/%m/%Y-%H:%M:%S")
    message = f"{timestamp} CRM is alive\n"

    # Log heartbeat
    with open("/tmp/crm_heartbeat_log.txt", "a") as log_file:
        log_file.write(message)

    # Optional: verify GraphQL endpoint
    try:
        response = requests.post(
            "http://localhost:8000/graphql",
            json={"query": "{ hello }"},
            timeout=5
        )
        response.raise_for_status()
    except Exception:
        pass
