#!/usr/bin/env python
"""
Database seeder for CRM system.
Run with: python seed_db.py
"""
import os
import sys
import django
from decimal import Decimal
import random
from datetime import datetime, timedelta

# Setup Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'alx_backend_graphql_crm.settings')
django.setup()

from crm.models import Customer, Product, Order

def clear_database():
    """Clear existing data."""
    print("Clearing existing data...")
    Order.objects.all().delete()
    Product.objects.all().delete()
    Customer.objects.all().delete()
    print("Database cleared.")

def create_customers():
    """Create sample customers."""
    print("Creating customers...")
    
    customers_data = [
        {"name": "Alice Johnson", "email": "alice@example.com", "phone": "+1234567890"},
        {"name": "Bob Smith", "email": "bob@example.com", "phone": "123-456-7890"},
        {"name": "Carol Davis", "email": "carol@example.com", "phone": "+447123456789"},
        {"name": "David Wilson", "email": "david@example.com", "phone": "555-123-4567"},
        {"name": "Eva Brown", "email": "eva@example.com", "phone": "+33612345678"},
    ]
    
    customers = []
    for data in customers_data:
        customer = Customer.objects.create(**data)
        customers.append(customer)
        print(f"Created customer: {customer.name} ({customer.email})")
    
    return customers

def create_products():
    """Create sample products."""
    print("Creating products...")
    
    products_data = [
        {"name": "Laptop", "description": "High-performance laptop", "price": Decimal("999.99"), "stock": 50},
        {"name": "Smartphone", "description": "Latest smartphone model", "price": Decimal("699.99"), "stock": 100},
        {"name": "Tablet", "description": "10-inch tablet", "price": Decimal("399.99"), "stock": 75},
        {"name": "Headphones", "description": "Wireless noise-cancelling headphones", "price": Decimal("199.99"), "stock": 150},
        {"name": "Smart Watch", "description": "Fitness tracking smartwatch", "price": Decimal("249.99"), "stock": 80},
        {"name": "Keyboard", "description": "Mechanical keyboard", "price": Decimal("129.99"), "stock": 60},
        {"name": "Mouse", "description": "Wireless gaming mouse", "price": Decimal("79.99"), "stock": 120},
        {"name": "Monitor", "description": "27-inch 4K monitor", "price": Decimal("449.99"), "stock": 40},
    ]
    
    products = []
    for data in products_data:
        product = Product.objects.create(**data)
        products.append(product)
        print(f"Created product: {product.name} - ${product.price}")
    
    return products

def create_orders(customers, products):
    """Create sample orders."""
    print("Creating orders...")
    
    orders_data = [
        {"customer": customers[0], "products": [products[0], products[1], products[2]]},
        {"customer": customers[1], "products": [products[3], products[4]]},
        {"customer": customers[2], "products": [products[5], products[6], products[7]]},
        {"customer": customers[3], "products": [products[0], products[3]]},
        {"customer": customers[4], "products": [products[1], products[4], products[5], products[6]]},
        {"customer": customers[0], "products": [products[7]]},
        {"customer": customers[1], "products": [products[2], products[3], products[4]]},
    ]
    
    orders = []
    for i, data in enumerate(orders_data):
        # Set order date to be in the past for some orders
        order_date = datetime.now() - timedelta(days=random.randint(0, 30))
        
        # Create order
        order = Order.objects.create(
            customer=data["customer"],
            order_date=order_date,
            status=random.choice(['pending', 'processing', 'shipped', 'delivered'])
        )
        
        # Add products to order
        order.products.add(*data["products"])
        
        # Calculate and save total
        order.total_amount = sum(p.price for p in data["products"])
        order.save()
        
        # Update product stock
        for product in data["products"]:
            if product.stock > 0:
                product.stock -= 1
                product.save()
        
        orders.append(order)
        print(f"Created order #{i+1} for {order.customer.name}: ${order.total_amount}")
    
    return orders

def main():
    """Main seeding function."""
    print("=" * 50)
    print("Starting database seeding...")
    print("=" * 50)
    
    # Clear existing data
    clear_database()
    
    # Create data
    customers = create_customers()
    products = create_products()
    orders = create_orders(customers, products)
    
    # Print summary
    print("=" * 50)
    print("Seeding completed!")
    print(f"Created: {len(customers)} customers")
    print(f"Created: {len(products)} products")
    print(f"Created: {len(orders)} orders")
    print("=" * 50)
    
    # Print sample GraphQL queries
    print("\nSample GraphQL Queries:")
    print("-" * 30)
    print("""
# Query all customers
{
  customers {
    id
    name
    email
    phone
    orders {
      id
      totalAmount
      products {
        name
        price
      }
    }
  }
}

# Query all products
{
  products {
    id
    name
    price
    stock
  }
}

# Query all orders
{
  orders {
    id
    customer {
      name
      email
    }
    products {
      name
      price
    }
    totalAmount
    status
    orderDate
  }
}
    """)

if __name__ == "__main__":
    main()