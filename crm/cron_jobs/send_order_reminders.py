#!/usr/bin/env python3

from gql import gql, Client
from gql.transport.requests import RequestsHTTPTransport
from datetime import datetime

# GraphQL endpoint
transport = RequestsHTTPTransport(
    url="http://localhost:8000/graphql",
    verify=True,
    retries=3,
)

client = Client(transport=transport, fetch_schema_from_transport=False)

# GraphQL query
query = gql("""
query {
  orders {
    id
    orderDate
    customer {
      email
    }
  }
}
""")

# Execute query
result = client.execute(query)

now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

# Log file
log_file = "/tmp/order_reminders_log.txt"

with open(log_file, "a") as f:
    for order in result.get("orders", []):
        f.write(
            f"{now} - Order ID: {order['id']}, Customer Email: {order['customer']['email']}\n"
        )

print("Order reminders processed!")
