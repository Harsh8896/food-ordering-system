from django.contrib import admin
from django.contrib.auth.models import User as DjangoUser
from .models import (
    User, Category, Food, Order,
    OrderAddress, FoodTracking, PaymentDetail,
    Review, Wishlist, Restaurant, PlatformSettings
)


# ── Jab Restaurant save ho, automatically Django staff user bane ──
def create_or_update_owner_user(restaurant):
    username = restaurant.owner_email
    existing_user = DjangoUser.objects.filter(username=username).first()

    if existing_user:
        # Already hai toh update karo
        existing_user.is_staff = True
        existing_user.is_superuser = False
        existing_user.save()
        restaurant.owner = existing_user
    else:
        # Naya user banao
        new_user = DjangoUser.objects.create_user(
            username=username,
            email=restaurant.owner_email,
            password=restaurant.owner_password,
            is_staff=True,
            is_superuser=False,
        )
        restaurant.owner = new_user
    restaurant.save()


# ── Restaurant ──
@admin.register(Restaurant)
class RestaurantAdmin(admin.ModelAdmin):
    list_display = ('name', 'owner_email', 'subscription_plan', 'status', 'created_date')
    list_filter = ('status', 'subscription_plan')
    search_fields = ('name', 'owner_email')

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        create_or_update_owner_user(obj)

    # Staff owner restaurants list mein sirf apna dekhe
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(owner=request.user)


# ── Food ──
@admin.register(Food)
class FoodAdmin(admin.ModelAdmin):
    list_display = ('item_name', 'get_restaurant', 'category', 'item_price', 'is_available')
    list_filter = ('is_available', 'category')
    search_fields = ('item_name',)

    def get_restaurant(self, obj):
        return obj.restaurant.name if obj.restaurant else 'N/A'
    get_restaurant.short_description = 'Restaurant'

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        try:
            restaurant = Restaurant.objects.get(owner=request.user)
            return qs.filter(restaurant=restaurant)
        except Restaurant.DoesNotExist:
            return qs.none()

    def save_model(self, request, obj, form, change):
        if not request.user.is_superuser:
            try:
                restaurant = Restaurant.objects.get(owner=request.user)
                obj.restaurant = restaurant
            except Restaurant.DoesNotExist:
                pass
        super().save_model(request, obj, form, change)

    # Owner sirf apni categories dekhe dropdown mein
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'category' and not request.user.is_superuser:
            try:
                restaurant = Restaurant.objects.get(owner=request.user)
                kwargs['queryset'] = Category.objects.filter(restaurant=restaurant)
            except Restaurant.DoesNotExist:
                kwargs['queryset'] = Category.objects.none()
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


# ── Category ──
@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('category_name', 'get_restaurant', 'creation_date')
    search_fields = ('category_name',)

    def get_restaurant(self, obj):
        return obj.restaurant.name if obj.restaurant else 'N/A'
    get_restaurant.short_description = 'Restaurant'

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        try:
            restaurant = Restaurant.objects.get(owner=request.user)
            return qs.filter(restaurant=restaurant)
        except Restaurant.DoesNotExist:
            return qs.none()

    def save_model(self, request, obj, form, change):
        if not request.user.is_superuser:
            try:
                restaurant = Restaurant.objects.get(owner=request.user)
                obj.restaurant = restaurant
            except Restaurant.DoesNotExist:
                pass
        super().save_model(request, obj, form, change)


# ── Orders ──
@admin.register(OrderAddress)
class OrderAddressAdmin(admin.ModelAdmin):
    list_display = ('order_number', 'get_customer', 'order_final_status', 'order_time')
    list_filter = ('order_final_status', 'order_time')
    search_fields = ('order_number',)

    def get_customer(self, obj):
        return f"{obj.user.first_name} {obj.user.last_name}"
    get_customer.short_description = 'Customer'

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        try:
            restaurant = Restaurant.objects.get(owner=request.user)
            order_nums = Order.objects.filter(
                food__restaurant=restaurant
            ).values_list('order_number', flat=True).distinct()
            return qs.filter(order_number__in=order_nums)
        except Restaurant.DoesNotExist:
            return qs.none()

# ── Reviews ──
@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('food', 'user', 'rating', 'created_at')
    list_filter = ('rating',)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        try:
            restaurant = Restaurant.objects.get(owner=request.user)
            return qs.filter(food__restaurant=restaurant)
        except Restaurant.DoesNotExist:
            return qs.none()


# ── FoodTracking ──
@admin.register(FoodTracking)
class FoodTrackingAdmin(admin.ModelAdmin):
    list_display = ('get_order_no', 'get_user_name', 'status', 'status_date')
    search_fields = ('order__order_number',)

    def get_order_no(self, obj):
        return obj.order.order_number if obj.order else 'N/A'
    get_order_no.short_description = 'Order Number'

    def get_user_name(self, obj):
        if obj.order and obj.order.user:
            return f"{obj.order.user.first_name} {obj.user.last_name}"
        return 'Unknown'
    get_user_name.short_description = 'Customer'

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        try:
            restaurant = Restaurant.objects.get(owner=request.user)
            return qs.filter(order__food__restaurant=restaurant)
        except Restaurant.DoesNotExist:
            return qs.none()


# ── Super Admin only ──
@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('id', 'first_name', 'last_name', 'email', 'mobile', 'reg_date')
    search_fields = ('email', 'first_name', 'mobile')

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.none()


@admin.register(PaymentDetail)
class PaymentDetailAdmin(admin.ModelAdmin):
    list_display = ('order_number', 'user', 'payment_mode', 'payment_date')

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.none()


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('order_number', 'user', 'food', 'quantity', 'is_order_placed')

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        try:
            restaurant = Restaurant.objects.get(owner=request.user)
            return qs.filter(food__restaurant=restaurant)
        except Restaurant.DoesNotExist:
            return qs.none()


admin.site.register(Wishlist)
admin.site.register(PlatformSettings)
