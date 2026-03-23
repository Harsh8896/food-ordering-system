from django.contrib import admin
from django.contrib.auth.models import User as DjangoUser
from .models import *


def create_or_update_owner_user(restaurant):
    username = restaurant.owner_email
    existing_user = DjangoUser.objects.filter(username=username).first()
    if existing_user:
        existing_user.is_staff = True
        existing_user.is_superuser = False
        existing_user.save()
        restaurant.owner = existing_user
    else:
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
    list_display = ('name', 'owner_email', 'location', 'subscription_plan', 'status', 'created_date')
    list_filter = ('status', 'subscription_plan')
    search_fields = ('name', 'owner_email')

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        create_or_update_owner_user(obj)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(owner=request.user)


# ── MasterFood — Super Admin only ──
@admin.register(MasterFood)
class MasterFoodAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'created_date', 'restaurant_count')
    search_fields = ('name', 'category')
    list_filter = ('category',)

    def restaurant_count(self, obj):
        return RestaurantMenuItem.objects.filter(master_food=obj).count()
    restaurant_count.short_description = 'Restaurants'

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.none()

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)

        if not change:  # Sirf naya MasterFood add hone par
            active_restaurants = Restaurant.objects.filter(status='active')
            for restaurant in active_restaurants:
                # Har restaurant ke liye RestaurantMenuItem auto create karo
                menu_item, created = RestaurantMenuItem.objects.get_or_create(
                    restaurant=restaurant,
                    master_food=obj,
                    defaults={
                        'price': 0,       # Restaurant owner baad mein set karega
                        'is_available': False,  # Pehle unavailable — owner enable karega
                        'prep_time': '30-45 mins',
                    }
                )
                # Food bhi auto create karo
                if created:
                    cat, _ = Category.objects.get_or_create(
                        category_name="General",
                        restaurant=restaurant
                    )
                    food, _ = Food.objects.get_or_create(
                        restaurant=restaurant,
                        item_name=obj.name,
                        defaults={
                            'category': cat,
                            'item_price': 0,
                            'item_quantity': '1',
                            'image': obj.image,
                            'is_available': False,
                            'is_master_food': True,
                        }
                    )
                    menu_item.food = food
                    menu_item.save()


# ── RestaurantMenuItem — Restaurant Owner only ──
@admin.register(RestaurantMenuItem)
class RestaurantMenuItemAdmin(admin.ModelAdmin):
    fields = ('master_food', 'price', 'is_available', 'description' , 'prep_time')
    list_display = ('get_food_name', 'restaurant', 'price', 'is_available', 'prep_time')
    list_filter = ('is_available',)

    def get_food_name(self, obj):
        return obj.master_food.name
    get_food_name.short_description = 'Food Item'

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
        if obj.food:
            obj.food.item_price = obj.price
            obj.food.is_available = obj.is_available
            obj.food.save()

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'master_food' and not request.user.is_superuser:
            try:
                restaurant = Restaurant.objects.get(owner=request.user)
                assigned = RestaurantMenuItem.objects.filter(
                    restaurant=restaurant
                ).values_list('master_food_id', flat=True)
                kwargs['queryset'] = MasterFood.objects.filter(id__in=assigned)
            except Restaurant.DoesNotExist:
                kwargs['queryset'] = MasterFood.objects.none()
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    # ✅ Fix — super admin add nahi karega, restaurant owner kar sakta hai
    def has_add_permission(self, request):
        if request.user.is_superuser:
            return False  # Super admin MasterFood se auto add hoga
        # Restaurant owner add kar sakta hai
        try:
            Restaurant.objects.get(owner=request.user)
            return True
        except Restaurant.DoesNotExist:
            return False

    def has_delete_permission(self, request, obj=None):
        if request.user.is_superuser:
            return True
        return False


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


# ── Order Address ──
@admin.register(OrderAddress)
class OrderAddressAdmin(admin.ModelAdmin):
    list_display = ('order_number', 'get_customer', 'order_final_status', 'order_time')
    list_filter = ('order_final_status', 'order_time')
    search_fields = ('order_number', 'user__first_name', 'address')

    def get_customer(self, obj):
        return f"{obj.user.first_name} {obj.user.last_name}"
    get_customer.short_description = 'Customer'

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        try:
            restaurant = Restaurant.objects.get(owner=request.user)
            restaurant_order_numbers = Order.objects.filter(
                food__restaurant=restaurant
            ).values_list('order_number', flat=True).distinct()
            return qs.filter(order_number__in=restaurant_order_numbers)
        except Restaurant.DoesNotExist:
            return qs.none()


# ── Order ──
@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('order_number', 'user', 'food', 'quantity', 'is_order_placed')
    list_filter = ('is_order_placed',)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        try:
            restaurant = Restaurant.objects.get(owner=request.user)
            return qs.filter(food__restaurant=restaurant)
        except Restaurant.DoesNotExist:
            return qs.none()


# ── Food Tracking ──
@admin.register(FoodTracking)
class FoodTrackingAdmin(admin.ModelAdmin):
    list_display = ('get_order_no', 'get_user_name', 'status', 'order_cancelled_by_user', 'status_date')
    list_filter = ('order_cancelled_by_user', 'status', 'status_date')
    search_fields = ('order__order_number', 'order__user__first_name')

    def get_order_no(self, obj):
        return obj.order.order_number if obj.order else 'N/A'
    get_order_no.short_description = 'Order Number'

    def get_user_name(self, obj):
        if obj.order and obj.order.user:
            return f"{obj.order.user.first_name} {obj.order.user.last_name}"
        return 'Unknown'
    get_user_name.short_description = 'Customer Name'

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        try:
            restaurant = Restaurant.objects.get(owner=request.user)
            return qs.filter(order__food__restaurant=restaurant)
        except Restaurant.DoesNotExist:
            return qs.none()


# ── User ──
@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('id', 'first_name', 'last_name', 'email', 'mobile', 'reg_date')
    search_fields = ('email', 'first_name', 'mobile')

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.none()


# ── Reviews ──
@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('food', 'user', 'rating', 'created_at')
    list_filter = ('rating', 'created_at')

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        try:
            restaurant = Restaurant.objects.get(owner=request.user)
            return qs.filter(food__restaurant=restaurant)
        except Restaurant.DoesNotExist:
            return qs.none()


# ── Payment ──
@admin.register(PaymentDetail)
class PaymentDetailAdmin(admin.ModelAdmin):
    list_display = ('order_number', 'user', 'payment_mode', 'payment_date')
    list_filter = ('payment_mode',)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.none()


# ── Platform Settings ──
@admin.register(PlatformSettings)
class PlatformSettingsAdmin(admin.ModelAdmin):
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.none()


admin.site.register(Wishlist)