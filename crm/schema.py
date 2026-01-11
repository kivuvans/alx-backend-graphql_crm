

import graphene
from graphene_django import DjangoObjectType, DjangoFilterConnectionField
from graphene import relay
import django_filters
from django.db import models
from .models import Customer, Product, Order
from .filters import CustomerFilter, ProductFilter, OrderFilter

import graphene
from django.db.models import F
from crm.models import Product
# ---------------------- CONNECTION TYPES ----------------------

class CustomerNode(DjangoObjectType):
    """Customer node for Relay connection."""
    class Meta:
        model = Customer
        interfaces = (relay.Node,)
        fields = '__all__'
        filterset_class = CustomerFilter
    
    total_spent = graphene.Decimal()
    order_count = graphene.Int()
    
    def resolve_total_spent(self, info):
        """Calculate total amount spent by customer."""
        total = self.orders.aggregate(total=models.Sum('total_amount'))['total']
        return total or 0
    
    def resolve_order_count(self, info):
        """Count total orders by customer."""
        return self.orders.count()


class ProductNode(DjangoObjectType):
    """Product node for Relay connection."""
    class Meta:
        model = Product
        interfaces = (relay.Node,)
        fields = '__all__'
        filterset_class = ProductFilter
    
    in_stock = graphene.Boolean()
    
    def resolve_in_stock(self, info):
        """Check if product is in stock."""
        return self.stock > 0


class OrderNode(DjangoObjectType):
    """Order node for Relay connection."""
    class Meta:
        model = Order
        interfaces = (relay.Node,)
        fields = '__all__'
        filterset_class = OrderFilter
    
    product_count = graphene.Int()
    formatted_date = graphene.String()
    
    def resolve_product_count(self, info):
        """Count products in order."""
        return self.products.count()
    
    def resolve_formatted_date(self, info):
        """Return formatted order date."""
        return self.order_date.strftime('%Y-%m-%d %H:%M:%S')

# ---------------------- INPUT TYPES FOR FILTERING ----------------------

class OrderByInput(graphene.InputObjectType):
    """Input type for ordering/sorting."""
    field = graphene.String(required=True, description="Field to order by")
    direction = graphene.String(default_value="asc", description="Order direction: 'asc' or 'desc'")

# ---------------------- FILTER INPUT TYPES ----------------------

class CustomerFilterInput(graphene.InputObjectType):
    """Input type for customer filtering."""
    name = graphene.String(description="Filter by name (case-insensitive partial match)")
    name_icontains = graphene.String(description="Filter by name (case-insensitive partial match)")
    name_exact = graphene.String(description="Filter by exact name match")
    email = graphene.String(description="Filter by email (case-insensitive partial match)")
    email_exact = graphene.String(description="Filter by exact email match")
    phone = graphene.String(description="Filter by phone number")
    phone_pattern = graphene.String(description="Filter by phone pattern (e.g., starts with '+1')")
    created_at_gte = graphene.Date(description="Filter customers created on or after this date")
    created_at_lte = graphene.Date(description="Filter customers created on or before this date")
    order_count_gte = graphene.Int(description="Filter customers with at least this many orders")
    order_count_lte = graphene.Int(description="Filter customers with at most this many orders")
    has_phone = graphene.Boolean(description="Filter customers with/without phone number")


class ProductFilterInput(graphene.InputObjectType):
    """Input type for product filtering."""
    name = graphene.String(description="Filter by product name (case-insensitive partial match)")
    description = graphene.String(description="Filter by product description")
    price_gte = graphene.Decimal(description="Filter products with price >= value")
    price_lte = graphene.Decimal(description="Filter products with price <= value")
    stock_gte = graphene.Int(description="Filter products with stock >= value")
    stock_lte = graphene.Int(description="Filter products with stock <= value")
    low_stock = graphene.Int(description="Filter products with stock < value (default: <10)")
    out_of_stock = graphene.Boolean(description="Filter products that are out of stock")
    in_stock = graphene.Boolean(description="Filter products that are in stock")
    created_at_gte = graphene.Date(description="Filter products created on or after this date")
    created_at_lte = graphene.Date(description="Filter products created on or before this date")


