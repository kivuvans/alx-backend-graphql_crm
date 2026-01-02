import graphene
from graphene_django import DjangoObjectType
from django.db import transaction
import re
from decimal import Decimal
from .models import Customer, Product, Order

# ---------------------- TYPES ----------------------

class CustomerType(DjangoObjectType):
    class Meta:
        model = Customer
        fields = '__all__'


class ProductType(DjangoObjectType):
    class Meta:
        model = Product
        fields = '__all__'


class OrderType(DjangoObjectType):
    class Meta:
        model = Order
        fields = '__all__'

    total_amount = graphene.Decimal()

    def resolve_total_amount(self, info):
        return self.total_amount

# ---------------------- INPUTS ----------------------

class CustomerInput(graphene.InputObjectType):
    name = graphene.String(required=True)
    email = graphene.String(required=True)
    phone = graphene.String()


class ProductInput(graphene.InputObjectType):
    name = graphene.String(required=True)
    description = graphene.String()
    price = graphene.Decimal(required=True)
    stock = graphene.Int()


class OrderInput(graphene.InputObjectType):
    customer_id = graphene.ID(required=True)
    product_ids = graphene.List(graphene.ID, required=True)
    order_date = graphene.DateTime()
    status = graphene.String()


# ---------------------- MUTATIONS ----------------------

class CreateCustomer(graphene.Mutation):
    """Mutation to create a single customer."""
    class Arguments:
        input = CustomerInput(required=True)

    customer = graphene.Field(CustomerType)
    message = graphene.String()
    success = graphene.Boolean()

    @staticmethod
    def validate_phone(phone):
        """Validate phone number format."""
        if not phone:
            return True
        # Support formats: +1234567890 or 123-456-7890 or (123) 456-7890
        pattern = r'^(\+\d{1,3}[- ]?)?(\(?\d{3}\)?[- ]?)?\d{3}[- ]?\d{4}$'
        return bool(re.match(pattern, phone))

    @staticmethod
    def validate_email(email):
        """Basic email validation."""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))

    def mutate(self, info, input):
        # Validate email format
        if not self.validate_email(input.email):
            raise Exception("Invalid email format")

        # Validate phone format
        if input.phone and not self.validate_phone(input.phone):
            raise Exception("Invalid phone format. Use +1234567890 or 123-456-7890")

        # Check for duplicate email
        if Customer.objects.filter(email=input.email).exists():
            raise Exception(f"Email '{input.email}' already exists")

        # Create customer
        customer = Customer(
            name=input.name,
            email=input.email,
            phone=input.phone if input.phone else None
        )
        customer.save()

        return CreateCustomer(
            customer=customer,
            message="Customer created successfully",
            success=True
        )


class BulkCreateCustomers(graphene.Mutation):
    """Mutation to create multiple customers at once."""
    class Arguments:
        inputs = graphene.List(CustomerInput, required=True)

    customers = graphene.List(CustomerType)
    errors = graphene.List(graphene.String)
    success_count = graphene.Int()
    error_count = graphene.Int()

    @transaction.atomic
    def mutate(self, info, inputs):
        customers = []
        errors = []
        
        for index, input_data in enumerate(inputs):
            try:
                # Validate email format
                email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
                if not re.match(email_pattern, input_data.email):
                    errors.append(f"Row {index + 1}: Invalid email format")
                    continue

                # Validate phone format if provided
                if input_data.phone:
                    phone_pattern = r'^(\+\d{1,3}[- ]?)?(\(?\d{3}\)?[- ]?)?\d{3}[- ]?\d{4}$'
                    if not re.match(phone_pattern, input_data.phone):
                        errors.append(f"Row {index + 1}: Invalid phone format")
                        continue

                # Check for duplicate email
                if Customer.objects.filter(email=input_data.email).exists():
                    errors.append(f"Row {index + 1}: Email '{input_data.email}' already exists")
                    continue

                # Create customer
                customer = Customer(
                    name=input_data.name,
                    email=input_data.email,
                    phone=input_data.phone if input_data.phone else None
                )
                customer.save()
                customers.append(customer)

            except Exception as e:
                errors.append(f"Row {index + 1}: {str(e)}")

        return BulkCreateCustomers(
            customers=customers,
            errors=errors,
            success_count=len(customers),
            error_count=len(errors)
        )


