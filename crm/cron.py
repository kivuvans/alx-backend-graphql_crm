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


from datetime import datetime
import requests


def update_low_stock():
    timestamp = datetime.now().strftime("%d/%m/%Y-%H:%M:%S")

    mutation = """
    mutation {
      updateLowStockProducts {
        products {
          name
          stock
        }
        message
      }
    }
    """

    try:
        response = requests.post(
            "http://localhost:8000/graphql",
            json={"query": mutation},
            timeout=10
        )
        response.raise_for_status()
        data = response.json()

        products = data["data"]["updateLowStockProducts"]["products"]

        with open("/tmp/low_stock_updates_log.txt", "a") as log_file:
            for product in products:
                log_file.write(
                    f"{timestamp} Updated {product['name']} to stock {product['stock']}\n"
                )

    except Exception as e:
        with open("/tmp/low_stock_updates_log.txt", "a") as log_file:
            log_file.write(f"{timestamp} Error updating stock\n")
