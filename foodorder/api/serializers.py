from rest_framework import serializers
from .models import *

class CategorySerializers(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = "__all__"

class FoodSerializers(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.category_name', read_only=True)
    restaurant_name = serializers.CharField(source='restaurant.name', read_only=True)  # ← add
    restaurant_location = serializers.CharField(source='restaurant.location', read_only=True)
    image = serializers.ImageField(required=False)
    is_available = serializers.BooleanField(default=True)

    class Meta:
        model = Food
        fields = [
            'id', 'category', 'category_name',
            'restaurant', 'restaurant_name', 'restaurant_location',   # ← add
            'item_name', 'item_price', 'item_description',
            'image', 'item_quantity', 'is_available'
        ]



class CartOrderSerializers(serializers.ModelSerializer):
    food = FoodSerializers()
    class Meta:
        model = Order
        fields = ["id", "food", "quantity"]


class MyOrdersListSerializer(serializers.ModelSerializer):
    order_final_status = serializers.SerializerMethodField()
    class Meta:
        model = OrderAddress
        fields = ["order_number", "order_time", "order_final_status"]

    def get_order_final_status(self, obj):
        return obj.order_final_status or "Waiting for restaurant confirmation"
    


class OrderSerializer(serializers.ModelSerializer):
    food = FoodSerializers()

    class Meta:
        model = Order
        fields = ['food', 'quantity']



class OrderAddressSerializer(serializers.ModelSerializer):
    payment_mode = serializers.SerializerMethodField()

    class Meta:
        model = OrderAddress
        fields = ['order_number', 'address', 'order_time', 'order_final_status', 'payment_mode']

    def get_payment_mode(self, obj):
        try:
            payment = PaymentDetail.objects.get(order_number=obj.order_number)
            return payment.payment_mode
        except PaymentDetail.DoesNotExist:
            return None
        
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'first_name', 'last_name', 'email', 'mobile', 'reg_date']



class OrderSummarySerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderAddress
        fields = ['id', 'order_number', 'order_time']


class OrderDetailSerializer(serializers.ModelSerializer):
    user_first_name = serializers.CharField(source='user.first_name')
    user_last_name = serializers.CharField(source='user.last_name')
    user_email = serializers.CharField(source='user.email')
    user_mobile = serializers.CharField(source='user.mobile')

    class Meta:
        model = OrderAddress
        fields = ['order_number', 'order_time', 'order_final_status', 'address', 'user_first_name', 'user_last_name', 'user_email', 'user_mobile']

class OrderedFoodSerializers(serializers.ModelSerializer):
    item_name = serializers.CharField(source='food.item_name')
    item_price = serializers.CharField(source='food.item_price')
    image = serializers.ImageField(source='food.image') # Video mein CharField se ImageField kiya gaya

    class Meta:
        model = Order
        fields = ['item_name', 'item_price', 'image']

class FoodTrackingSerializer(serializers.ModelSerializer):
    class Meta:
        model = FoodTracking
        fields = ['remark', 'status', 'status_date', 'order_cancelled_by_user']


class ReviewSerializer(serializers.ModelSerializer):
    user_name = serializers.SerializerMethodField()
    food_name = serializers.CharField(source='food.item_name', read_only=True)

    class Meta:
        model = Review
        fields = ['id', 'user', 'user_name', 'food', 'food_name', 'rating', 'comment', 'created_at']

    def get_user_name(self, obj):
        return f"{obj.user.first_name} {obj.user.last_name}"
    
class OrderDeliveredSerializer(serializers.ModelSerializer):
    # Foreign Key ke zariye user ka naam uthana
    user_name = serializers.CharField(source='user.first_name', read_only=True)
    
    # Foreign Key ke zariye food ka naam aur price uthana
    # (Dhyan rahe: Ye tabhi kaam karega agar serializer ka 'model' Order hai)
    food_name = serializers.CharField(source='food.item_name', read_only=True)
    price = serializers.DecimalField(source='food.item_price', max_digits=10, decimal_places=2, read_only=True)

    class Meta:
        model = Order  # Humne yahan OrderAddress ki jagah Order model use kiya hai
        fields = ['order_number', 'user_name', 'food_name', 'price']


class RestaurantSerializer(serializers.ModelSerializer):
    days_left = serializers.SerializerMethodField()

    class Meta:
        model = Restaurant
        fields = '__all__'

    def get_days_left(self, obj):
        from datetime import date
        return (obj.subscription_expiry - date.today()).days