class CreateProduct(graphene.Mutation):
    """Mutation to create a product."""
    class Arguments:
        input = ProductInput(required=True)

    product = graphene.Field(ProductType)
    message = graphene.String()

    def mutate(self, info, input):
        # Validate price is positive
        if input.price <= Decimal('0'):
            raise Exception("Price must be greater than 0")

        # Validate stock is not negative
        if input.stock and input.stock < 0:
            raise Exception("Stock cannot be negative")

        # Create product
        product = Product(
            name=input.name,
            description=input.description if input.description else "",
            price=input.price,
            stock=input.stock if input.stock else 0
        )
        product.save()

        return CreateProduct(
            product=product,
            message="Product created successfully"
        )


class CreateOrder(graphene.Mutation):
    """Mutation to create an order."""
    class Arguments:
        input = OrderInput(required=True)

    order = graphene.Field(OrderType)
    message = graphene.String()

    @transaction.atomic
    def mutate(self, info, input):
        # Validate customer exists
        try:
            customer = Customer.objects.get(id=input.customer_id)
        except Customer.DoesNotExist:
            raise Exception(f"Customer with ID '{input.customer_id}' not found")

        # Validate at least one product
        if not input.product_ids:
            raise Exception("At least one product is required")

        # Get and validate products
        products = []
        total_amount = Decimal('0')
        
        for product_id in input.product_ids:
            try:
                product = Product.objects.get(id=product_id)
                products.append(product)
                total_amount += product.price
            except Product.DoesNotExist:
                raise Exception(f"Product with ID '{product_id}' not found")

        # Validate stock availability
        for product in products:
            if product.stock < 1:
                raise Exception(f"Product '{product.name}' is out of stock")

        # Create order
        order = Order(
            customer=customer,
            order_date=input.order_date if input.order_date else None,
            status=input.status if input.status else 'pending',
            total_amount=total_amount
        )
        order.save()

        # Add products to order (ManyToMany relationship)
        order.products.add(*products)

        # Update product stock
        for product in products:
            product.stock -= 1
            product.save()

        return CreateOrder(
            order=order,
            message="Order created successfully"
        )


# ---------------------- QUERIES ----------------------

class Query(graphene.ObjectType):
    """GraphQL queries for CRM."""
    customers = graphene.List(CustomerType)
    customer = graphene.Field(CustomerType, id=graphene.ID(required=True))
    
    products = graphene.List(ProductType)
    product = graphene.Field(ProductType, id=graphene.ID(required=True))
    
    orders = graphene.List(OrderType)
    order = graphene.Field(OrderType, id=graphene.ID(required=True))

    def resolve_customers(self, info):
        return Customer.objects.all()

    def resolve_customer(self, info, id):
        try:
            return Customer.objects.get(id=id)
        except Customer.DoesNotExist:
            return None

    def resolve_products(self, info):
        return Product.objects.all()

    def resolve_product(self, info, id):
        try:
            return Product.objects.get(id=id)
        except Product.DoesNotExist:
            return None

    def resolve_orders(self, info):
        return Order.objects.all()

    def resolve_order(self, info, id):
        try:
            return Order.objects.get(id=id)
        except Order.DoesNotExist:
            return None


# ---------------------- MUTATIONS CLASS ----------------------

class Mutation(graphene.ObjectType):
    """GraphQL mutations for CRM."""
    create_customer = CreateCustomer.Field()
    bulk_create_customers = BulkCreateCustomers.Field()
    create_product = CreateProduct.Field()
    create_order = CreateOrder.Field()