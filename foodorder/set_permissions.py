import os
import sys
import django

# Apna actual settings module path
sys.path.insert(0, 'D:\\FOOD-ORDERING-SYS\\backend\\foodorder')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'foodorder.settings')
django.setup()

from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from api.models import Restaurant, Food, Category, OrderAddress, Order, Review, FoodTracking

print("Script started...")
print(f"Total restaurants: {Restaurant.objects.count()}")

models_to_allow = [Food, Category, OrderAddress, Order, Review, FoodTracking]

for restaurant in Restaurant.objects.all():
    print(f"Processing: {restaurant.name} | owner: {restaurant.owner}")
    if restaurant.owner:
        user = restaurant.owner
        for model in models_to_allow:
            ct = ContentType.objects.get_for_model(model)
            permissions = Permission.objects.filter(content_type=ct)
            user.user_permissions.add(*permissions)
        print(f"✓ Permissions set for: {restaurant.name} - {user.username}")

print("Done!")