class OrderFilterInput(graphene.InputObjectType):
    """Input type for order filtering."""
    total_amount_gte = graphene.Decimal(description="Filter orders with total amount >= value")
    total_amount_lte = graphene.Decimal(description="Filter orders with total amount <= value")
    order_date_gte = graphene.Date(description="Filter orders on or after this date")
    order_date_lte = graphene.Date(description="Filter orders on or before this date")
    customer_name = graphene.String(description="Filter orders by customer name")
    customer_email = graphene.String(description="Filter orders by customer email")
    customer_id = graphene.ID(description="Filter orders by customer ID")
    product_name = graphene.String(description="Filter orders by product name")
    product_id = graphene.ID(description="Filter orders by product ID")
    product_ids = graphene.List(graphene.ID, description="Filter orders that include any of these product IDs")
    status = graphene.String(description="Filter orders by status")
    status_in = graphene.List(graphene.String, description="Filter orders with any of these statuses")
    min_product_count = graphene.Int(description="Filter orders with at least this many products")
    max_product_count = graphene.Int(description="Filter orders with at most this many products")

# ---------------------- QUERIES WITH FILTERING ----------------------

class Query(graphene.ObjectType):
    """GraphQL queries for CRM with filtering support."""
    
    # Relay connections with filtering
    all_customers = DjangoFilterConnectionField(
        CustomerNode,
        filterset_class=CustomerFilter,
        order_by=graphene.String(description="Order results by field, use '-' for descending"),
        description="Get all customers with filtering and pagination"
    )
    
    all_products = DjangoFilterConnectionField(
        ProductNode,
        filterset_class=ProductFilter,
        order_by=graphene.String(description="Order results by field, use '-' for descending"),
        description="Get all products with filtering and pagination"
    )
    
    all_orders = DjangoFilterConnectionField(
        OrderNode,
        filterset_class=OrderFilter,
        order_by=graphene.String(description="Order results by field, use '-' for descending"),
        description="Get all orders with filtering and pagination"
    )
    
    # Single item queries
    customer = relay.Node.Field(CustomerNode, description="Get a single customer by ID")
    product = relay.Node.Field(ProductNode, description="Get a single product by ID")
    order = relay.Node.Field(OrderNode, description="Get a single order by ID")
    
    # Legacy simple queries (without Relay)
    customers = graphene.List(
        CustomerNode,
        filter=CustomerFilterInput(description="Filter criteria for customers"),
        order_by=graphene.String(description="Order by field, use '-' for descending"),
        description="Get customers with filtering"
    )
    
    products = graphene.List(
        ProductNode,
        filter=ProductFilterInput(description="Filter criteria for products"),
        order_by=graphene.String(description="Order by field, use '-' for descending"),
        description="Get products with filtering"
    )
    
    orders = graphene.List(
        OrderNode,
        filter=OrderFilterInput(description="Filter criteria for orders"),
        order_by=graphene.String(description="Order by field, use '-' for descending"),
        description="Get orders with filtering"
    )
    
    # Statistics
    customer_count = graphene.Int(
        filter=CustomerFilterInput(description="Filter criteria for counting"),
        description="Count customers matching filter"
    )
    
    product_count = graphene.Int(
        filter=ProductFilterInput(description="Filter criteria for counting"),
        description="Count products matching filter"
    )
    
    order_count = graphene.Int(
        filter=OrderFilterInput(description="Filter criteria for counting"),
        description="Count orders matching filter"
    )
    
    total_revenue = graphene.Decimal(
        filter=OrderFilterInput(description="Filter criteria for revenue calculation"),
        description="Total revenue from orders matching filter"
    )
    
    # Resolvers for simple queries
    def resolve_customers(self, info, filter=None, order_by=None):
        queryset = Customer.objects.all()
        
        if filter:
            # Apply filters manually
            if filter.get('name'):
                queryset = queryset.filter(name__icontains=filter['name'])
            if filter.get('email'):
                queryset = queryset.filter(email__icontains=filter['email'])
            if filter.get('phone'):
                queryset = queryset.filter(phone__icontains=filter['phone'])
            if filter.get('phone_pattern'):
                import re
                pattern = re.escape(filter['phone_pattern'])
                queryset = queryset.filter(phone__regex=f'^{pattern}')
            if filter.get('created_at_gte'):
                queryset = queryset.filter(created_at__gte=filter['created_at_gte'])
            if filter.get('created_at_lte'):
                queryset = queryset.filter(created_at__lte=filter['created_at_lte'])
        
        # Apply ordering
        if order_by:
            queryset = queryset.order_by(order_by)
        
        return queryset
    
    def resolve_products(self, info, filter=None, order_by=None):
        queryset = Product.objects.all()
        
        if filter:
            # Apply filters manually
            if filter.get('name'):
                queryset = queryset.filter(name__icontains=filter['name'])
            if filter.get('price_gte') is not None:
                queryset = queryset.filter(price__gte=filter['price_gte'])
            if filter.get('price_lte') is not None:
                queryset = queryset.filter(price__lte=filter['price_lte'])
            if filter.get('stock_gte') is not None:
                queryset = queryset.filter(stock__gte=filter['stock_gte'])
            if filter.get('stock_lte') is not None:
                queryset = queryset.filter(stock__lte=filter['stock_lte'])
            if filter.get('low_stock') is not None:
                threshold = filter['low_stock'] if filter['low_stock'] != 0 else 10
                queryset = queryset.filter(stock__lt=threshold)
            if filter.get('out_of_stock'):
                queryset = queryset.filter(stock=0)
            if filter.get('in_stock'):
                queryset = queryset.filter(stock__gt=0)
        
        # Apply ordering
        if order_by:
            queryset = queryset.order_by(order_by)
        
        return queryset
    
    def resolve_orders(self, info, filter=None, order_by=None):
        queryset = Order.objects.all()
        
        if filter:
            # Apply filters manually
            if filter.get('total_amount_gte') is not None:
                queryset = queryset.filter(total_amount__gte=filter['total_amount_gte'])
            if filter.get('total_amount_lte') is not None:
                queryset = queryset.filter(total_amount__lte=filter['total_amount_lte'])
            if filter.get('order_date_gte'):
                queryset = queryset.filter(order_date__gte=filter['order_date_gte'])
            if filter.get('order_date_lte'):
                queryset = queryset.filter(order_date__lte=filter['order_date_lte'])
            if filter.get('customer_name'):
                queryset = queryset.filter(customer__name__icontains=filter['customer_name'])
            if filter.get('product_name'):
                queryset = queryset.filter(products__name__icontains=filter['product_name'])
            if filter.get('status'):
                queryset = queryset.filter(status=filter['status'])
        
        # Remove duplicates from M2M relationships
        queryset = queryset.distinct()
        
        # Apply ordering
        if order_by:
            queryset = queryset.order_by(order_by)
        
        return queryset
    
    # Resolvers for statistics
    def resolve_customer_count(self, info, filter=None):
        queryset = Customer.objects.all()
        
        if filter:
            # Apply the same filters as resolve_customers
            if filter.get('name'):
                queryset = queryset.filter(name__icontains=filter['name'])
            if filter.get('email'):
                queryset = queryset.filter(email__icontains=filter['email'])
            if filter.get('phone_pattern'):
                import re
                pattern = re.escape(filter['phone_pattern'])
                queryset = queryset.filter(phone__regex=f'^{pattern}')
        
        return queryset.count()
    
    def resolve_product_count(self, info, filter=None):
        queryset = Product.objects.all()
        
        if filter:
            if filter.get('name'):
                queryset = queryset.filter(name__icontains=filter['name'])
            if filter.get('price_gte') is not None:
                queryset = queryset.filter(price__gte=filter['price_gte'])
            if filter.get('price_lte') is not None:
                queryset = queryset.filter(price__lte=filter['price_lte'])
        
        return queryset.count()
    
    def resolve_order_count(self, info, filter=None):
        queryset = Order.objects.all()
        
        if filter:
            if filter.get('total_amount_gte') is not None:
                queryset = queryset.filter(total_amount__gte=filter['total_amount_gte'])
            if filter.get('status'):
                queryset = queryset.filter(status=filter['status'])
        
        return queryset.count()
    
    def resolve_total_revenue(self, info, filter=None):
        queryset = Order.objects.filter(status__in=['delivered', 'shipped'])
        
        if filter:
            if filter.get('total_amount_gte') is not None:
                queryset = queryset.filter(total_amount__gte=filter['total_amount_gte'])
            if filter.get('total_amount_lte') is not None:
                queryset = queryset.filter(total_amount__lte=filter['total_amount_lte'])
            if filter.get('order_date_gte'):
                queryset = queryset.filter(order_date__gte=filter['order_date_gte'])
            if filter.get('order_date_lte'):
                queryset = queryset.filter(order_date__lte=filter['order_date_lte'])
        
        total = queryset.aggregate(total=models.Sum('total_amount'))['total']
        return total or 0


# Keep your existing Mutation class (from previous tasks)
from .mutations import Mutation as CRMMutation

class Mutation(CRMMutation, graphene.ObjectType):
    """GraphQL mutations for CRM."""
    update_low_stock_products = UpdateLowStockProducts.Field()
    pass

class UpdateLowStockProducts(graphene.Mutation):
    products = graphene.List(lambda: ProductType)
    message = graphene.String()

    def mutate(self, info):
        low_stock_products = Product.objects.filter(stock__lt=10)

        updated_products = []
        for product in low_stock_products:
            product.stock += 10
            product.save()
            updated_products.append(product)

        return UpdateLowStockProducts(
            products=updated_products,
            message="Low stock products updated successfully"
        )
