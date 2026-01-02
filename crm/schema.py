import graphene
from graphene_django import DjangoObjectType
from django.db import transaction, models
import re
from decimal import Decimal
import uuid
from datetime import datetime
from .models import Customer, Product, Order

# ---------------------- TYPES ----------------------

class CustomerType(DjangoObjectType):
    """Customer GraphQL type with additional computed fields."""
    class Meta:
        model = Customer
        fields = '__all__'
    
    total_spent = graphene.Decimal()
    order_count = graphene.Int()
    
    def resolve_total_spent(self, info):
        """Calculate total amount spent by customer."""
        total = self.orders.aggregate(total=models.Sum('total_amount'))['total']
        return total or Decimal('0')
    
    def resolve_order_count(self, info):
        """Count total orders by customer."""
        return self.orders.count()


class ProductType(DjangoObjectType):
    """Product GraphQL type with additional fields."""
    class Meta:
        model = Product
        fields = '__all__'
    
    in_stock = graphene.Boolean()
    
    def resolve_in_stock(self, info):
        """Check if product is in stock."""
        return self.stock > 0


class OrderType(DjangoObjectType):
    """Order GraphQL type with enhanced relationships."""
    class Meta:
        model = Order
        fields = '__all__'
    
    product_count = graphene.Int()
    formatted_date = graphene.String()
    
    def resolve_product_count(self, info):
        """Count products in order."""
        return self.products.count()
    
    def resolve_formatted_date(self, info):
        """Return formatted order date."""
        return self.order_date.strftime('%Y-%m-%d %H:%M:%S')


# ---------------------- INPUTS ----------------------

class CustomerInput(graphene.InputObjectType):
    name = graphene.String(required=True, description="Customer's full name")
    email = graphene.String(required=True, description="Unique email address")
    phone = graphene.String(description="Phone number in international or local format")


class BulkCustomerInput(graphene.InputObjectType):
    customers = graphene.List(CustomerInput, required=True, description="List of customers to create")


class ProductInput(graphene.InputObjectType):
    name = graphene.String(required=True, description="Product name")
    description = graphene.String(description="Product description")
    price = graphene.Decimal(required=True, description="Product price (positive decimal)")
    stock = graphene.Int(description="Initial stock quantity")


class OrderInput(graphene.InputObjectType):
    customer_id = graphene.ID(required=True, description="Existing customer ID")
    product_ids = graphene.List(graphene.ID, required=True, description="List of existing product IDs")
    status = graphene.String(description="Order status")


class UpdateCustomerInput(graphene.InputObjectType):
    """Input for updating customer information."""
    id = graphene.ID(required=True, description="Customer ID")
    name = graphene.String(description="Updated name")
    phone = graphene.String(description="Updated phone number")


class UpdateProductStockInput(graphene.InputObjectType):
    """Input for updating product stock."""
    id = graphene.ID(required=True, description="Product ID")
    stock_change = graphene.Int(required=True, description="Change in stock (positive to add, negative to remove)")


class CancelOrderInput(graphene.InputObjectType):
    """Input for canceling an order."""
    id = graphene.ID(required=True, description="Order ID")
    reason = graphene.String(description="Cancellation reason")


# ---------------------- RESPONSE TYPES ----------------------

class MutationResponse(graphene.ObjectType):
    """Base response type for mutations."""
    success = graphene.Boolean(required=True)
    message = graphene.String()
    errors = graphene.List(graphene.String)


class CustomerResponse(MutationResponse):
    """Response type for customer mutations."""
    customer = graphene.Field(CustomerType)


class BulkCustomerResponse(MutationResponse):
    """Response type for bulk customer mutations."""
    customers = graphene.List(CustomerType)
    created_count = graphene.Int()
    failed_count = graphene.Int()


class ProductResponse(MutationResponse):
    """Response type for product mutations."""
    product = graphene.Field(ProductType)


