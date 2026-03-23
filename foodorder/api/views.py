from urllib import response
from django.shortcuts import render
from rest_framework.decorators import api_view, parser_classes
from django.contrib.auth import authenticate
from rest_framework.response import Response
from .models import * 
from .serializers import * 
from rest_framework.parsers import FormParser, MultiPartParser
from django.shortcuts import render
from django.utils.timezone import now, timedelta, make_aware
from datetime import datetime
from django.db.models import Sum, F, DecimalField, Count, Avg
from decimal import Decimal
from collections import defaultdict
from django.db.models.functions import TruncMonth, Coalesce, TruncWeek


# ── Helper: Restaurant ke order numbers nikalna ──
def get_restaurant_order_numbers(restaurant_id):
    # 'null' string ya None dono handle karo
    if not restaurant_id or restaurant_id == 'null':
        return Order.objects.none().values_list('order_number', flat=True)
    return Order.objects.filter(
        food__restaurant_id=restaurant_id
    ).values_list('order_number', flat=True).distinct()


@api_view(["POST"])
def admin_login_api(request):
    username = request.data.get("username")
    password = request.data.get("password")

    user = authenticate(username=username, password=password)

    if user is not None and user.is_staff and not user.is_superuser:
        try:
            restaurant = Restaurant.objects.get(owner=user)
            return Response({
                "message": "Login Successful",
                "username": username,
                "restaurant_id": restaurant.id,
                "restaurant_name": restaurant.name,
            }, status=200)
        except Restaurant.DoesNotExist:
            return Response({"message": "No restaurant linked to this account"}, status=401)
    return Response({"message": "Invalid Credentials"}, status=401)


@api_view(["POST"])
def add_category(request):
    category_name = request.data.get("category_name")
    restaurant_id = request.data.get("restaurant")
    Category.objects.create(
        category_name=category_name,
        restaurant_id=restaurant_id
    )
    return Response({"message": "Category has been created"}, status=201)


@api_view(["GET"])
def list_categories(request):
    restaurant_id = request.GET.get('restaurant_id')
    if restaurant_id:
        categories = Category.objects.filter(restaurant_id=restaurant_id)
    else:
        categories = Category.objects.all()
    serializer = CategorySerializers(categories, many=True)
    return Response(serializer.data)


