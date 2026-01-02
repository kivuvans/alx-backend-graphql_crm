import django_filters as filters
from .models import Customer, Product, Order
from django.db import models
import re

class CustomerFilter(filters.FilterSet):
    """Filter for Customer model."""
    
    name = filters.CharFilter(
        field_name='name',
        lookup_expr='icontains',
        help_text="Case-insensitive partial match for customer name"
    )
    
    name_exact = filters.CharFilter(
        field_name='name',
        lookup_expr='iexact',
        help_text="Case-insensitive exact match for customer name"
    )
    
    email = filters.CharFilter(
        field_name='email',
        lookup_expr='icontains',
        help_text="Case-insensitive partial match for customer email"
    )
    
    email_exact = filters.CharFilter(
        field_name='email',
        lookup_expr='iexact',
        help_text="Case-insensitive exact match for customer email"
    )
    
    phone = filters.CharFilter(
        field_name='phone',
        lookup_expr='icontains',
        help_text="Partial match for phone number"
    )
    
    phone_exact = filters.CharFilter(
        field_name='phone',
        lookup_expr='iexact',
        help_text="Exact match for phone number"
    )
    
    phone_pattern = filters.CharFilter(
        method='filter_phone_pattern',
        help_text="Filter by phone number pattern (e.g., starts with +1)"
    )
    
    created_at_gte = filters.DateFilter(
        field_name='created_at',
        lookup_expr='gte',
        help_text="Filter customers created on or after this date"
    )
    
    created_at_lte = filters.DateFilter(
        field_name='created_at',
        lookup_expr='lte',
        help_text="Filter customers created on or before this date"
    )
    
    updated_at_gte = filters.DateFilter(
        field_name='updated_at',
        lookup_expr='gte',
        help_text="Filter customers updated on or after this date"
    )
    
    updated_at_lte = filters.DateFilter(
        field_name='updated_at',
        lookup_expr='lte',
        help_text="Filter customers updated on or before this date"
    )
    
    has_phone = filters.BooleanFilter(
        field_name='phone',
        lookup_expr='isnull',
        exclude=True,
        help_text="Filter customers with/without phone number"
    )
    
    order_count_gte = filters.NumberFilter(
        method='filter_by_order_count',
        help_text="Filter customers with at least this many orders"
    )
    
    order_count_lte = filters.NumberFilter(
        method='filter_by_order_count',
        help_text="Filter customers with at most this many orders"
    )
    
    def filter_phone_pattern(self, queryset, name, value):
        """Custom filter for phone number pattern."""
        if value:
            # Remove any non-digit characters except + for pattern matching
            pattern = re.escape(value)
            # Create regex pattern to match phone numbers starting with the pattern
            regex_pattern = f'^{pattern}'
            return queryset.filter(phone__regex=regex_pattern)
        return queryset
    
    def filter_by_order_count(self, queryset, name, value):
        """Filter customers by number of orders."""
        if value is not None:
            # Annotate each customer with their order count
            queryset = queryset.annotate(
                order_count=models.Count('orders')
            )
            
            if name == 'order_count_gte':
                return queryset.filter(order_count__gte=value)
            elif name == 'order_count_lte':
                return queryset.filter(order_count__lte=value)
        
        return queryset
    
    class Meta:
        model = Customer
        fields = {
            'name': ['exact', 'icontains', 'istartswith', 'iendswith'],
            'email': ['exact', 'icontains', 'istartswith', 'iendswith'],
            'phone': ['exact', 'icontains', 'istartswith', 'iendswith'],
        }
        # Auto-generate filters for all fields with common lookups
        filter_overrides = {
            models.CharField: {
                'filter_class': filters.CharFilter,
                'extra': lambda f: {
                    'lookup_expr': 'icontains',
                },
            },
            models.EmailField: {
                'filter_class': filters.CharFilter,
                'extra': lambda f: {
                    'lookup_expr': 'icontains',
                },
            },
        }