class OrderResponse(MutationResponse):
    """Response type for order mutations."""
    order = graphene.Field(OrderType)


# ---------------------- VALIDATION UTILITIES ----------------------

class ValidationUtils:
    """Utility class for input validation."""
    
    @staticmethod
    def validate_email(email):
        """Validate email format."""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(pattern, email):
            return False, "Invalid email format"
        return True, None
    
    @staticmethod
    def validate_phone(phone):
        """Validate phone number format."""
        if not phone:
            return True, None
        
        # Multiple formats supported
        patterns = [
            r'^\+\d{1,3}[- ]?\d{6,14}$',  # International: +1234567890
            r'^\d{3}[- ]?\d{3}[- ]?\d{4}$',  # Local: 123-456-7890
            r'^\(\d{3}\) \d{3}-\d{4}$',  # Local: (123) 456-7890
        ]
        
        for pattern in patterns:
            if re.match(pattern, phone):
                return True, None
        
        return False, "Invalid phone format. Use +1234567890 or 123-456-7890"
    
    @staticmethod
    def validate_price(price):
        """Validate price is positive."""
        if price <= Decimal('0'):
            return False, "Price must be greater than 0"
        return True, None
    
    @staticmethod
    def validate_stock(stock):
        """Validate stock is non-negative."""
        if stock < 0:
            return False, "Stock cannot be negative"
        return True, None
    
    @staticmethod
    def validate_name(name):
        """Validate name is not empty."""
        if not name or not name.strip():
            return False, "Name cannot be empty"
        return True, None


# ---------------------- MUTATIONS ----------------------

class CreateCustomer(graphene.Mutation):
    """Mutation to create a single customer."""
    
    class Arguments:
        input = CustomerInput(required=True)
    
    Output = CustomerResponse
    
    @staticmethod
    def mutate(root, info, input):
        try:
            # Validate inputs
            is_valid, error = ValidationUtils.validate_name(input.name)
            if not is_valid:
                return CustomerResponse(success=False, message=error)
            
            is_valid, error = ValidationUtils.validate_email(input.email)
            if not is_valid:
                return CustomerResponse(success=False, message=error)
            
            if input.phone:
                is_valid, error = ValidationUtils.validate_phone(input.phone)
                if not is_valid:
                    return CustomerResponse(success=False, message=error)
            
            # Check for duplicate email
            if Customer.objects.filter(email=input.email).exists():
                return CustomerResponse(
                    success=False, 
                    message=f"Email '{input.email}' already exists"
                )
            
            # Create customer
            customer = Customer(
                name=input.name.strip(),
                email=input.email.lower(),
                phone=input.phone if input.phone else None
            )
            customer.save()
            
            return CustomerResponse(
                success=True,
                message="Customer created successfully",
                customer=customer
            )
            
        except Exception as e:
            return CustomerResponse(
                success=False,
                message=f"Error creating customer: {str(e)}"
            )


class BulkCreateCustomers(graphene.Mutation):
    """Mutation to create multiple customers in bulk."""
    
    class Arguments:
        input = BulkCustomerInput(required=True)
    
    Output = BulkCustomerResponse
    
    @transaction.atomic
    def mutate(root, info, input):
        customers = []
        errors = []
        created_count = 0
        failed_count = 0
        
        for idx, customer_input in enumerate(input.customers):
            try:
                # Validate name
                is_valid, error_msg = ValidationUtils.validate_name(customer_input.name)
                if not is_valid:
                    errors.append(f"Row {idx + 1}: {error_msg}")
                    failed_count += 1
                    continue
                
                # Validate email
                is_valid, error_msg = ValidationUtils.validate_email(customer_input.email)
                if not is_valid:
                    errors.append(f"Row {idx + 1}: {error_msg}")
                    failed_count += 1
                    continue
                
                # Validate phone if provided
                if customer_input.phone:
                    is_valid, error_msg = ValidationUtils.validate_phone(customer_input.phone)
                    if not is_valid:
                        errors.append(f"Row {idx + 1}: {error_msg}")
                        failed_count += 1
                        continue
                
                # Check for duplicate email
                if Customer.objects.filter(email=customer_input.email.lower()).exists():
                    errors.append(f"Row {idx + 1}: Email '{customer_input.email}' already exists")
                    failed_count += 1
                    continue
                
                # Create customer
                customer = Customer(
                    name=customer_input.name.strip(),
                    email=customer_input.email.lower(),
                    phone=customer_input.phone if customer_input.phone else None
                )
                customer.save()
                
                customers.append(customer)
                created_count += 1
                
            except Exception as e:
                errors.append(f"Row {idx + 1}: {str(e)}")
                failed_count += 1
        
        message = f"Created {created_count} customer(s), {failed_count} failed"
        return BulkCustomerResponse(
            success=created_count > 0,
            message=message,
            customers=customers,
            errors=errors if errors else None,
            created_count=created_count,
            failed_count=failed_count
        )


