from django.contrib import admin
from django.contrib.auth.models import User as DjangoUser
from django import forms
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


# ── MasterFood ke liye custom form ──
class MasterFoodAdminForm(forms.ModelForm):
    # Restaurants — checkboxes (sirf active & non-discarded)
    restaurants = forms.ModelMultipleChoiceField(
        queryset=Restaurant.objects.filter(status='active', is_discarded=False),
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label="Restaurants select karo (jinke liye yeh item hoga)",
        help_text="Naye restaurants add karne ke liye check karo. Pehle se linked change nahi honge.",
    )
    price = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        required=False,
        initial=0,
        label="Price (₹)",
        help_text="Sabhi selected restaurants ke liye same price lagega",
    )
    prep_time = forms.CharField(
        max_length=50,
        required=False,
        initial="30-45 mins",
        label="Prep Time",
    )

    class Meta:
        model = MasterFood
        fields = ['name', 'description', 'image', 'category']


@admin.register(MasterFood)
class MasterFoodAdmin(admin.ModelAdmin):
    form = MasterFoodAdminForm
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

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        if obj is not None:
            # Sirf jo RestaurantMenuItem exist karta hai unhe pre-checked dikhao
            # Baaki restaurants unchecked dikhenge — admin unhe future mein add kar sakta hai
            linked_ids = RestaurantMenuItem.objects.filter(
                master_food=obj
            ).values_list('restaurant_id', flat=True)
            form.base_fields['restaurants'].initial = list(linked_ids)
            # Queryset — saare active restaurants dikhao (linked + unlinked dono)
            form.base_fields['restaurants'].queryset = Restaurant.objects.filter(
                status='active', is_discarded=False
            )
        return form

    def save_model(self, request, obj, form, change):
        # Step 1: MasterFood save karo (Cloudinary upload bhi yahan hoti hai)
        super().save_model(request, obj, form, change)

        selected_restaurants = list(form.cleaned_data.get('restaurants', []))
        price     = form.cleaned_data.get('price') or 0
        prep_time = form.cleaned_data.get('prep_time') or '30-45 mins'

        selected_ids = [r.id for r in selected_restaurants]

        # ✅ Step 2: Jo restaurants UNCHECK hain unka RestaurantMenuItem delete karo
        # Food delete mat karo — restaurant ka apna item safe rahega
        # Admin pe restaurant tab bhi dikhega (RestaurantMenuItem na ho tab bhi checkbox dikhta hai)
        RestaurantMenuItem.objects.filter(
            master_food=obj
        ).exclude(restaurant_id__in=selected_ids).delete()

        # ✅ Step 3: Selected restaurants ke liye MenuItem + Food banao ya recreate karo
        for restaurant in selected_restaurants:
            cat, _ = Category.objects.get_or_create(
                category_name="General",
                restaurant=restaurant,
            )

            # Food get/create — agar pehle se hai to reuse karo
            food, food_created = Food.objects.get_or_create(
                restaurant=restaurant,
                item_name=obj.name,
                defaults={
                    'category': cat,
                    'item_price': price,
                    'item_quantity': '1',
                    'image': obj.image,
                    'is_available': True,
                    'is_master_food': True,
                }
            )
            # Agar food pehle se tha aur disabled tha — enable karo
            if not food_created and not food.is_available:
                food.is_available = True
                food.save()

            # RestaurantMenuItem get/create
            menu_item, created = RestaurantMenuItem.objects.get_or_create(
                restaurant=restaurant,
                master_food=obj,
                defaults={
                    'price': price,
                    'is_available': True,
                    'prep_time': prep_time,
                    'food': food,
                }
            )

            # Pehle se tha — food link karo agar missing hai
            if not created and menu_item.food is None:
                menu_item.food = food
                menu_item.save(update_fields=['food'])


@admin.register(RestaurantMenuItem)
class RestaurantMenuItemAdmin(admin.ModelAdmin):
    fields = ('master_food', 'price', 'is_available', 'description', 'prep_time')
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

    def has_add_permission(self, request):
        if request.user.is_superuser:
            return False
        try:
            Restaurant.objects.get(owner=request.user)
            return True
        except Restaurant.DoesNotExist:
            return False

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser


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


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('id', 'first_name', 'last_name', 'email', 'mobile', 'reg_date')
    search_fields = ('email', 'first_name', 'mobile')

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.none()


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


@admin.register(PaymentDetail)
class PaymentDetailAdmin(admin.ModelAdmin):
    list_display = ('order_number', 'user', 'payment_mode', 'payment_date')
    list_filter = ('payment_mode',)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.none()


@admin.register(PlatformSettings)
class PlatformSettingsAdmin(admin.ModelAdmin):
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.none()


admin.site.register(Wishlist)