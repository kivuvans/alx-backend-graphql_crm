#!/bin/bash

# Timestamp
NOW=$(date "+%Y-%m-%d %H:%M:%S")

# Run Django shell command to delete inactive customers
DELETED_COUNT=$(
python manage.py shell <<EOF
from crm.models import Customer
from django.utils import timezone
from datetime import timedelta

one_year_ago = timezone.now() - timedelta(days=365)

qs = Customer.objects.filter(order__isnull=True)
count = qs.count()
qs.delete()

print(count)
EOF
)

# Log result
echo "$NOW - Deleted customers: $DELETED_COUNT" >> /tmp/customer_cleanup_log.txt