class CreateProduct(graphene.Mutation):
    """Mutation to create a product."""
    
    class Arguments:
        input = ProductInput(required=True)
    
    Output = ProductResponse
    
    @staticmethod
    def mutate(root, info, input):
        try:
            # Validate name
            is_valid, error = ValidationUtils.validate_name(input.name)
            if not is_valid:
                return ProductResponse(success=False, message=error)
            
            # Validate price
            is_valid, error = ValidationUtils.validate_price(input.price)
            if not is_valid:
                return ProductResponse(success=False, message=error)
            
            # Validate stock
            stock = input.stock if input.stock is not None else 0
            is_valid, error = ValidationUtils.validate_stock(stock)
            if not is_valid:
                return ProductResponse(success=False, message=error)
            
            # Create product
            product = Product(
                name=input.name.strip(),
                description=input.description.strip() if input.description else "",
                price=input.price,
                stock=stock
            )
            product.save()
            
            return ProductResponse(
                success=True,
                message="Product created successfully",
                product=product
            )
            
        except Exception as e:
            return ProductResponse(
                success=False,
                message=f"Error creating product: {str(e)}"
            )


class CreateOrder(graphene.Mutation):
    """Mutation to create an order."""
    
    class Arguments:
        input = OrderInput(required=True)
    
    Output = OrderResponse
    
    @transaction.atomic
    def mutate(root, info, input):
        try:
            # Validate customer exists
            try:
                customer = Customer.objects.get(id=input.customer_id)
            except Customer.DoesNotExist:
                return OrderResponse(
                    success=False,
                    message=f"Customer with ID '{input.customer_id}' not found"
                )
            
            # Validate at least one product
            if not input.product_ids:
                return OrderResponse(
                    success=False,
                    message="At least one product is required"
                )
            
            # Get and validate products
            products = []
            total_amount = Decimal('0')
            
            for product_id in input.product_ids:
                try:
                    product = Product.objects.get(id=product_id)
                    
                    # Check stock availability
                    if product.stock < 1:
                        return OrderResponse(
                            success=False,
                            message=f"Product '{product.name}' is out of stock"
                        )
                    
                    products.append(product)
                    total_amount += product.price
                    
                except Product.DoesNotExist:
                    return OrderResponse(
                        success=False,
                        message=f"Product with ID '{product_id}' not found"
                    )
            
            # Create order
            order = Order(
                customer=customer,
                status=input.status if input.status else 'pending',
                total_amount=total_amount
            )
            order.save()
            
            # Add products to order
            order.products.add(*products)
            
            # Update product stock
            for product in products:
                product.stock -= 1
                product.save(update_fields=['stock'])
            
            # Refresh order to get calculated total
            order.refresh_from_db()
            
            return OrderResponse(
                success=True,
                message="Order created successfully",
                order=order
            )
            
        except Exception as e:
            return OrderResponse(
                success=False,
                message=f"Error creating order: {str(e)}"
            )