class ProductFilter(filters.FilterSet):
    """Filter for Product model."""
    
    name = filters.CharFilter(
        field_name='name',
        lookup_expr='icontains',
        help_text="Case-insensitive partial match for product name"
    )
    
    description = filters.CharFilter(
        field_name='description',
        lookup_expr='icontains',
        help_text="Case-insensitive partial match for product description"
    )
    
    price_gte = filters.NumberFilter(
        field_name='price',
        lookup_expr='gte',
        help_text="Filter products with price greater than or equal to"
    )
    
    price_lte = filters.NumberFilter(
        field_name='price',
        lookup_expr='lte',
        help_text="Filter products with price less than or equal to"
    )
    
    price_exact = filters.NumberFilter(
        field_name='price',
        lookup_expr='exact',
        help_text="Exact price match"
    )
    
    stock_gte = filters.NumberFilter(
        field_name='stock',
        lookup_expr='gte',
        help_text="Filter products with stock greater than or equal to"
    )
    
    stock_lte = filters.NumberFilter(
        field_name='stock',
        lookup_expr='lte',
        help_text="Filter products with stock less than or equal to"
    )
    
    stock_exact = filters.NumberFilter(
        field_name='stock',
        lookup_expr='exact',
        help_text="Exact stock match"
    )
    
    low_stock = filters.NumberFilter(
        method='filter_low_stock',
        help_text="Filter products with stock less than this value (default: 10)"
    )
    
    out_of_stock = filters.BooleanFilter(
        field_name='stock',
        lookup_expr='exact',
        method='filter_out_of_stock',
        help_text="Filter products that are out of stock"
    )
    
    in_stock = filters.BooleanFilter(
        method='filter_in_stock',
        help_text="Filter products that are in stock"
    )
    
    created_at_gte = filters.DateFilter(
        field_name='created_at',
        lookup_expr='gte',
        help_text="Filter products created on or after this date"
    )
    
    created_at_lte = filters.DateFilter(
        field_name='created_at',
        lookup_expr='lte',
        help_text="Filter products created on or before this date"
    )
    
    def filter_low_stock(self, queryset, name, value):
        """Filter products with low stock."""
        threshold = value if value is not None else 10
        return queryset.filter(stock__lt=threshold)
    
    def filter_out_of_stock(self, queryset, name, value):
        """Filter products that are out of stock."""
        if value:
            return queryset.filter(stock=0)
        return queryset.filter(stock__gt=0)
    
    def filter_in_stock(self, queryset, name, value):
        """Filter products that are in stock."""
        if value:
            return queryset.filter(stock__gt=0)
        return queryset.filter(stock=0)
    
    class Meta:
        model = Product
        fields = {
            'name': ['exact', 'icontains', 'istartswith', 'iendswith'],
            'description': ['exact', 'icontains'],
            'price': ['exact', 'gte', 'lte', 'gt', 'lt'],
            'stock': ['exact', 'gte', 'lte', 'gt', 'lt'],
        }


class OrderFilter(filters.FilterSet):
    """Filter for Order model."""
    
    total_amount_gte = filters.NumberFilter(
        field_name='total_amount',
        lookup_expr='gte',
        help_text="Filter orders with total amount greater than or equal to"
    )
    
    total_amount_lte = filters.NumberFilter(
        field_name='total_amount',
        lookup_expr='lte',
        help_text="Filter orders with total amount less than or equal to"
    )
    
    order_date_gte = filters.DateFilter(
        field_name='order_date',
        lookup_expr='gte',
        help_text="Filter orders on or after this date"
    )
    
    order_date_lte = filters.DateFilter(
        field_name='order_date',
        lookup_expr='lte',
        help_text="Filter orders on or before this date"
    )
    
    customer_name = filters.CharFilter(
        field_name='customer__name',
        lookup_expr='icontains',
        help_text="Filter orders by customer name (case-insensitive partial match)"
    )
    
    customer_email = filters.CharFilter(
        field_name='customer__email',
        lookup_expr='icontains',
        help_text="Filter orders by customer email (case-insensitive partial match)"
    )
    
    customer_id = filters.UUIDFilter(
        field_name='customer__id',
        help_text="Filter orders by customer ID"
    )
    
    product_name = filters.CharFilter(
        field_name='products__name',
        lookup_expr='icontains',
        help_text="Filter orders by product name (case-insensitive partial match)"
    )
    
    product_id = filters.UUIDFilter(
        field_name='products__id',
        help_text="Filter orders by product ID"
    )
    
    product_ids = filters.BaseInFilter(
        field_name='products__id',
        lookup_expr='in',
        help_text="Filter orders that include any of these product IDs"
    )
    
    status = filters.ChoiceFilter(
        choices=Order.STATUS_CHOICES,
        help_text="Filter orders by status"
    )
    
    status_in = filters.BaseInFilter(
        field_name='status',
        lookup_expr='in',
        help_text="Filter orders with any of these statuses"
    )
    
    has_product = filters.BooleanFilter(
        method='filter_has_product',
        help_text="Filter orders that have at least one product"
    )
    
    min_product_count = filters.NumberFilter(
        method='filter_by_product_count',
        help_text="Filter orders with at least this many products"
    )
    
    max_product_count = filters.NumberFilter(
        method='filter_by_product_count',
        help_text="Filter orders with at most this many products"
    )
    
    created_at_gte = filters.DateFilter(
        field_name='created_at',
        lookup_expr='gte',
        help_text="Filter orders created on or after this date"
    )
    
    created_at_lte = filters.DateFilter(
        field_name='created_at',
        lookup_expr='lte',
        help_text="Filter orders created on or before this date"
    )
    
    def filter_has_product(self, queryset, name, value):
        """Filter orders that have products."""
        if value:
            return queryset.filter(products__isnull=False).distinct()
        return queryset.filter(products__isnull=True).distinct()
    
    def filter_by_product_count(self, queryset, name, value):
        """Filter orders by number of products."""
        if value is not None:
            # Annotate each order with product count
            queryset = queryset.annotate(
                product_count=models.Count('products')
            )
            
            if name == 'min_product_count':
                return queryset.filter(product_count__gte=value)
            elif name == 'max_product_count':
                return queryset.filter(product_count__lte=value)
        
        return queryset
    
    class Meta:
        model = Order
        fields = {
            'total_amount': ['exact', 'gte', 'lte', 'gt', 'lt'],
            'order_date': ['exact', 'gte', 'lte', 'gt', 'lt'],
            'status': ['exact', 'in'],
            'created_at': ['exact', 'gte', 'lte', 'gt', 'lt'],
        }