@api_view(["Post"])
@parser_classes([MultiPartParser, FormParser])
def add_food_item(request):
    serializer = FoodSerializers(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response({"message": "Food item has been added"}, status=201)
    return Response({"message": "Something went wrong"}, status=400)


@api_view(["GET"])
def list_foods(request):
    restaurant_id = request.GET.get('restaurant_id')
    if restaurant_id:
        foods = Food.objects.filter(restaurant_id=restaurant_id)
    else:
        foods = Food.objects.all()
    serializer = FoodSerializers(foods, many=True)
    return Response(serializer.data)


@api_view(["GET"])
def food_search(request):
    query = request.GET.get("q", "")
    foods = Food.objects.filter(item_name__icontains=query)
    serializer = FoodSerializers(foods, many=True)
    return Response(serializer.data)


import random
@api_view(["GET"])
def random_foods(request):
    foods = list(Food.objects.all())
    random.shuffle(foods)
    limited_foods = foods[0:9]
    serializer = FoodSerializers(limited_foods, many=True)
    return Response(serializer.data)


from django.contrib.auth.hashers import make_password
@api_view(["POST"])
def register_user(request):
    first_name = request.data.get("firstname")
    last_name = request.data.get("lastname")
    email = request.data.get("email")
    mobile = request.data.get("mobile")
    password = request.data.get("password")

    if User.objects.filter(email=email).exists() or User.objects.filter(mobile=mobile).exists():
        return Response({"message": "Email and mobile no already registered"}, status=400)
    User.objects.create(
        first_name=first_name, last_name=last_name,
        email=email, mobile=mobile, password=make_password(password)
    )
    return Response({"message": "User registered successfully"}, status=201)


from django.db.models import Q
from django.contrib.auth.hashers import check_password
@api_view(["POST"])
def login_user(request):
    email = request.data.get("email")
    password = request.data.get("password")

    try:
        user = User.objects.get(Q(email=email) | Q(mobile=email))
        if check_password(password, user.password):
            return Response({
                "message": "Login Successful",
                "userId": user.id,
                "userName": f"{user.first_name} {user.last_name}"
            }, status=200)
        else:
            return Response({"message": "Invalid Credentials"}, status=401)
    except:
        return Response({"message": "Invalid Credentials"}, status=401)


from django.shortcuts import get_object_or_404
@api_view(["GET"])
def food_detail(request, id):
    food = get_object_or_404(Food, id=id)
    serializer = FoodSerializers(food)
    return Response(serializer.data)


@api_view(["POST"])
def add_to_cart(request):
    user_id = request.data.get("userId")
    food_id = request.data.get("foodId")

    try:
        user = User.objects.get(id=user_id)
        food = Food.objects.get(id=food_id)

        order, created = Order.objects.get_or_create(
            user=user, food=food, is_order_placed=False,
            defaults={"quantity": 1}
        )
        if not created:
            order.quantity += 1
            order.save()

        return Response({"message": "Food added to cart successfully"}, status=200)
    except Exception as e:
        return Response({"message": str(e)}, status=400)


@api_view(["GET"])
def add_cart_item(request, user_id):
    orders = Order.objects.filter(user_id=user_id, is_order_placed=False).select_related()
    serializer = CartOrderSerializers(orders, many=True)
    return Response(serializer.data)


@api_view(["PUT"])
def update_cart_quantity(request):
    order_id = request.data.get("orderId")
    quantity = request.data.get("quantity")

    try:
        order = Order.objects.get(id=order_id, is_order_placed=False)
        order.quantity = quantity
        order.save()
        return Response({"message": "quantity updated successfully"}, status=200)
    except:
        return Response({"message": "Something went wrong"}, status=404)


@api_view(["DELETE"])
def delete_cart_item(request, order_id):
    try:
        order = Order.objects.get(id=order_id, is_order_placed=False)
        order.delete()
        return Response({"message": "Item deleted from cart"}, status=200)
    except:
        return Response({"message": "Something went wrong"}, status=404)


def make_unique_order_number():
    while True:
        num = str(random.randint(100000000, 999999999))
        if not OrderAddress.objects.filter(order_number=num).exists():
            return num


@api_view(['POST'])
def place_order(request):
    user_id = request.data.get('userId')
    address = request.data.get('address')
    payment_mode = request.data.get('paymentMode')
    card_number = request.data.get('cardNumber')
    expiry = request.data.get('expiry')
    cvv = request.data.get('cvv')

    try:
        order = Order.objects.filter(user_id=user_id, is_order_placed=False)
        order_number = make_unique_order_number()
        order.update(order_number=order_number, is_order_placed=True)

        OrderAddress.objects.create(
            user_id=user_id, order_number=order_number, address=address
        )
        PaymentDetail.objects.create(
            user_id=user_id, order_number=order_number,
            payment_mode=payment_mode,
            card_number=card_number if payment_mode == 'online' else None,
            expiry_date=expiry if payment_mode == 'online' else None,
            cvv=cvv if payment_mode == 'online' else None,
        )
        return Response({"message": f"Order Placed successfully! Order No {order_number}"}, status=200)
    except:
        return Response({"message": "Something went wrong"}, status=404)


@api_view(['GET'])
def user_orders(request, user_id):
    orders = OrderAddress.objects.filter(user_id=user_id).order_by('-id')
    serializer = MyOrdersListSerializer(orders, many=True)
    return Response(serializer.data)


@api_view(['GET'])
def order_by_order_number(request, order_number):
    orders = Order.objects.filter(order_number=order_number, is_order_placed=True).select_related('food')
    serializer = OrderSerializer(orders, many=True)
    return Response(serializer.data)


@api_view(['GET'])
def get_order_address(request, order_number):
    address = OrderAddress.objects.get(order_number=order_number)
    serializer = OrderAddressSerializer(address)
    return Response(serializer.data)


def get_invoice(request, order_number):
    orders = Order.objects.filter(order_number=order_number, is_order_placed=True).select_related('food')
    address = OrderAddress.objects.get(order_number=order_number)
    grand_total = 0
    order_data = []
    for order in orders:
        total_price = order.food.item_price * order.quantity
        grand_total += total_price
        order_data.append({'food': order.food, 'quantity': order.quantity, 'total_price': total_price})
    context = {'order_number': order_number, 'orders': order_data, 'address': address, 'grand_total': grand_total}
    return render(request, 'invoice.html', context)


@api_view(['GET'])
def get_user_profile(request, user_id):
    user = User.objects.get(id=user_id)
    serializer = UserSerializer(user)
    return Response(serializer.data)


@api_view(['PUT'])
def update_user_profile(request, user_id):
    user = User.objects.get(id=user_id)
    serializer = UserSerializer(user, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        return Response({"message": "Profile updated successfully!"}, status=200)
    return Response(serializer.errors, status=400)


from django.contrib.auth.hashers import make_password, check_password
@api_view(['POST'])
def change_password(request, user_id):
    current_password = request.data.get('current_password')
    new_password = request.data.get('new_password')
    try:
        user = User.objects.get(id=user_id)
        if not check_password(current_password, user.password):
            return Response({"message": "Current password is incorrect"}, status=400)
        user.password = make_password(new_password)
        user.save()
        return Response({"message": "Password changed successfully!"}, status=200)
    except User.DoesNotExist:
        return Response({"message": "User not found"}, status=404)


@api_view(['GET'])
def orders_not_confirmed(request):
    restaurant_id = request.GET.get('restaurant_id')
    if restaurant_id:
        order_nums = get_restaurant_order_numbers(restaurant_id)
        orders = OrderAddress.objects.filter(
            order_final_status__isnull=True,
            order_number__in=order_nums
        ).order_by('-order_time')
    else:
        orders = OrderAddress.objects.filter(
            order_final_status__isnull=True
        ).order_by('-order_time')
    serializer = OrderSummarySerializer(orders, many=True)
    return Response(serializer.data)


@api_view(['GET'])
def orders_confirmed(request):
    restaurant_id = request.GET.get('restaurant_id')
    if restaurant_id:
        order_nums = get_restaurant_order_numbers(restaurant_id)
        orders = OrderAddress.objects.filter(
            order_final_status="Order Confirmed",
            order_number__in=order_nums
        ).order_by('-order_time')
    else:
        orders = OrderAddress.objects.filter(
            order_final_status="Order Confirmed"
        ).order_by('-order_time')
    serializer = OrderSummarySerializer(orders, many=True)
    return Response(serializer.data)


@api_view(['GET'])
def being_prepared(request):
    restaurant_id = request.GET.get('restaurant_id')
    if restaurant_id:
        order_nums = get_restaurant_order_numbers(restaurant_id)
        orders = OrderAddress.objects.filter(
            order_final_status="Food being Prepared",
            order_number__in=order_nums
        ).order_by('-order_time')
    else:
        orders = OrderAddress.objects.filter(
            order_final_status="Food being Prepared"
        ).order_by('-order_time')
    serializer = OrderSummarySerializer(orders, many=True)
    return Response(serializer.data)


@api_view(['GET'])
def food_pickup(request):
    restaurant_id = request.GET.get('restaurant_id')
    if restaurant_id:
        order_nums = get_restaurant_order_numbers(restaurant_id)
        orders = OrderAddress.objects.filter(
            order_final_status="Food Pickup",
            order_number__in=order_nums
        ).order_by('-order_time')
    else:
        orders = OrderAddress.objects.filter(
            order_final_status="Food Pickup"
        ).order_by('-order_time')
    serializer = OrderSummarySerializer(orders, many=True)
    return Response(serializer.data)


@api_view(['GET'])
def order_cancelled(request):
    restaurant_id = request.GET.get('restaurant_id')
    if restaurant_id:
        order_nums = get_restaurant_order_numbers(restaurant_id)
        orders = OrderAddress.objects.filter(
            order_final_status="Order Cancelled",
            order_number__in=order_nums
        ).order_by('-order_time')
    else:
        orders = OrderAddress.objects.filter(
            order_final_status="Order Cancelled"
        ).order_by('-order_time')
    serializer = OrderSummarySerializer(orders, many=True)
    return Response(serializer.data)


@api_view(['GET'])
def all_orders(request):
    restaurant_id = request.GET.get('restaurant_id')
    if restaurant_id:
        order_nums = get_restaurant_order_numbers(restaurant_id)
        orders = OrderAddress.objects.filter(
            order_number__in=order_nums
        ).order_by('-order_time')
    else:
        orders = OrderAddress.objects.all().order_by('-order_time')
    serializer = OrderSummarySerializer(orders, many=True)
    return Response(serializer.data)


@api_view(['POST'])
def order_between_dates(request):
    from_date = request.data.get('from_date')
    to_date = request.data.get('to_date')
    status = request.data.get('status')
    restaurant_id = request.data.get('restaurant_id')

    orders = OrderAddress.objects.filter(order_time__date__range=[from_date, to_date])

    if restaurant_id:
        order_nums = get_restaurant_order_numbers(restaurant_id)
        orders = orders.filter(order_number__in=order_nums)

    if status != 'all':
        if status == 'not_confirmed':
            orders = orders.filter(order_final_status__isnull=True)
        else:
            orders = orders.filter(order_final_status=status)

    serializer = OrderSummarySerializer(orders.order_by('-order_time'), many=True)
    return Response(serializer.data, status=200)


@api_view(['GET'])
def view_order_detail(request, order_number):
    try:
        order_address = OrderAddress.objects.select_related('user').get(order_number=order_number)
        ordered_foods = Order.objects.filter(order_number=order_number).select_related('food')
        tracking = FoodTracking.objects.filter(order__order_number=order_number)
    except OrderAddress.DoesNotExist:
        return Response({'error': 'Order not found'}, status=404)
    except Exception as e:
        return Response({'error': str(e)}, status=404)

    return Response({
        'order': OrderDetailSerializer(order_address).data,
        'foods': OrderedFoodSerializers(ordered_foods, many=True).data,
        'tracking': FoodTrackingSerializer(tracking, many=True).data,
    })


@api_view(['POST'])
def update_order_status(request):
    order_number = request.data.get('order_number')
    new_status = request.data.get('status')
    remark = request.data.get('remark')

    try:
        address = OrderAddress.objects.get(order_number=order_number)
        order = Order.objects.filter(order_number=order_number).first()

        if not order:
            return Response({'error': 'Order not found'}, status=404)

        FoodTracking.objects.create(
            order=order, remark=remark,
            status=new_status, order_cancelled_by_user=False
        )
        address.order_final_status = new_status
        address.save()

        return Response({'message': 'Order status updated successfully'}, status=200)
    except OrderAddress.DoesNotExist:
        return Response({'error': 'Invalid order number'}, status=404)
    except Exception as e:
        return Response({'error': str(e)}, status=400)


@api_view(['GET'])
def search_orders(request):
    query = request.GET.get('q', '')
    restaurant_id = request.GET.get('restaurant_id')

    if query:
        orders = OrderAddress.objects.filter(
            order_number__icontains=query
        ).order_by('-order_time')
        if restaurant_id:
            order_nums = get_restaurant_order_numbers(restaurant_id)
            orders = orders.filter(order_number__in=order_nums)
    else:
        orders = []

    serializer = OrderSummarySerializer(orders, many=True)
    return Response(serializer.data)


@api_view(['GET', 'PUT', 'DELETE'])
def category_detail(request, id):
    try:
        category = Category.objects.get(id=id)
    except Category.DoesNotExist:
        return Response({'error': 'Category Not Found'}, status=404)

    if request.method == 'GET':
        serializer = CategorySerializers(category)
        return Response(serializer.data)
    elif request.method == 'PUT':
        serializer = CategorySerializers(category, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({'message': 'Category updated successfully'}, status=200)
        return Response(serializer.errors, status=400)
    elif request.method == 'DELETE':
        category.delete()
        return Response({'message': 'Category deleted successfully'}, status=200)


@api_view(['DELETE'])
def delete_food(request, id):
    try:
        food = Food.objects.get(id=id)
        food.delete()
        return Response({'message': 'Food deleted successfully'}, status=200)
    except Food.DoesNotExist:
        return Response({'error': 'Food item NOT found'}, status=404)


@api_view(['GET', 'PUT'])
@parser_classes([MultiPartParser, FormParser])
def edit_food(request, id):
    try:
        food = Food.objects.get(id=id)
    except Food.DoesNotExist:
        return Response({'error': 'Food item Not Found'}, status=404)

    if request.method == 'GET':
        serializer = FoodSerializers(food)
        return Response(serializer.data)
    elif request.method == 'PUT':
        data = request.data.copy()
        if 'image' not in request.FILES:
            data['image'] = food.image
        if 'is_available' in data:
            data['is_available'] = data['is_available'].lower() == 'true'
        serializer = FoodSerializers(food, data=data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({'message': 'Food item updated successfully'}, status=200)
        return Response(serializer.errors, status=400)


@api_view(['GET'])
def list_users(request):
    users = User.objects.all().order_by('-id')
    serializer = UserSerializer(users, many=True)
    return Response(serializer.data)


@api_view(['DELETE'])
def delete_user(request, id):
    try:
        user = User.objects.get(id=id)
        user.delete()
        return Response({'message': 'User deleted successfully'}, status=200)
    except User.DoesNotExist:
        return Response({'error': 'User Not Found'}, status=404)


def get_sales_total(start_date):
    aware_start = make_aware(datetime.combine(start_date, datetime.min.time()))
    paid_order_numbers = PaymentDetail.objects.filter(
        payment_date__gte=aware_start
    ).values_list('order_number', flat=True)
    total = Order.objects.filter(order_number__in=paid_order_numbers).annotate(
        line_total=F('quantity') * F('food__item_price')
    ).aggregate(total_amount=Sum('line_total'))['total_amount'] or 0.0
    return round(total, 2)


@api_view(['GET'])
def dashboard_metrics(request):
    restaurant_id = request.GET.get('restaurant_id')

    # 'null' string ya empty string ko None treat karo
    if restaurant_id in ('null', '', None):
        restaurant_id = None

    if restaurant_id:
        order_nums = get_restaurant_order_numbers(restaurant_id)
        order_addresses = OrderAddress.objects.filter(order_number__in=order_nums)
        orders = Order.objects.filter(food__restaurant_id=restaurant_id)
    else:
        order_addresses = OrderAddress.objects.all()
        orders = Order.objects.all()

    today_date = now().date()
    start_of_week = today_date - timedelta(days=today_date.weekday())
    start_of_month = today_date.replace(day=1)
    start_of_year = today_date.replace(month=1, day=1)

    def get_sales(start_date):
        aware_start = make_aware(datetime.combine(start_date, datetime.min.time()))
        paid_order_numbers = PaymentDetail.objects.filter(
            payment_date__gte=aware_start
        ).values_list('order_number', flat=True)
        total = orders.filter(
            order_number__in=paid_order_numbers
        ).annotate(
            line_total=F('quantity') * F('food__item_price')
        ).aggregate(total_amount=Sum('line_total'))['total_amount'] or 0.0
        return round(total, 2)

    data = {
        "total_orders": order_addresses.count(),
        "new_orders": order_addresses.filter(order_final_status__isnull=True).count(),
        "confirmed_orders": order_addresses.filter(order_final_status='Order Confirmed').count(),
        "food_preparing": order_addresses.filter(order_final_status='Food being Prepared').count(),
        "food_pickup": order_addresses.filter(order_final_status='Food Pickup').count(),
        "food_delivered": order_addresses.filter(order_final_status='Food Delivered').count(),
        "cancelled_orders": order_addresses.filter(order_final_status='Order Cancelled').count(),
        "total_users": User.objects.count(),
        "total_categories": Category.objects.filter(restaurant_id=restaurant_id).count() if restaurant_id else Category.objects.count(),
        "total_reviews": Review.objects.count(),
        "total_wishlists": Wishlist.objects.count(),
        "today_sales": get_sales(today_date),
        "week_sales": get_sales(start_of_week),
        "month_sales": get_sales(start_of_month),
        "year_sales": get_sales(start_of_year),
    }
    return Response(data)


@api_view(['GET'])
def monthly_sales_summary(request):
    orders = (
        Order.objects.filter(is_order_placed=True)
        .values('order_number')
        .annotate(
            total_price=Coalesce(
                Sum(F('quantity') * F('food__item_price'), output_field=DecimalField(max_digits=12, decimal_places=2)),
                Decimal('0.00')
            )
        )
    )
    order_price_map = {o['order_number']: o['total_price'] for o in orders}

    addresses = (
        OrderAddress.objects
        .filter(order_number__in=order_price_map.keys())
        .annotate(month=TruncMonth('order_time'))
        .values('month', 'order_number')
    )

    month_totals = defaultdict(lambda: Decimal('0.00'))
    for addr in addresses:
        label = addr['month'].strftime('%b %Y')
        month_totals[label] += order_price_map.get(addr['order_number'], Decimal('0.00'))

    result = [{"month": m, "sales": total} for m, total in month_totals.items()]
    return Response(result)


@api_view(['GET'])
def top_selling_foods(request):
    top_foods = (
        Order.objects.filter(is_order_placed=True)
        .values('food__item_name')
        .annotate(total_sold=Sum('quantity'))
        .order_by('-total_sold')[:5]
    )
    return Response(top_foods)


@api_view(['GET'])
def weekly_sales_summary(request):
    orders = (
        Order.objects.filter(is_order_placed=True)
        .values('order_number')
        .annotate(
            total_price=Coalesce(
                Sum(F('quantity') * F('food__item_price'), output_field=DecimalField(max_digits=12, decimal_places=2)),
                Decimal('0.00')
            )
        )
    )
    order_price_map = {o['order_number']: o['total_price'] for o in orders}

    addresses = (
        OrderAddress.objects
        .filter(order_number__in=order_price_map.keys())
        .annotate(week=TruncWeek('order_time'))
        .values('week', 'order_number')
    )

    weekly_totals = defaultdict(lambda: Decimal('0.00'))
    for addr in addresses:
        label = addr['week'].strftime('Week %W')
        weekly_totals[label] += order_price_map.get(addr['order_number'], Decimal('0.00'))

    result = [{"week": w, "sales": total} for w, total in weekly_totals.items()]
    return Response(result)


@api_view(['GET'])
def weekly_user_registrations(request):
    data = (
        User.objects
        .annotate(week=TruncWeek('reg_date'))
        .values('week')
        .annotate(new_users=Count('id'))
        .order_by('week')
    )
    result = [
        {"week": entry['week'].strftime('Week %W'), "new_users": entry['new_users']}
        for entry in data
    ]
    return Response(result)


@api_view(['GET'])
def track_order(request, order_number):
    try:
        order = Order.objects.filter(order_number=order_number, is_order_placed=True).first()
        if not order:
            return Response({"message": "Order not found"}, status=404)
        tracking_entries = FoodTracking.objects.filter(order=order)
        serializer = FoodTrackingSerializer(tracking_entries, many=True)
        return Response(serializer.data)
    except Exception as e:
        return Response({"error": str(e)}, status=400)


@api_view(['POST'])
def cancel_order(request, order_number):
    remark = request.data.get('remark')
    try:
        address = OrderAddress.objects.get(order_number=order_number)
        address.order_final_status = "Order Cancelled"
        address.save()

        sample_order = Order.objects.filter(order_number=order_number).first()
        FoodTracking.objects.create(
            order=sample_order, remark=remark,
            status="Order Cancelled", order_cancelled_by_user=True
        )
        return Response({"message": "Order Cancelled successfully"}, status=200)
    except Exception as e:
        return Response({"message": str(e)}, status=400)


@api_view(['POST'])
def add_review(request, food_id):
    user_id = request.data.get('user_id')
    rating = request.data.get('rating')
    comment = request.data.get('comment')
    try:
        user = User.objects.get(id=user_id)
        food = Food.objects.get(id=food_id)
        Review.objects.create(user=user, food=food, rating=rating, comment=comment)
        return Response({"message": "Review Submitted"}, status=201)
    except (User.DoesNotExist, Food.DoesNotExist):
        return Response({"message": "User or Food not Found"}, status=404)


@api_view(['GET'])
def food_reviews(request, food_id):
    reviews = Review.objects.filter(food_id=food_id).order_by('-created_at')
    serializer = ReviewSerializer(reviews, many=True)
    return Response(serializer.data)


@api_view(['DELETE', 'PUT'])
def review_detail(request, id):
    try:
        review = Review.objects.get(id=id)
    except Review.DoesNotExist:
        return Response({"message": "Review not Found"}, status=404)

    if request.method == 'DELETE':
        review.delete()
        return Response({"message": "Review deleted"}, status=200)
    if request.method == 'PUT':
        data = {
            "rating": request.data.get("rating", review.rating),
            "comment": request.data.get("comment", review.comment)
        }
        serializer = ReviewSerializer(review, data=data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Review Updated"}, status=200)
        return Response(serializer.errors, status=400)


@api_view(['GET'])
def food_rating_summary(request, food_id):
    reviews = Review.objects.filter(food_id=food_id)
    rating_summary = reviews.values('rating').annotate(count=Count('rating')).order_by('-rating')
    breakdown = {entry['rating']: entry['count'] for entry in rating_summary}
    avg_data = reviews.aggregate(average=Avg('rating'))
    average = round(avg_data['average'] or 0, 1)
    total_reviews = reviews.count()
    return Response({'average': average, 'total_reviews': total_reviews, 'breakdown': breakdown})


@api_view(['GET'])
def all_reviews(request):
    reviews = Review.objects.select_related('user', 'food').order_by('-created_at')
    serializer = ReviewSerializer(reviews, many=True)
    return Response(serializer.data)


@api_view(['DELETE'])
def delete_review(request, id):
    try:
        review = Review.objects.get(id=id)
        review.delete()
        return Response({"message": "Review deleted successfully"}, status=200)
    except Review.DoesNotExist:
        return Response({"message": "Review not found"}, status=404)


@api_view(['GET'])
def food_delivered(request):
    restaurant_id = request.GET.get('restaurant_id')
    if restaurant_id:
        order_nums = get_restaurant_order_numbers(restaurant_id)
        delivered_orders = OrderAddress.objects.filter(
            order_final_status="Food Delivered",
            order_number__in=order_nums
        )
    else:
        delivered_orders = OrderAddress.objects.filter(order_final_status="Food Delivered")

    order_numbers = delivered_orders.values_list('order_number', flat=True)
    orders = Order.objects.filter(order_number__in=order_numbers).select_related('user', 'food')
    serializer = OrderDeliveredSerializer(orders, many=True)
    return Response(serializer.data)


@api_view(['GET', 'POST'])
def restaurant_list(request):
    if request.method == 'GET':
        restaurants = Restaurant.objects.all().order_by('-created_date')
        serializer = RestaurantSerializer(restaurants, many=True)
        return Response(serializer.data)

    if request.method == 'POST':
        data = request.data.copy()
        if 'owner_password' in data:
            data['owner_password'] = make_password(data['owner_password'])
        serializer = RestaurantSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response({'message': 'Restaurant added successfully'}, status=201)
        return Response(serializer.errors, status=400)


@api_view(['GET', 'PUT', 'DELETE'])
def restaurant_detail(request, id):
    try:
        restaurant = Restaurant.objects.get(id=id)
    except Restaurant.DoesNotExist:
        return Response({'error': 'Restaurant not found'}, status=404)

    if request.method == 'GET':
        serializer = RestaurantSerializer(restaurant)
        return Response(serializer.data)
    if request.method == 'PUT':
        data = request.data.copy()
        if 'owner_password' in data and data['owner_password']:
            data['owner_password'] = make_password(data['owner_password'])
        serializer = RestaurantSerializer(restaurant, data=data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({'message': 'Restaurant updated successfully'}, status=200)
        return Response(serializer.errors, status=400)
    if request.method == 'DELETE':
        restaurant.delete()
        return Response({'message': 'Restaurant deleted successfully'}, status=200)


@api_view(['PUT'])
def restaurant_suspend(request, id):
    try:
        restaurant = Restaurant.objects.get(id=id)
        restaurant.status = 'suspended' if restaurant.status == 'active' else 'active'
        restaurant.save()
        return Response({
            'message': f'Restaurant {restaurant.status} successfully',
            'status': restaurant.status
        }, status=200)
    except Restaurant.DoesNotExist:
        return Response({'error': 'Restaurant not found'}, status=404)


@api_view(['GET', 'PUT'])
def platform_settings(request):
    settings, created = PlatformSettings.objects.get_or_create(id=1)
    if request.method == 'GET':
        serializer = PlatformSettingsSerializer(settings)
        return Response(serializer.data)
    if request.method == 'PUT':
        serializer = PlatformSettingsSerializer(settings, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({'message': 'Settings saved successfully'}, status=200)
        return Response(serializer.errors, status=400)


@api_view(['POST'])
def restaurant_owner_login(request):
    email = request.data.get('email')
    password = request.data.get('password')
    try:
        restaurant = Restaurant.objects.get(owner_email=email)
        if check_password(password, restaurant.owner_password):
            return Response({
                'message': 'Login successful',
                'restaurant_id': restaurant.id,
                'restaurant_name': restaurant.name,
                'owner_email': restaurant.owner_email,
            }, status=200)
        else:
            return Response({'message': 'Invalid credentials'}, status=401)
    except Restaurant.DoesNotExist:
        return Response({'message': 'Invalid credentials'}, status=401)
    

@api_view(['GET'])
def delivered_orders_for_user(request, user_id):
    # Sirf delivered orders fetch karo
    delivered_addresses = OrderAddress.objects.filter(
        user_id=user_id,
        order_final_status="Food Delivered"
    ).values_list('order_number', flat=True)

    # Un orders ke foods fetch karo
    orders = Order.objects.filter(
        user_id=user_id,
        order_number__in=delivered_addresses,
        is_order_placed=True
    ).select_related('food')

    # Har food ke liye user ka review check karo
    result = []
    for order in orders:
        existing_review = Review.objects.filter(
            user_id=user_id,
            food=order.food
        ).first()

        result.append({
            'order_id': order.id,
            'order_number': order.order_number,
            'food_id': order.food.id,
            'food_name': order.food.item_name,
            'food_image': request.build_absolute_uri(order.food.image.url) if order.food.image else None,
            'food_price': str(order.food.item_price),
            'quantity': order.quantity,
            'already_reviewed': existing_review is not None,
            'my_rating': existing_review.rating if existing_review else None,
            'my_comment': existing_review.comment if existing_review else None,
            'my_review_id': existing_review.id if existing_review else None,
        })

    return Response(result)