# ---------------------- NEW ENHANCED MUTATIONS ----------------------

class UpdateCustomer(graphene.Mutation):
    """Mutation to update customer information."""
    
    class Arguments:
        input = UpdateCustomerInput(required=True)
    
    Output = CustomerResponse
    
    @staticmethod
    def mutate(root, info, input):
        try:
            # Get customer
            try:
                customer = Customer.objects.get(id=input.id)
            except Customer.DoesNotExist:
                return CustomerResponse(
                    success=False,
                    message=f"Customer with ID '{input.id}' not found"
                )
            
            # Update fields if provided
            if input.name:
                is_valid, error = ValidationUtils.validate_name(input.name)
                if not is_valid:
                    return CustomerResponse(success=False, message=error)
                customer.name = input.name.strip()
            
            if input.phone:
                is_valid, error = ValidationUtils.validate_phone(input.phone)
                if not is_valid:
                    return CustomerResponse(success=False, message=error)
                customer.phone = input.phone
            
            customer.save()
            
            return CustomerResponse(
                success=True,
                message="Customer updated successfully",
                customer=customer
            )
            
        except Exception as e:
            return CustomerResponse(
                success=False,
                message=f"Error updating customer: {str(e)}"
            )


class UpdateProductStock(graphene.Mutation):
    """Mutation to update product stock."""
    
    class Arguments:
        input = UpdateProductStockInput(required=True)
    
    Output = ProductResponse
    
    @staticmethod
    def mutate(root, info, input):
        try:
            # Get product
            try:
                product = Product.objects.get(id=input.id)
            except Product.DoesNotExist:
                return ProductResponse(
                    success=False,
                    message=f"Product with ID '{input.id}' not found"
                )
            
            # Calculate new stock
            new_stock = product.stock + input.stock_change
            
            # Validate new stock
            if new_stock < 0:
                return ProductResponse(
                    success=False,
                    message=f"Cannot reduce stock below 0. Current stock: {product.stock}"
                )
            
            # Update stock
            product.stock = new_stock
            product.save(update_fields=['stock'])
            
            action = "added to" if input.stock_change > 0 else "removed from"
            return ProductResponse(
                success=True,
                message=f"Stock {action} product. New stock: {new_stock}",
                product=product
            )
            
        except Exception as e:
            return ProductResponse(
                success=False,
                message=f"Error updating product stock: {str(e)}"
            )


class CancelOrder(graphene.Mutation):
    """Mutation to cancel an order."""
    
    class Arguments:
        input = CancelOrderInput(required=True)
    
    Output = OrderResponse
    
    @transaction.atomic
    def mutate(root, info, input):
        try:
            # Get order
            try:
                order = Order.objects.get(id=input.id)
            except Order.DoesNotExist:
                return OrderResponse(
                    success=False,
                    message=f"Order with ID '{input.id}' not found"
                )
            
            # Check if order can be cancelled
            if order.status == 'cancelled':
                return OrderResponse(
                    success=False,
                    message="Order is already cancelled"
                )
            
            if order.status == 'delivered':
                return OrderResponse(
                    success=False,
                    message="Cannot cancel delivered orders"
                )
            
            # Cancel order
            order.status = 'cancelled'
            order.save(update_fields=['status'])
            
            # Restock products
            for product in order.products.all():
                product.stock += 1
                product.save(update_fields=['stock'])
            
            reason_msg = f" Reason: {input.reason}" if input.reason else ""
            return OrderResponse(
                success=True,
                message=f"Order cancelled successfully.{reason_msg}",
                order=order
            )
            
        except Exception as e:
            return OrderResponse(
                success=False,
                message=f"Error cancelling order: {str(e)}"
            )


# ---------------------- QUERIES ----------------------

