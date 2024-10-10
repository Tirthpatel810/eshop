from django.utils import timezone
from datetime import timedelta
from functools import wraps
import random
import string
from django.shortcuts import get_object_or_404, render,redirect
from .models import * 
from django.core.mail import send_mail
from django.contrib import messages
import razorpay
from django.conf import settings

razorpay_client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))

def login_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        # Assuming you are storing the user's email in session after login
        if request.session.get('email'):
            return view_func(request, *args, **kwargs)
        else:
            return redirect('login')  # Redirect to your custom login page if not authenticated
    return wrapper

def index(request):
    featured_products = Product.objects.all().order_by('-discount')[:3]
    context = {
        'featured_products': featured_products,
    }
    return render(request, 'index.html', context)

def about(request):
    return render(request, 'about.html')

def register(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')

        if password == confirm_password:
            # Create user instance
            user = CustomUser(username=username, email=email)
            user.set_password(password)  # Hash password
            user.save()
            return redirect('login')  # Redirect to login page after successful registration
        else:
            error_message = "Passwords do not match"
            return render(request, 'register.html', {'error_message': error_message})
    
    return render(request, 'register.html')

def login(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')

        try:
            user = CustomUser.objects.get(email=email)
        except CustomUser.DoesNotExist:
            error_message = "Invalid email or password"
            return render(request, 'login.html', {'error_message': error_message})

        if user.check_password(password):
            # Set session or cookie to keep the user logged in
            request.session['email'] = user.email
            return redirect('index')
        else:
            error_message = "Invalid email or password"
            return render(request, 'login.html', {'error_message': error_message})

    return render(request, 'login.html')

def logout(request):
    request.session.flush()  # Clears all session data
    return redirect('index')  # Redirect to login page after logging out

def contact(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        mobile = request.POST.get('mobile')
        question = request.POST.get('question')

        Contact.objects.create(name=name, email=email,mobile=mobile,question=question)
        return redirect('index')
    return render(request, 'contact.html')

def product_list(request):
    products = Product.objects.all()

    # Search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        products = products.filter(name__icontains=search_query)

    # Sorting functionality
    sort_by = request.GET.get('sort', 'name')  # Default sorting by name
    products = products.order_by(sort_by)

    context = {
        'products': products,
        'search_query': search_query,
        'sort_by': sort_by,
    }
    return render(request, 'product_list.html', context)

def product_list_view(request):
    # Handle search and sorting here
    products = Product.objects.all()  # Add filtering/sorting logic
    return render(request, 'product_list.html', {'products': products})

def product_detail_view(request, product_id):
    product = get_object_or_404(Product, product_id=product_id)
    return render(request, 'product_detail.html', {'product': product})

@login_required  # Ensure the user is logged in
def add_to_cart(request, product_id):
    product = get_object_or_404(Product, product_id=product_id)
    # Get or create the cart for the current logged-in user
    email = request.session['email']
    # Check if the product is already in the cart
    cart_item, created = CartItem.objects.get_or_create(email=email, product=product)
    if not created:
        # If the item already exists, increment the quantity
        cart_item.quantity += 1
        cart_item.save()

    return redirect('cart_view')

@login_required
def view_cart(request):
    # Get the cart items for the logged-in user
    cart_items = CartItem.objects.filter(email=request.session['email'])
    total_price = sum(item.total_price() for item in cart_items)
    return render(request, 'cart.html', {'cart_items': cart_items, 'total_price': total_price})

def cart_view(request):
    # Check for cart in session
    cart = request.session.get('cart', {})
    total_price = sum(float(item['price']) * item['quantity'] for item in cart.values())
    return render(request, 'cart.html', {'cart': cart, 'total_price': total_price})

@login_required
def update_cart_item(request, cart_item_id):
    # Get the cart item for the logged-in user
    cart_item = get_object_or_404(CartItem, id=cart_item_id, email=request.session['email'])  # Use request.user.email
    
    if request.method == 'POST':
        new_quantity = int(request.POST.get('quantity', 1))
        if new_quantity > 0:
            cart_item.quantity = new_quantity
            cart_item.save()
        else:
            cart_item.delete()  # Remove the item if quantity is zero
    
    return redirect('cart_view')

@login_required
def remove_cart_item(request, cart_item_id):
    cart_item = get_object_or_404(CartItem, id=cart_item_id, email=request.session['email'])
    cart_item.delete()
    return redirect('cart_view')


def checkout(request):
    return redirect('index')

def forgot_password(request):
    if request.method == 'POST':
        email = request.POST['email']

        # Check if the email exists in CustomUser
        user = None
        try:
            user = CustomUser.objects.get(email=email)
        except CustomUser.DoesNotExist:
            messages.error(request, "Email not found!")
            return redirect('forgot_password')

        # Generate a random reset code
        reset_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

        # Save the reset code and expiration time (valid for 2 minutes)
        user.reset_code = reset_code
        user.reset_code_expires_at = timezone.now() + timedelta(minutes=2)
        user.save()

        # Send the reset code via email
        try:
            send_mail(
                'Password Reset Code',
                f'Your password reset code is: {reset_code}. It will expire in 2 minutes.',
                'shethvanshil1234@gmail.com',
                [email],
                fail_silently=False,
            )
        except Exception as e:
            messages.error(request, f"Error sending email: {e}")
            return redirect('forgot_password')

        messages.success(request, "A reset code has been sent to your email.")
        return redirect('verify_reset_code')

    return render(request, 'forgot_password.html')

def verify_reset_code(request):
    if request.method == 'POST':
        reset_code = request.POST['reset_code']

        # Check for valid reset code in CustomUser
        user = None
        try:
            user = CustomUser.objects.get(reset_code=reset_code, reset_code_expires_at__gt=timezone.now())
        except CustomUser.DoesNotExist:
            messages.error(request, "Invalid or expired reset code!")
            return redirect('verify_reset_code')

        # If reset code is valid, proceed to reset password form
        return redirect('reset_password', user_id=user.id)

    return render(request, 'verify_reset_code.html')

def reset_password(request, user_id):
    # Try to find the user in CustomUser
    user = None
    try:
        user = CustomUser.objects.get(id=user_id)
    except CustomUser.DoesNotExist:
        messages.error(request, "User not found!")
        return redirect('login')

    if request.method == 'POST':
        new_password = request.POST['new_password']
        confirm_password = request.POST['confirm_password']

        if new_password != confirm_password:
            messages.error(request, "Passwords do not match!")
            return redirect('reset_password', user_id=user_id)

        # Update the user's password
        user.set_password(new_password)  # Set hashed password using the model's set_password method
        user.reset_code = None  # Clear the reset code
        user.reset_code_expires_at = None  # Clear the expiration time
        user.save()

        messages.success(request, "Password has been reset successfully!")
        return redirect('login')

    return render(request, 'reset_password.html', {'user_id': user_id})

@login_required
def checkout(request):
    cart_items = CartItem.objects.filter(email=request.session['email'])
    total_price = sum(item.total_price() for item in cart_items)
    user = get_object_or_404(CustomUser,email=request.session['email'])
    
    if request.method == 'POST':
        payment_method = request.POST.get('payment_method')
        
        if payment_method == 'COD':
            # Create order for COD
            order = Order.objects.create(
                user=user,
                total_amount=total_price,
                payment_method='COD',
                payment_status='Pending'
            )
            # Add order items
            for item in cart_items:
                OrderItem.objects.create(order=order, product=item.product, quantity=item.quantity)
            cart_items.delete()  # Clear the cart after order creation
            return redirect('order_success')  # Redirect to success page

        elif payment_method == 'Online':
            # Create Razorpay order
            razorpay_order = razorpay_client.order.create({
                "amount": int(total_price * 100),  # Amount in paise
                "currency": "INR",
                "payment_capture": "1"
            })

            order = Order.objects.create(
                user=user,
                total_amount=total_price,
                payment_method='Online',
                razorpay_order_id=razorpay_order['id'],
                payment_status='Pending'
            )
            for item in cart_items:
                OrderItem.objects.create(order=order, product=item.product, quantity=item.quantity)
            
            context = {
                'order': order,
                'cart_items': cart_items,
                'razorpay_order_id': razorpay_order['id'],
                'razorpay_merchant_key': settings.RAZORPAY_KEY_ID,
                'total_price': total_price,
            }
            return render(request, 'payment.html', context)
    
    return render(request, 'checkout.html', {'cart_items': cart_items, 'total_price': total_price})


@login_required
def payment_success(request):
    if request.method == 'POST':
        payment_id = request.POST.get('razorpay_payment_id')
        order_id = request.POST.get('razorpay_order_id')
        signature = request.POST.get('razorpay_signature')

        # Verify the Razorpay signature
        try:
            razorpay_client.utility.verify_payment_signature({
                'razorpay_order_id': order_id,
                'razorpay_payment_id': payment_id,
                'razorpay_signature': signature }) 
        except razorpay.errors.SignatureVerificationError: 
            return render(request, 'payment_failed.html')

        order = Order.objects.get(razorpay_order_id=order_id)
        order.razorpay_payment_id = payment_id
        order.razorpay_signature = signature
        order.payment_status = 'Completed'
        order.save()

        # Clear the cart after successful payment
        CartItem.objects.filter(email=request.session['email']).delete()

        return redirect('order_success')  # Redirect to order success page
    return redirect('checkout')

@login_required
def order_success(request):
    return render(request, 'order_success.html')

@login_required
def view_order(request):
    user = get_object_or_404(CustomUser,email=request.session['email'])
    orders = Order.objects.filter(user=user).order_by('-created_at')
    return render(request, 'view_order.html', {'orders': orders})

@login_required
def order_success(request):
    return render(request, 'order_success.html')

@login_required
def track_order(request, order_id):
    user = get_object_or_404(CustomUser,email=request.session['email'])
    order = get_object_or_404(Order, id=order_id, user=user)
    
    if order.payment_status == 'Shipped':
        tracking_info = "Your order has been shipped."
    elif order.payment_status == 'Pending':
        tracking_info = "Your order is still being processed."
    elif order.payment_status == 'Cancelled':
        tracking_info = "Your order was cancelled."
    elif order.payment_status == 'Completed':
        tracking_info = "Your order was delivered."
    else:
        tracking_info = "Order status unknown."

    return render(request, 'track_order.html', {'order': order, 'tracking_info': tracking_info})

@login_required
def cancel_order(request, order_id):
    user = get_object_or_404(CustomUser,email=request.session['email'])
    order = get_object_or_404(Order, id=order_id, user=user)

    # Check if the order can still be canceled (before shipment or not canceled already)
    if order.payment_status != 'Shipped' and order.payment_status != 'Cancelled':
        order.payment_status = 'Cancelled'
        order.save()
        messages.success(request, f'Order #{order.id} has been canceled successfully.')
    else:
        messages.error(request, f'Order #{order.id} cannot be canceled.')

    return redirect('view_orders')