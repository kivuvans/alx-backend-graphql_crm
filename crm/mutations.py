import graphene
from graphene_django import DjangoObjectType
from django.db import transaction
import re
from decimal import Decimal
from .models import Customer, Product, Order

# ... (Copy all your mutation classes from the previous schema.py here)
# I won't duplicate them here for brevity, but you should move:
# CreateCustomer, BulkCreateCustomers, CreateProduct, CreateOrder,
# UpdateCustomer, UpdateProductStock, CancelOrder, and Mutation class

class Mutation(graphene.ObjectType):
    """GraphQL mutations for CRM."""
    create_customer = CreateCustomer.Field()
    bulk_create_customers = BulkCreateCustomers.Field()
    create_product = CreateProduct.Field() # type: ignore
    create_order = CreateOrder.Field()
    update_customer = UpdateCustomer.Field()
    update_product_stock = UpdateProductStock.Field()
    cancel_order = CancelOrder.Field()