class Query(graphene.ObjectType):
    """GraphQL queries for CRM."""
    
    # Customer queries
    customers = graphene.List(
        CustomerType,
        search=graphene.String(description="Search customers by name or email"),
        email=graphene.String(description="Filter by exact email")
    )
    
    customer = graphene.Field(
        CustomerType,
        id=graphene.ID(required=True, description="Customer ID")
    )
    
    # Product queries
    products = graphene.List(
        ProductType,
        search=graphene.String(description="Search products by name"),
        min_price=graphene.Decimal(description="Minimum price filter"),
        max_price=graphene.Decimal(description="Maximum price filter"),
        in_stock=graphene.Boolean(description="Filter by stock availability")
    )
    
    product = graphene.Field(
        ProductType,
        id=graphene.ID(required=True, description="Product ID")
    )
    
    # Order queries
    orders = graphene.List(
        OrderType,
        customer_id=graphene.ID(description="Filter by customer ID"),
        status=graphene.String(description="Filter by order status"),
        start_date=graphene.DateTime(description="Start date filter"),
        end_date=graphene.DateTime(description="End date filter")
    )
    
    order = graphene.Field(
        OrderType,
        id=graphene.ID(required=True, description="Order ID")
    )
    
    # Statistics
    customer_count = graphene.Int()
    product_count = graphene.Int()
    order_count = graphene.Int()
    total_revenue = graphene.Decimal()
    
    # Resolvers
    def resolve_customers(self, info, search=None, email=None):
        queryset = Customer.objects.all()
        
        if search:
            queryset = queryset.filter(
                models.Q(name__icontains=search) |
                models.Q(email__icontains=search)
            )
        
        if email:
            queryset = queryset.filter(email=email)
        
        return queryset
    
    def resolve_customer(self, info, id):
        try:
            return Customer.objects.get(id=id)
        except Customer.DoesNotExist:
            return None
    
    def resolve_products(self, info, search=None, min_price=None, max_price=None, in_stock=None):
        queryset = Product.objects.all()
        
        if search:
            queryset = queryset.filter(name__icontains=search)
        
        if min_price is not None:
            queryset = queryset.filter(price__gte=min_price)
        
        if max_price is not None:
            queryset = queryset.filter(price__lte=max_price)
        
        if in_stock is not None:
            if in_stock:
                queryset = queryset.filter(stock__gt=0)
            else:
                queryset = queryset.filter(stock=0)
        
        return queryset
    
    def resolve_product(self, info, id):
        try:
            return Product.objects.get(id=id)
        except Product.DoesNotExist:
            return None
    
    def resolve_orders(self, info, customer_id=None, status=None, start_date=None, end_date=None):
        queryset = Order.objects.all()
        
        if customer_id:
            queryset = queryset.filter(customer_id=customer_id)
        
        if status:
            queryset = queryset.filter(status=status)
        
        if start_date:
            queryset = queryset.filter(order_date__gte=start_date)
        
        if end_date:
            queryset = queryset.filter(order_date__lte=end_date)
        
        return queryset
    
    def resolve_order(self, info, id):
        try:
            return Order.objects.get(id=id)
        except Order.DoesNotExist:
            return None
    
    def resolve_customer_count(self, info):
        return Customer.objects.count()
    
    def resolve_product_count(self, info):
        return Product.objects.count()
    
    def resolve_order_count(self, info):
        return Order.objects.count()
    
    def resolve_total_revenue(self, info):
        total = Order.objects.filter(status__in=['delivered', 'shipped']).aggregate(
            total=models.Sum('total_amount')
        )['total']
        return total or Decimal('0')


# ---------------------- MUTATIONS CLASS ----------------------

class Mutation(graphene.ObjectType):
    """GraphQL mutations for CRM."""
    
    # Original mutations
    create_customer = CreateCustomer.Field()
    bulk_create_customers = BulkCreateCustomers.Field()
    create_product = CreateProduct.Field()
    create_order = CreateOrder.Field()
    
    # Enhanced mutations
    update_customer = UpdateCustomer.Field()
    update_product_stock = UpdateProductStock.Field()
    cancel_order = CancelOrder.Field()