from django.db import models

# Create your models here.

class User(models.Model):
    first_name = models.CharField(max_length=50, null=True)
    last_name = models.CharField(max_length=50, null=True)
    email = models.EmailField(max_length=50, null=True, unique=True)
    mobile = models.CharField(max_length=15, )
    password = models.CharField(max_length=50)
    reg_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name}"
    

class Category(models.Model):
    restaurant = models.ForeignKey('Restaurant', on_delete=models.CASCADE, null=True, blank=True)
    category_name = models.CharField(max_length=50, null=True)
    creation_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.category_name
    

class Food(models.Model):
    restaurant = models.ForeignKey('Restaurant', on_delete=models.CASCADE, null=True, blank=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    item_name = models.CharField(max_length=50)
    item_price = models.DecimalField(max_digits=10, decimal_places=2)
    item_description = models.TextField(max_length=500, null=True, blank=False)
    image = models.ImageField(upload_to="food_images/")
    item_quantity = models.CharField(max_length=50)
    is_available = models.BooleanField(default=True)
    reg_gdate = models.DateTimeField(auto_now_add=True)
    # ✅ Naya field — MasterFood se linked hai ya nahi
    is_master_food = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.item_name} {self.item_price}"
    



class Order(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    food = models.ForeignKey(Food, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    is_order_placed = models.BooleanField(default=False)
    order_number = models.CharField(max_length=100, null=True)

    def __str__(self):
        return f"{self.order_number} {self.user}"
    


class OrderAddress(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    restaurant = models.ForeignKey('Restaurant', on_delete=models.SET_NULL, null=True, blank=True)
    order_number = models.CharField(max_length=100, null=True)
    address = models.TextField()
    order_time = models.DateTimeField(auto_now_add=True)
    order_final_status = models.CharField(max_length=200, null=True)

    def __str__(self):
        return f"{self.order_number} - {self.user}"
    

class FoodTracking(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    remark = models.CharField(max_length=200, null=True)
    status = models.TextField(max_length=200, null=True)
    status_date = models.DateTimeField(auto_now_add=True)
    order_cancelled_by_user = models.BooleanField(null=True)

    def __str__(self):
        return f"{self.order} {self.status}"
    


class PaymentDetail(models.Model):

    PAYMENT_CHOICE = [
        ("cod", "Cash on Delivery"),
        ("online", "Online Payment")
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    order_number = models.CharField(max_length=200, null=True)
    payment_mode = models.CharField(max_length=20, choices=PAYMENT_CHOICE)
    card_number = models.CharField(max_length=20, null=True, blank=True)
    expiry_date = models.CharField(max_length=10, null=True, blank=True)
    cvv = models.CharField(max_length=5,null=True, blank=True)
    payment_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.order_number} - {self.payment_mode}"
    

    
class Review(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    food = models.ForeignKey(Food, on_delete=models.CASCADE)
    rating = models.PositiveIntegerField(default=1)
    comment = models.TextField(null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Review by {self.user.first_name} for {self.food.item_name} - {self.rating} stars"
    


class Wishlist(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    food = models.ForeignKey(Food, on_delete=models.CASCADE)
    added_on = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "food")

    def __str__(self):
        return f"{self.user.first_name} for {self.food.item_name} - {self.rating} stars"
    

from django.contrib.auth.models import User as DjangoUser

class Restaurant(models.Model):
    PLAN_CHOICES = [
        ('Basic', 'Basic'),
        ('Standard', 'Standard'),
        ('Premium', 'Premium'),
    ]
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('suspended', 'Suspended'),
    ]
    owner = models.OneToOneField(DjangoUser, on_delete=models.SET_NULL, null=True, blank=True)  # ← ye add karo
    name = models.CharField(max_length=100)
    owner_email = models.EmailField(unique=True)
    owner_password = models.CharField(max_length=200)
    location = models.CharField(max_length=200)
    subscription_plan = models.CharField(max_length=20, choices=PLAN_CHOICES, default='Standard')
    subscription_expiry = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    created_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name
    

class PlatformSettings(models.Model):
    brand_name = models.CharField(max_length=100, default='FoodSys')
    brand_logo_url = models.URLField(blank=True)
    platform_currency = models.CharField(max_length=10, default='INR')
    currency_symbol = models.CharField(max_length=5, default='₹')
    support_email = models.EmailField(default='support@foodsys.com')
    support_phone = models.CharField(max_length=20, default='+91-XXXXXXXXXX')
    platform_timezone = models.CharField(max_length=50, default='Asia/Kolkata')
    maintenance_mode = models.BooleanField(default=False)
    enable_restaurant_registration = models.BooleanField(default=True)
    max_restaurants = models.IntegerField(default=500)

    def __str__(self):
        return self.brand_name
    

class MasterFood(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(null=True, blank=True)
    image = models.ImageField(upload_to='master_foods/')
    category = models.CharField(max_length=100)
    created_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class RestaurantMenuItem(models.Model):
    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE)
    master_food = models.ForeignKey(MasterFood, on_delete=models.CASCADE)
    food = models.ForeignKey(Food, on_delete=models.SET_NULL, null=True, blank=True)  # ← add
    price = models.DecimalField(max_digits=10, decimal_places=2)
    is_available = models.BooleanField(default=True)
    prep_time = models.CharField(max_length=50, null=True, blank=True)
    description = models.TextField(null=True, blank=True)

    class Meta:
        unique_together = ('restaurant', 'master_food')

    def __str__(self):
        return f"{self.restaurant.name} - {self.master_food.name}"