from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse 
from django.core.mail import send_mail
from django.conf import settings
from django.db.models import Q, Avg, Count 
from django.utils import timezone
from django.views.generic import TemplateView
from django.urls import reverse 
from django.core.paginator import Paginator
from datetime import datetime, timedelta 
import random
from .models import *
from .forms import (
    ContactForm, 
    CustomPasswordResetForm, 
    CustomSetPasswordForm, 
    UserProfileForm, 
    UserForm, 
    PasswordChangeForm, 
    ServiceRequestForm, 
    ServiceResponseForm
)

# =======================================================
# 1. Public & General Views
# =======================================================

def index(request):
    """
    Home page logic: Show categories and featured services.
    """
    categories = ServiceCategory.objects.all()
    
    # Get top 6 rated services for featured section - is_active=True services only
    featured_services = Service.objects.filter(
        is_active=True
    ).annotate(
        avg_rating=Avg('reviews__rating')
    ).order_by('-avg_rating')[:6]
    
    context = {
        'categories': categories,
        'featured_services': featured_services,
    }
    return render(request, 'index.html', context)


def services(request):
    """
    Services page logic: Filter, search, and sort active services.
    """
    categories = ServiceCategory.objects.all()
    services = Service.objects.filter(is_active=True)  # Only active services
    
    # Filter by category
    category_name = request.GET.get('category')
    if category_name and category_name != 'all':
        services = services.filter(category__name=category_name)
    
    # Filter by search term
    search_term = request.GET.get('search')
    if search_term:
        services = services.filter(
            Q(title__icontains=search_term) |
            Q(description__icontains=search_term) |
            Q(category__name__icontains=search_term) |
            Q(provider__first_name__icontains=search_term) |
            Q(provider__last_name__icontains=search_term)
        )
    
    # Filter by location
    location = request.GET.get('location')
    if location:
        services = services.filter(location__icontains=location)
    
    # Sort services
    sort_by = request.GET.get('sort', 'rating')
    if sort_by == 'rating':
        services = services.annotate(avg_rating=Avg('reviews__rating')).order_by('-avg_rating')
    elif sort_by == 'price-low':
        services = services.extra(
            select={'min_price': "CAST(SUBSTRING(price_range FROM '₹([0-9]+)') AS INTEGER)"}
        ).order_by('min_price')
    elif sort_by == 'price-high':
        services = services.extra(
            select={'max_price': "CAST(SUBSTRING(price_range FROM '₹([0-9]+)') AS INTEGER)"}
        ).order_by('-max_price')
    elif sort_by == 'reviews':
        services = services.annotate(review_count=Count('reviews')).order_by('-review_count')
    
    context = {
        'categories': categories,
        'services': services,
        'search_term': search_term,
        'location_filter': location,
        'category_filter': category_name,
    }
    return render(request, 'services.html', context)

def service_detail(request, service_id):
    """
    Service detail page logic: show service details, provider info, and reviews.
    """
    service = get_object_or_404(Service, id=service_id, is_active=True)
    # NOTE: Reviews filter changed to link directly to the service for accuracy.
    reviews = Review.objects.filter(service=service, is_approved=True).order_by('-created_at')[:10]
    
    # Calculate average rating
    avg_rating = reviews.aggregate(avg_rating=Avg('rating'))['avg_rating'] or 0
    
    context = {
        'service': service,
        'reviews': reviews,
        'avg_rating': round(avg_rating, 1),
        'review_count': reviews.count(),
    }
    return render(request, 'service_detail.html', context)

def contact_view(request):
    """
    Handle contact form submission and save the message.
    """
    form = ContactForm()
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            contact_message = form.save()
            
            # Send email notification (optional)
            try:
                # Assuming CONTACT_EMAIL is defined in settings.py
                send_mail(
                    f'New Contact Message: {contact_message.get_subject_display()}',
                    f'''
                    Name: {contact_message.name}
                    Email: {contact_message.email}
                    Phone: {contact_message.phone}
                    Subject: {contact_message.get_subject_display()}
                    Message: {contact_message.message}
                    ''',
                    settings.DEFAULT_FROM_EMAIL,
                    [getattr(settings, 'CONTACT_EMAIL', settings.DEFAULT_FROM_EMAIL)],
                    fail_silently=True,
                )
            except Exception as e:
                print(f"Email sending failed: {e}")
            
            messages.success(request, 'Your message has been sent successfully! We will get back to you soon.')
            return redirect('contact')
        else:
            messages.error(request, 'Please correct the errors below.')
    
    # index function, which was redundant, is removed. home is used for the main index.
    
    return render(request, 'contact.html', {
        'form': form
    })

# --- Class-based views for static content ---

class AboutView(TemplateView):
    template_name = 'about.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get active team members or use default hardcoded ones
        team_members = TeamMember.objects.filter(is_active=True).order_by('order')
        
        if not team_members.exists():
            # Create default team members if none exist (Used by HTML template)
            context['team_members'] = [
                {
                    'name': 'Sachin Sonkamble',
                    'position': 'CEO & Founder',
                    'initials': 'SS',
                    'description': 'Former tech executive with 15+ years in building marketplace platforms.',
                    'color': '3B82F6'
                },
                {
                    'name': 'Raj Shigavan', 
                    'position': 'CTO & Co-Founder',
                    'initials': 'RS',
                    'description': 'Technology leader with expertise in scalable platforms and mobile applications.',
                    'color': '10b981'
                },
                {
                    'name': 'Amar Yewate',
                    'position': 'Head of Operations', 
                    'initials': 'AY',
                    'description': 'Operations expert ensuring smooth service delivery and quality standards.',
                    'color': 'f59e0b'
                }
            ]
        else:
            context['team_members'] = team_members

        context['stats'] = {
            'customers': '10,000+',
            'professionals': '2,500+', 
            'services_completed': '50,000+',
            'average_rating': '4.8/5'
        }
        
        return context

# Wrappers for TemplateView
class PrivacyPolicyView(TemplateView):
    template_name = 'privacy_policy.html'
def privacy_policy_view(request):
    return PrivacyPolicyView.as_view()(request)

class TermsOfServiceView(TemplateView):
    template_name = 'terms_of_service.html'
def terms_of_service_view(request):
    return TermsOfServiceView.as_view()(request)

# =======================================================
# 2. Authentication Views
# =======================================================

def user_register(request):
    """
    User registration logic: Create CustomUser and handle provider fields.
    """
    categories = ServiceCategory.objects.all()
    
    if request.method == 'POST':
        try:
            # Get form data
            name = request.POST.get('name', '').strip()
            email = request.POST.get('email', '').strip().lower()
            password = request.POST.get('password', '')
            confirm_password = request.POST.get('confirm_password', '')
            phone = request.POST.get('phone', '').strip()
            location = request.POST.get('location', '').strip()
            user_type = request.POST.get('user_type', 'customer')
            
            # Validation
            if not all([name, email, password, confirm_password, phone, location]):
                messages.error(request, 'Please fill all required fields.')
                return render(request, 'register.html', {'categories': categories})
            
            if password != confirm_password:
                messages.error(request, 'Passwords do not match.')
                return render(request, 'register.html', {'categories': categories})
            
            if len(password) < 6:
                messages.error(request, 'Password must be at least 6 characters long.')
                return render(request, 'register.html', {'categories': categories})
            
            if CustomUser.objects.filter(email=email).exists():
                messages.error(request, 'User with this email already exists.')
                return render(request, 'register.html', {'categories': categories})
            
            # Create user
            first_name = name.split(' ')[0]
            last_name = ' '.join(name.split(' ')[1:]) if len(name.split(' ')) > 1 else ''
            
            user = CustomUser.objects.create_user(
                username=email,
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name,
                user_type=user_type,
                phone=phone,
                location=location
            )
            
            # Handle provider-specific data
            if user_type == 'provider':
                business_name = request.POST.get('business_name', '').strip()
                experience = request.POST.get('experience', '')
                
                if business_name:
                    user.business_name = business_name
                if experience:
                    user.experience = experience
                
                user.save()
                
                # Save service categories
                category_ids = request.POST.getlist('categories')
                if category_ids:
                    user.service_categories.set(category_ids)
            
            # Send welcome email
            try:
                send_mail(
                    'Welcome to FixFinder! 🛠️',
                    f'''
Hello {user.first_name},

Thank you for registering with FixFinder! We're excited to have you on board.

Your account has been successfully created as a {user_type}.

Get started by:
- Browsing services
- Posting service requests
- Connecting with professionals

If you have any questions, feel free to contact our support team.

Best regards,
FixFinder Team
                    ''',
                    settings.DEFAULT_FROM_EMAIL,
                    [user.email],
                    fail_silently=False,
                )
            except Exception as e:
                print(f"Email sending failed: {e}")
            
            # Create notification
            Notification.objects.create(
                user=user,
                title='Welcome to FixFinder!',
                message='Your account has been created successfully.',
                notification_type='registration'
            )
            
            messages.success(request, 'Registration successful! Please login to continue.')
            return redirect('login')
            
        except Exception as e:
            messages.error(request, f'Error during registration: {str(e)}')
            return render(request, 'register.html', {'categories': categories})
    
    return render(request, 'register.html', {'categories': categories})

def user_login(request):
    """
    User login logic: Authenticate, set session, and redirect.
    """
    if request.method == 'POST':
        email = request.POST.get('email', '').strip().lower()
        password = request.POST.get('password', '')
        
        if not email or not password:
            messages.error(request, 'Please enter both email and password.')
            return render(request, 'login.html')
        
        # Use email as username for authentication
        user = authenticate(request, username=email, password=password)
        
        if user is not None:
            if user.is_active:
                login(request, user)
                
                # Create login notification
                Notification.objects.create(
                    user=user,
                    title='Login Successful',
                    message=f'You logged in successfully at {timezone.now().strftime("%Y-%m-%d %H:%M")}',
                    notification_type='login'
                )
                
                messages.success(request, f'Welcome back, {user.first_name}!')
                
                # Redirect based on user type
                if user.user_type == 'admin':
                    return redirect('admin_dashboard')
                else:
                    return redirect('dashboard')
            else:
                messages.error(request, 'Your account is disabled.')
        else:
            messages.error(request, 'Invalid email or password.')
    
    return render(request, 'login.html')

def user_logout(request):
    """
    Logout logic: Clear session and redirect to home.
    """
    if request.user.is_authenticated:
        # Create logout notification
        Notification.objects.create(
            user=request.user,
            title='Logout',
            message=f'You logged out at {timezone.now().strftime("%Y-%m-%d %H:%M")}',
            notification_type='logout'
        )
    
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('index') # Changed to 'index' as per the URL pattern for homepage

def password_reset_request(request):
    """
    Initiates password reset process: creates token and sends email.
    """
    if request.method == 'POST':
        form = CustomPasswordResetForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            # NOTE: CustomUser is used instead of User here for consistency with the rest of the app
            user = CustomUser.objects.get(email=email) 
            
            # Create password reset token
            reset_token = PasswordResetToken.objects.create(user=user)
            
            # Send email with reset link
            reset_link = request.build_absolute_uri(
                reverse('password_reset_confirm', kwargs={'token': reset_token.token})
            )
            
            try:
                send_mail(
                    'Reset Your FixFinder Password',
                    f'''
                    Hello {user.username},
                    
                    You requested a password reset for your FixFinder account.
                    
                    Please click the link below to reset your password:
                    {reset_link}
                    
                    This link will expire in 24 hours.
                    
                    If you didn't request this reset, please ignore this email.
                    
                    Best regards,
                    FixFinder Team
                    ''',
                    settings.DEFAULT_FROM_EMAIL,
                    [email],
                    fail_silently=False,
                )
                
                messages.success(request, 'Password reset link has been sent to your email address. Please check your inbox.')
                return redirect('password_reset_done')
                
            except Exception as e:
                messages.error(request, 'Failed to send email. Please try again.')
                reset_token.delete()  # Delete token if email fails
                
        else:
            for error in form.errors.values():
                messages.error(request, error)
    else:
        form = CustomPasswordResetForm()
    
    return render(request, 'password_reset.html', {'form': form})



def simple_password_reset(request):
    """
    Ek hi page mein complete password reset - aapke design ke saath
    """
    if request.method == 'POST':
        # Step 1: Email submit
        if 'email' in request.POST:
            email = request.POST.get('email', '').strip().lower()
            
            if not email:
                messages.error(request, 'Please enter your email address.')
                return render(request, 'password_reset_simple.html')
            
            try:
                user = CustomUser.objects.get(email=email, is_active=True)
                
                # Generate random 6-digit code
                reset_code = str(random.randint(100000, 999999))
                
                # Save code in session (24 hours expiry)
                request.session['reset_code'] = reset_code
                request.session['reset_email'] = email
                request.session.set_expiry(86400)  # 24 hours
                
                # Send email with code
                send_mail(
                    'Your FixFinder Password Reset Code',
                    f'''
Hello {user.first_name},

Your password reset code is: {reset_code}

Enter this code on the password reset page to set your new password.

This code will expire in 24 hours.

If you didn't request this reset, please ignore this email.

Best regards,
FixFinder Team
                    ''',
                    settings.DEFAULT_FROM_EMAIL,
                    [email],
                    fail_silently=False,
                )
                
                messages.success(request, f'Password reset code sent to {email}')
                return render(request, 'password_reset_simple.html', {'show_code_form': True})
                
            except CustomUser.DoesNotExist:
                messages.error(request, 'No account found with this email address.')
                return render(request, 'password_reset_simple.html')
        
        # Step 2: Code verification and password reset
        elif 'reset_code' in request.POST and 'new_password' in request.POST:
            entered_code = request.POST.get('reset_code', '').strip()
            new_password = request.POST.get('new_password', '')
            confirm_password = request.POST.get('confirm_password', '')
            
            # Validate session data
            if not all([request.session.get('reset_code'), request.session.get('reset_email')]):
                messages.error(request, 'Reset session expired. Please start again.')
                return redirect('simple_password_reset')
            
            # Validate code
            if entered_code != request.session.get('reset_code'):
                messages.error(request, 'Invalid reset code. Please try again.')
                return render(request, 'password_reset_simple.html', {'show_code_form': True})
            
            # Validate passwords
            if len(new_password) < 6:
                messages.error(request, 'Password must be at least 6 characters long.')
                return render(request, 'password_reset_simple.html', {'show_code_form': True})
            
            if new_password != confirm_password:
                messages.error(request, 'Passwords do not match.')
                return render(request, 'password_reset_simple.html', {'show_code_form': True})
            
            # Update password
            try:
                user = CustomUser.objects.get(email=request.session['reset_email'])
                user.set_password(new_password)
                user.save()
                
                # Clear session
                request.session.flush()
                
                messages.success(request, 'Password reset successfully! You can now login with your new password.')
                return redirect('login')
                
            except CustomUser.DoesNotExist:
                messages.error(request, 'User not found. Please try again.')
                return redirect('simple_password_reset')
    
    # Check if user has active reset session
    show_code_form = bool(request.session.get('reset_code'))
    
    return render(request, 'password_reset_simple.html', {
        'show_code_form': show_code_form
    })



def password_reset_confirm(request, token):
    """
    Validates token and allows user to set a new password.
    """
    try:
        reset_token = PasswordResetToken.objects.get(token=token, is_used=False)
        
        if not reset_token.is_valid():
            messages.error(request, 'This reset link has expired or is invalid.')
            return redirect('password_reset')
        
        if request.method == 'POST':
            # NOTE: CustomUser is used instead of User for form initialization
            form = CustomSetPasswordForm(reset_token.user, request.POST) 
            if form.is_valid():
                form.save()
                reset_token.is_used = True
                reset_token.save()
                
                messages.success(request, 'Your password has been reset successfully. You can now login with your new password.')
                return redirect('login')
            else:
                for error in form.errors.values():
                    messages.error(request, error)
        else:
            form = CustomSetPasswordForm(reset_token.user)
        
        return render(request, 'password_reset_confirm.html', {
            'form': form,
            'token': token,
            'valid_token': True
        })
        
    except PasswordResetToken.DoesNotExist:
        messages.error(request, 'Invalid reset link. Please request a new password reset.')
        return redirect('password_reset')

def password_reset_done(request):
    return render(request, 'password_reset_done.html')

def password_reset_complete(request):
    return render(request, 'password_reset_complete.html')

# =======================================================
# 3. Dashboard & Admin Views
# =======================================================

# views.py में dashboard function ko update karein
@login_required
def dashboard(request):
    """
    Shows personalized dashboard based on user_type (Customer/Provider).
    """
    user = request.user
    
    if user.user_type == 'customer':
        # Customer dashboard
        bookings = Booking.objects.filter(customer=user)
        total_bookings = bookings.count()
        active_bookings = bookings.filter(status__in=['confirmed', 'in_progress']).count()
        completed_bookings = bookings.filter(status='completed').count()
        
        # Calculate total spent - (FIXED: total_price is already correct here)
        total_spent = bookings.filter(status='completed').aggregate(
            total=models.Sum('total_price') 
        )['total'] or 0
        
        recent_bookings = bookings.order_by('-booking_date')[:5]
        
        # Recent activity
        recent_activity = []
        for booking in recent_bookings:
            recent_activity.append({
                'text': f'Booked {booking.service.title if booking.service else booking.service_name} with {booking.provider.get_full_name()}',
                'time': booking.booking_date,
                'type': 'booking',
                'icon': '📋'
            })
        
        context = {
            'total_bookings': total_bookings,
            'active_bookings': active_bookings,
            'completed_bookings': completed_bookings,
            'total_spent': total_spent,
            'recent_activity': recent_activity,
            'recent_bookings': recent_bookings,
            'unread_messages': 0,
        }
        
    elif user.user_type == 'provider':
        # Provider dashboard
        services = Service.objects.filter(provider=user, is_active=True)
        bookings = Booking.objects.filter(provider=user)
        
        total_services = services.count()
        total_bookings = bookings.count()
        active_bookings = bookings.filter(status__in=['confirmed', 'in_progress']).count()
        completed_bookings = bookings.filter(status='completed').count()
        
        # Calculate total earned - (FIXED: total_price is already correct here)
        total_earned = bookings.filter(status='completed').aggregate(
            total=models.Sum('total_price')
        )['total'] or 0
        
        # Calculate average rating
        avg_rating = Review.objects.filter(provider=user).aggregate(
            avg_rating=Avg('rating')
        )['avg_rating'] or 0
        
        recent_bookings = bookings.order_by('-booking_date')[:5]
        
        # Recent activity
        recent_activity = []
        for booking in recent_bookings:
            recent_activity.append({
                'text': f'New booking from {booking.customer.get_full_name()} for {booking.service.title if booking.service else booking.service_name}',
                'time': booking.booking_date,
                'type': 'booking',
                'icon': '📋'
            })
        
        # Service requests in area - ERROR IS FIXED HERE!
        service_requests = ServiceRequest.objects.filter(
            category__in=user.service_categories.values_list('name', flat=True), # FIXED from category__name__in
            location__icontains=user.location.split(',')[0] if user.location else '',
            status='open'
        ).order_by('-created_at')[:3]
        
        # Provider ke liye additional data
        my_services = services[:3]
        total_reviews = Review.objects.filter(provider=user).count()
        
        context = {
            'total_bookings': total_bookings,
            'active_bookings': active_bookings,
            'completed_bookings': completed_bookings,
            'total_earned': total_earned,
            'recent_activity': recent_activity,
            'my_services': my_services,
            'service_requests': service_requests,
            'average_rating': round(avg_rating, 1),
            'total_services': total_services,
            'recent_bookings': recent_bookings,
            'unread_messages': 0,
            'total_reviews': total_reviews,
        }
        
    else:  # Admin
        return redirect('admin_dashboard')
    
    # Add user type for template
    context['user_type'] = user.user_type
    
    return render(request, 'dashboard.html', context)

@login_required
def admin_dashboard(request):
    """
    Admin dashboard logic: Platform statistics and recent activities.
    """
    if request.user.user_type != 'admin':
        messages.error(request, 'Access denied. Admin privileges required.')
        return redirect('dashboard')
    
    # Platform statistics
    total_users = CustomUser.objects.count()
    total_providers = CustomUser.objects.filter(user_type='provider').count()
    total_customers = CustomUser.objects.filter(user_type='customer').count()
    total_services = Service.objects.count()
    total_bookings = Booking.objects.count()
    total_requests = ServiceRequest.objects.count()
    
    # Recent activities
    recent_users = CustomUser.objects.order_by('-date_joined')[:5]
    recent_bookings = Booking.objects.order_by('-booking_date')[:5]
    recent_services = Service.objects.order_by('-created_at')[:5]
    
    context = {
        'total_users': total_users,
        'total_providers': total_providers,
        'total_customers': total_customers,
        'total_services': total_services,
        'total_bookings': total_bookings,
        'total_requests': total_requests,
        'recent_users': recent_users,
        'recent_bookings': recent_bookings,
        'recent_services': recent_services,
    }
    
    return render(request, 'admin.html', context)

# =======================================================
# 4. Profile Management Views
# =======================================================

@login_required
def profile(request):
    """
    Display user profile, stats, and last 10 activities (bookings, reviews).
    """
    # NOTE: Since CustomUser is AUTH_USER_MODEL, the original logic fetching UserProfile is now redundant 
    # if the main data is on CustomUser. However, since the code contained both, 
    # we use the UserProfile model (if it exists) to prevent breaking the code flow.
    # It assumes request.user is an instance of CustomUser, but fetches UserProfile for consistency
    # with the provided fragments.
    
    # Safely get UserProfile (or the corresponding CustomUser data)
    # The provided fragments heavily rely on the separate UserProfile model linked to the default User model,
    # which conflicts with the CustomUser model used everywhere else.
    # To minimize changes, we assume the original intent was to use request.user directly
    # for most data and link to a separate UserProfile model for provider/settings data.
    
    # Using request.user (CustomUser) for core data as established in models.py merge.
    user = request.user 
    
    # Re-using the UserProfile object for compatibility with the forms/views that still use it
    try:
        user_profile = UserProfile.objects.get(user=user)
    except UserProfile.DoesNotExist:
        # Create a placeholder UserProfile if it doesn't exist to prevent crash
        user_profile = UserProfile.objects.create(user=user, user_type=user.user_type)
        
    
    # Get user bookings
    if user.user_type == 'customer':
        bookings = Booking.objects.filter(customer=user).order_by('-booking_date')
    else:
        bookings = Booking.objects.filter(provider=user).order_by('-booking_date')
    
    # Get reviews
    if user.user_type == 'customer':
        reviews = Review.objects.filter(customer=user).order_by('-created_at')
    else:
        reviews = Review.objects.filter(provider=user).order_by('-created_at')
    
    # Get notifications
    notifications = Notification.objects.filter(user=user, is_read=False).order_by('-created_at')
    
    # Calculate stats
    total_bookings = bookings.count()
    active_bookings = bookings.filter(status__in=['confirmed', 'in_progress']).count()
    completed_bookings = bookings.filter(status='completed').count()
    
    total_spent = 0
    total_earned = 0
    if user.user_type == 'customer':
        total_spent = bookings.filter(status='completed').aggregate(
            total=models.Sum('total_price')
        )['total'] or 0
    else:
        total_earned = bookings.filter(status='completed').aggregate(
            total=models.Sum('total_price')
        )['total'] or 0
    
    # Provider rating
    provider_rating = 0
    review_count = 0
    if user.user_type == 'provider':
        provider_rating = Review.objects.filter(provider=user).aggregate(
            avg_rating=Avg('rating')
        )['avg_rating'] or 0
        review_count = reviews.count()
    
    context = {
        'user_profile': user_profile, # For compatibility with old templates
        'user': user, # CustomUser instance
        'bookings': bookings[:10],
        'reviews': reviews[:10],
        'notifications': notifications[:10],
        'total_bookings': total_bookings,
        'active_bookings': active_bookings,
        'completed_bookings': completed_bookings,
        'total_spent': total_spent,
        'total_earned': total_earned,
        'provider_rating': round(provider_rating, 1),
        'review_count': review_count,
    }
    
    return render(request, 'profile.html', context)

@login_required
def profile_edit(request):
    """
    Edit user's basic info (UserForm) and profile info (UserProfileForm).
    """
    user_profile = get_object_or_404(UserProfile, user=request.user)
    
    if request.method == 'POST':
        # NOTE: UserForm uses the default User model, this might cause issues if CustomUser is used
        # For minimal change, we use request.user instance directly.
        user_form = UserForm(request.POST, instance=request.user) 
        profile_form = UserProfileForm(request.POST, instance=user_profile)
        
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('profile')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        user_form = UserForm(instance=request.user)
        profile_form = UserProfileForm(instance=user_profile)
    
    context = {
        'user_form': user_form,
        'profile_form': profile_form,
        'user_profile': user_profile,
    }
    
    return render(request, 'profile_edit.html', context)

@login_required
def profile_change_password(request):
    """
    Change user password, requires current password validation.
    """
    if request.method == 'POST':
        form = PasswordChangeForm(request.POST)
        if form.is_valid():
            current_password = form.cleaned_data['current_password']
            new_password = form.cleaned_data['new_password']
            confirm_password = form.cleaned_data['confirm_password']
            
            if not request.user.check_password(current_password):
                messages.error(request, 'Current password is incorrect.')
            elif new_password != confirm_password:
                messages.error(request, 'New passwords do not match.')
            else:
                request.user.set_password(new_password)
                request.user.save()
                update_session_auth_hash(request, request.user) # Keeps user logged in
                messages.success(request, 'Password changed successfully!')
                return redirect('profile')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = PasswordChangeForm()
    
    context = {
        'form': form,
    }
    
    return render(request, 'profile_change_password.html', context)

@login_required
def profile_bookings(request):
    """
    View user's bookings with filtering and pagination.
    """
    user = request.user
    
    if user.user_type == 'customer':
        bookings = Booking.objects.filter(customer=user).order_by('-booking_date')
    else:
        bookings = Booking.objects.filter(provider=user).order_by('-booking_date')
    
    # Filter by status
    status_filter = request.GET.get('status', 'all')
    if status_filter != 'all':
        bookings = bookings.filter(status=status_filter)
    
    # Pagination
    paginator = Paginator(bookings, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'status_filter': status_filter,
        'total_bookings': bookings.count(),
    }
    
    return render(request, 'profile_bookings.html', context)

@login_required
def profile_reviews(request):
    """
    View user's reviews given (customer) or received (provider).
    """
    user = request.user
    
    if user.user_type == 'customer':
        reviews = Review.objects.filter(customer=user).order_by('-created_at')
    else:
        reviews = Review.objects.filter(provider=user).order_by('-created_at')
    
    # Calculate average rating for providers
    rating_stats = None
    if user.user_type == 'provider':
        rating_stats = reviews.aggregate(
            avg_rating=Avg('rating'),
            total_reviews=Count('id')
        )
    
    # Pagination
    paginator = Paginator(reviews, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'rating_stats': rating_stats,
    }
    
    return render(request, 'profile_reviews.html', context)

@login_required
def profile_notifications(request):
    """
    View all notifications for the user with pagination and mark all as read feature.
    """
    notifications = Notification.objects.filter(user=request.user).order_by('-created_at')
    
    # Mark as read if specified
    if request.GET.get('mark_read') == 'all':
        notifications.update(is_read=True)
        messages.success(request, 'All notifications marked as read.')
        return redirect('profile_notifications')
    
    # Pagination
    paginator = Paginator(notifications, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'unread_count': notifications.filter(is_read=False).count(),
    }
    
    return render(request, 'profile_notifications.html', context)

@login_required
def mark_notification_read(request, notification_id):
    """
    Mark a specific notification as read and redirect back to notifications page.
    """
    notification = get_object_or_404(Notification, id=notification_id, user=request.user)
    notification.is_read = True
    notification.save()
    
    messages.success(request, 'Notification marked as read.')
    return redirect('profile_notifications')

@login_required
def profile_settings(request):
    """
    Update user profile settings (notifications, visibility, etc.).
    """
    user_profile = get_object_or_404(UserProfile, user=request.user)
    
    if request.method == 'POST':
        profile_form = UserProfileForm(request.POST, instance=user_profile)
        if profile_form.is_valid():
            profile_form.save()
            messages.success(request, 'Settings updated successfully!')
            return redirect('profile_settings')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        profile_form = UserProfileForm(instance=user_profile)
    
    context = {
        'profile_form': profile_form,
    }
    
    return render(request, 'profile_settings.html', context)

@login_required
def delete_account(request):
    """
    Soft delete user account (set is_active=False).
    """
    if request.method == 'POST':
        # Soft delete - mark user as inactive instead of actually deleting
        request.user.is_active = False
        request.user.save()
        
        # Logout user
        logout(request)
        
        messages.success(request, 'Your account has been deleted successfully.')
        return redirect('index')
    
    return render(request, 'delete_account_confirm.html')

# =======================================================
# 5. Service & Booking Views
# =======================================================

# views.py - Add Service View (Fixed)
@login_required
def add_service(request):
    """
    Add service logic: Only providers can add services.
    """
    if request.user.user_type != 'provider':
        messages.error(request, 'Only service providers can add services.')
        return redirect('dashboard')
    
    categories = ServiceCategory.objects.all()
    
    if request.method == 'POST':
        try:
            # Validate required fields
            required_fields = ['category', 'title', 'description', 'price', 'location', 'experience', 'availability']
            for field in required_fields:
                if not request.POST.get(field):
                    messages.error(request, f'Please fill in the {field.replace("_", " ")} field.')
                    return render(request, 'add_service.html', {'categories': categories})   

             # Get category
            category_id = request.POST.get('category')
            try:
                category = ServiceCategory.objects.get(id=category_id)
            except ServiceCategory.DoesNotExist:
                messages.error(request, 'Invalid category selected.')
                return render(request, 'add_service.html', {'categories': categories})
            
            # Create service - is_active=True for immediate visibility
            service = Service.objects.create(
                provider=request.user,
                category_id=request.POST.get('category'),
                title=request.POST.get('title'),
                description=request.POST.get('description'),
                price_range=request.POST.get('price'),
                location=request.POST.get('location'),
                experience=request.POST.get('experience'),
                availability=request.POST.get('availability'),
                is_active=True  # Directly active for demo, you can set to False for admin approval
            )
            
            # Handle image uploads
            images = request.FILES.getlist('images')
            for image in images:
                if image.size > 5 * 1024 * 1024:  # 5MB limit
                    messages.warning(request, f'Image {image.name} is too large. Skipped.')
                    continue
                ServiceImage.objects.create(service=service, image=image)
            
            # Send notification to admin (optional)
            try:
                admin_users = CustomUser.objects.filter(user_type='admin')
                for admin in admin_users:
                    send_mail(
                        'New Service Added',
                        f'''
Hello Admin,

A new service has been added to FixFinder:

Service: {service.title}
Provider: {service.provider.get_full_name()}
Category: {service.category.name}
Location: {service.location}

FixFinder Admin
                        ''',
                        settings.DEFAULT_FROM_EMAIL,
                        [admin.email],
                        fail_silently=True,
                    )
            except Exception as e:
                print(f"Admin notification email failed: {e}")
            
            # Create notification for provider
            Notification.objects.create(
                user=request.user,
                title='Service Added Successfully',
                message=f'Your service "{service.title}" has been added successfully.',
                notification_type='service_added'
            )
            
            messages.success(request, 'Service added successfully! It is now visible to customers.')
            return redirect('dashboard')
            
        except Exception as e:
            messages.error(request, f'Error adding service: {str(e)}')
            return render(request, 'add_service.html', {'categories': categories})
    
    return render(request, 'add_service.html', {'categories': categories})

@login_required
def book_service(request, service_id):
    """
    Handle service booking: create booking, send emails/notifications.
    """
    service = get_object_or_404(Service, id=service_id, is_active=True)
    
    if request.method == 'POST':
        try:
            service_date = request.POST.get('service_date')
            service_time = request.POST.get('service_time')
            address = request.POST.get('address')
            special_instructions = request.POST.get('special_instructions', '')
            
            # Price extraction and validation (assuming price_range is a string like '₹1000-₹2000')
            price_str = service.price_range.replace('₹', '').split('-')[0].strip()
            try:
                total_price = float(price_str)
            except ValueError:
                total_price = 0.0  # Default or handle error
            
            if not all([service_date, service_time, address]):
                messages.error(request, 'Please fill all required fields.')
                return redirect('service_detail', service_id=service_id)
            
            # Create booking
            booking = Booking.objects.create(
                customer=request.user,
                service=service,
                provider=service.provider,
                service_name=service.title, # Redundant field but kept for compatibility
                service_description=service.description, # Redundant field but kept for compatibility
                service_date=service_date,
                service_time=service_time,
                customer_address=address, # Using customer_address field name from models
                total_price=total_price,  # FIXED: Changed from 'price' to 'total_price'
                special_instructions=special_instructions,
                status='confirmed'
            )
            
            # =======================================================
            # EMAIL NOTIFICATION SYSTEM - CUSTOMER
            # =======================================================
            try:
                # Customer Email - Booking Confirmation
                customer_subject = f'✅ Booking Confirmed: {service.title} - FixFinder'
                customer_message = f"""
Hello {request.user.first_name},

🎉 Your service booking has been confirmed!

📋 **Booking Details:**
• Service: {service.title}
• Provider: {service.provider.get_full_name()}
• Date: {service_date}
• Time: {service_time}
• Total Amount: ₹{total_price}
• Booking ID: #{booking.id}

📍 **Service Address:**
{address}

📝 **Special Instructions:**
{special_instructions if special_instructions else 'None provided'}

📞 **Provider Contact:**
• Name: {service.provider.get_full_name()}
• Phone: {service.provider.phone}
• Email: {service.provider.email}

💡 **Next Steps:**
1. The provider will contact you within 24 hours to confirm the appointment
2. Keep your phone accessible for communication
3. Have the service area ready at the scheduled time

If you need to modify or cancel your booking, please contact the provider directly.

Thank you for choosing FixFinder! 🛠️

Best regards,
FixFinder Team
                """
                
                send_mail(
                    customer_subject,
                    customer_message.strip(),
                    settings.DEFAULT_FROM_EMAIL,
                    [request.user.email],
                    fail_silently=False,
                )
                print(f"✅ Customer email sent to: {request.user.email}")
                
            except Exception as e:
                print(f"❌ Customer email failed: {e}")
                # Don't show error to user, just log it
            
            # =======================================================
            # EMAIL NOTIFICATION SYSTEM - PROVIDER
            # =======================================================
            try:
                # Provider Email - New Booking Notification
                provider_subject = f'🎉 New Booking: {service.title} - FixFinder'
                provider_message = f"""
Hello {service.provider.first_name},

🎊 You have received a new booking!

📋 **Booking Details:**
• Service: {service.title}
• Customer: {request.user.get_full_name()}
• Date: {service_date}
• Time: {service_time}
• Total Amount: ₹{total_price}
• Booking ID: #{booking.id}

👤 **Customer Information:**
• Name: {request.user.get_full_name()}
• Phone: {request.user.phone}
• Email: {request.user.email}

📍 **Service Location:**
{address}

📝 **Customer Instructions:**
{special_instructions if special_instructions else 'No special instructions'}

🚀 **Action Required:**
1. Contact the customer within 24 hours to confirm the appointment
2. Discuss any additional details or requirements
3. Confirm the service timing and location

💼 **Service Details:**
• Category: {service.category.name}
• Your Price: {service.price_range}
• Customer Rating: ⭐ {service.rating}/5

Please ensure you provide excellent service to maintain your high ratings!

Best regards,
FixFinder Team
                """
                
                send_mail(
                    provider_subject,
                    provider_message.strip(),
                    settings.DEFAULT_FROM_EMAIL,
                    [service.provider.email],
                    fail_silently=False,
                )
                print(f"✅ Provider email sent to: {service.provider.email}")
                
            except Exception as e:
                print(f"❌ Provider email failed: {e}")
                # Don't show error to user, just log it
            
            # =======================================================
            # CREATE NOTIFICATIONS IN DATABASE
            # =======================================================
            Notification.objects.create(
                user=request.user,
                title='Booking Confirmed ✅',
                message=f'Your booking for "{service.title}" has been confirmed. Check your email for details.',
                notification_type='booking_confirmed',
                related_booking=booking
            )
            
            Notification.objects.create(
                user=service.provider,
                title='New Booking Received 🎉',
                message=f'New booking from {request.user.get_full_name()} for "{service.title}". Check your email for details.',
                notification_type='new_booking',
                related_booking=booking
            )
            
            messages.success(request, 
                f'✅ Service booked successfully! \n'
                f'• Confirmation email sent to {request.user.email} \n'
                f'• Provider notified about your booking \n'
                f'• Booking ID: #{booking.id}'
            )
            return redirect('dashboard')
            
        except Exception as e:
            messages.error(request, f'❌ Error booking service: {str(e)}')
            return redirect('service_detail', service_id=service_id)
    
    # If GET request, show booking form
    context = {
        'service': service,
        'today': datetime.now().strftime('%Y-%m-%d')  # For date picker min attribute
    }
    return render(request, 'book_service.html', context)


@login_required
def booking_detail(request, booking_id):
    """
    View detailed booking information
    """
    booking = get_object_or_404(Booking, id=booking_id)
    
    # Check if user has permission to view this booking
    if request.user.user_type == 'customer' and booking.customer != request.user:
        messages.error(request, 'You do not have permission to view this booking.')
        return redirect('dashboard')
    
    if request.user.user_type == 'provider' and booking.provider != request.user:
        messages.error(request, 'You do not have permission to view this booking.')
        return redirect('dashboard')
    
    context = {
        'booking': booking,
    }
    return render(request, 'booking_detail.html', context)


@login_required
def cancel_booking(request, booking_id):
    """
    Cancel booking with email notifications to both customer and provider
    """
    booking = get_object_or_404(Booking, id=booking_id)
    
    # Check if user has permission to cancel this booking
    if booking.customer != request.user and booking.provider != request.user:
        messages.error(request, 'You do not have permission to cancel this booking.')
        return redirect('dashboard')
    
    # Check if booking can be cancelled
    if booking.status in ['cancelled', 'completed']:
        messages.error(request, f'This booking is already {booking.status} and cannot be cancelled.')
        return redirect('booking_detail', booking_id=booking_id)
    
    if request.method == 'POST':
        try:
            cancellation_reason = request.POST.get('cancellation_reason')
            additional_comments = request.POST.get('additional_comments', '')
            
            if not cancellation_reason:
                messages.error(request, 'Please provide a cancellation reason.')
                return redirect('cancel_booking', booking_id=booking_id)
            
            # Update booking status
            old_status = booking.status
            booking.status = 'cancelled'
            booking.save()
            
            # =======================================================
            # EMAIL NOTIFICATION SYSTEM - CUSTOMER
            # =======================================================
            try:
                customer_subject = f'❌ Booking Cancelled: {booking.service.title if booking.service else booking.service_name} - FixFinder'
                customer_message = f"""
Hello {booking.customer.first_name},

Your booking has been cancelled.

📋 **Booking Details:**
• Service: {booking.service.title if booking.service else booking.service_name}
• Provider: {booking.provider.get_full_name()}
• Date: {booking.service_date}
• Time: {booking.service_time}
• Booking ID: #{booking.id}

📝 **Cancellation Details:**
• Reason: {dict(CANCELLATION_REASONS).get(cancellation_reason, cancellation_reason)}
• Additional Comments: {additional_comments if additional_comments else 'None provided'}
• Cancelled By: {request.user.get_full_name()}
• Cancellation Time: {timezone.now().strftime("%Y-%m-%d %H:%M")}

💰 **Refund Information:**
Based on our cancellation policy, your refund will be processed within 3-5 business days.

If you have any questions or need to rebook, please contact our support team.

We hope to serve you better in the future!

Best regards,
FixFinder Team
                """
                
                send_mail(
                    customer_subject,
                    customer_message.strip(),
                    settings.DEFAULT_FROM_EMAIL,
                    [booking.customer.email],
                    fail_silently=False,
                )
                print(f"✅ Customer cancellation email sent to: {booking.customer.email}")
                
            except Exception as e:
                print(f"❌ Customer cancellation email failed: {e}")
            
            # =======================================================
            # EMAIL NOTIFICATION SYSTEM - PROVIDER
            # =======================================================
            try:
                provider_subject = f'❌ Booking Cancelled: {booking.service.title if booking.service else booking.service_name} - FixFinder'
                provider_message = f"""
Hello {booking.provider.first_name},

A booking has been cancelled.

📋 **Booking Details:**
• Service: {booking.service.title if booking.service else booking.service_name}
• Customer: {booking.customer.get_full_name()}
• Date: {booking.service_date}
• Time: {booking.service_time}
• Booking ID: #{booking.id}
• Total Amount: ₹{booking.total_price}

📝 **Cancellation Details:**
• Reason: {dict(CANCELLATION_REASONS).get(cancellation_reason, cancellation_reason)}
• Additional Comments: {additional_comments if additional_comments else 'None provided'}
• Cancelled By: {request.user.get_full_name()}
• Cancellation Time: {timezone.now().strftime("%Y-%m-%d %H:%M")}

👤 **Customer Contact:**
• Name: {booking.customer.get_full_name()}
• Phone: {booking.customer.phone}
• Email: {booking.customer.email}

We appreciate your understanding. Keep up the great work!

Best regards,
FixFinder Team
                """
                
                send_mail(
                    provider_subject,
                    provider_message.strip(),
                    settings.DEFAULT_FROM_EMAIL,
                    [booking.provider.email],
                    fail_silently=False,
                )
                print(f"✅ Provider cancellation email sent to: {booking.provider.email}")
                
            except Exception as e:
                print(f"❌ Provider cancellation email failed: {e}")
            
            # =======================================================
            # CREATE NOTIFICATIONS IN DATABASE
            # =======================================================
            Notification.objects.create(
                user=booking.customer,
                title='Booking Cancelled ❌',
                message=f'Your booking for "{booking.service.title if booking.service else booking.service_name}" has been cancelled.',
                notification_type='booking_cancelled',
                related_booking=booking
            )
            
            Notification.objects.create(
                user=booking.provider,
                title='Booking Cancelled ❌',
                message=f'Booking from {booking.customer.get_full_name()} for "{booking.service.title if booking.service else booking.service_name}" has been cancelled.',
                notification_type='booking_cancelled',
                related_booking=booking
            )
            
            messages.success(request, 
                f'✅ Booking cancelled successfully! \n'
                f'• Cancellation emails sent to both parties \n'
                f'• Refund will be processed as per policy \n'
                f'• Booking ID: #{booking.id}'
            )
            return redirect('dashboard')
            
        except Exception as e:
            messages.error(request, f'❌ Error cancelling booking: {str(e)}')
            return redirect('cancel_booking', booking_id=booking_id)
    
    # GET request - show cancellation form
    context = {
        'booking': booking,
    }
    return render(request, 'cancel_booking.html', context)

# Cancellation reasons dictionary
CANCELLATION_REASONS = {
    'change_of_plans': 'Change of plans',
    'found_another_provider': 'Found another service provider',
    'service_no_longer_needed': 'Service no longer needed',
    'scheduling_conflict': 'Scheduling conflict',
    'price_concern': 'Price concern',
    'personal_reasons': 'Personal reasons',
    'other': 'Other',
}

# =======================================================
# 6. Service Request Views
# =======================================================

def create_provider_notifications(service_request):
    """
    Utility function to create notifications for relevant service providers.
    """
    # NOTE: UserProfile is assumed to exist and is linked to the User model.
    
    # Filter by service category and location (city/area)
    relevant_providers = CustomUser.objects.filter(
        user_type='provider',
        # Check if the provider's CustomUser location field contains the request location (city)
        location__icontains=service_request.location.split(',')[0].strip(),
        # Check if the provider is registered for the service category
        service_categories__in=[service_request.category.id]
    ).distinct()
    
    # Also send emails to relevant providers
    for provider in relevant_providers:
        Notification.objects.create(
            user=provider,
            title=f"New Service Request: {service_request.title}",
            message=f"A new {service_request.get_category_display()} request has been posted in {service_request.location}.",
            notification_type='service_request',
            # related_service_request is not in Notification model, using related_id for generic linking
            related_booking=None 
        )
        
        # Send Email notification to providers (Redundant email logic removed, kept the simpler notification)


# views.py - Post Service Request View (Fixed)
@login_required
def post_service_request(request):
    """
    Submit a detailed service request.
    """
    categories = ServiceCategory.objects.all()
    
    if request.method == 'POST':
        form = ServiceRequestForm(request.POST)
        if form.is_valid():
            service_request = form.save(commit=False)
            service_request.customer = request.user
            
            # Auto-fill contact info if available
            if not service_request.contact_name:
                service_request.contact_name = request.user.get_full_name() or request.user.username
            if not service_request.contact_phone and request.user.phone:
                service_request.contact_phone = request.user.phone
            if not service_request.location and request.user.location:
                service_request.location = request.user.location

            service_request.save()
            
            # Create notification for relevant service providers
            create_provider_notifications(service_request)
            
            # Send email notifications
            send_service_request_emails(service_request)
            
            messages.success(request, 'Your service request has been posted successfully! Service providers in your area will be notified.')
            return redirect('service_requests')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        # Initial data based on user profile
        initial_data = {
            'contact_name': request.user.get_full_name() or request.user.username,
            'contact_phone': request.user.phone or '',
            'location': request.user.location or '',
        }
        form = ServiceRequestForm(initial=initial_data)
    
    context = {
        'form': form,
        'categories': categories
    }
    return render(request, 'post_service_request.html', context)

def send_service_request_emails(service_request):
    """
    Send email notifications for new service request
    """
    # 1. Send confirmation email to customer
    send_customer_confirmation_email(service_request)
    
    # 2. Send notifications to relevant providers
    send_provider_notification_emails(service_request)

def send_customer_confirmation_email(service_request):
    """
    Send confirmation email to customer
    """
    try:
        customer_subject = '✅ Service Request Posted Successfully - FixFinder'
        customer_message = f"""
Hello {service_request.customer.first_name},

🎉 Your service request has been posted successfully!

📋 **Request Details:**
• Service: {service_request.title}
• Category: {service_request.category.name}
• Location: {service_request.location}
• Budget: {service_request.budget}
• Request ID: #{service_request.id}
• Posted on: {service_request.created_at.strftime('%d %b %Y at %I:%M %p')}

👥 **What Happens Next:**
1. Service providers in your area will be notified about your request
2. Providers will review your request and send responses
3. You'll receive notifications when providers respond
4. You can review provider profiles and choose the best fit

📞 **Providers will contact you at:**
• Name: {service_request.contact_name}
• Phone: {service_request.contact_phone}

🔍 **To view responses:**
1. Login to your FixFinder account
2. Go to "My Service Requests"
3. Click on your request to see provider responses

We'll notify you as soon as providers start responding!

Thank you for choosing FixFinder! 🛠️

Best regards,
FixFinder Team
        """
        
        send_mail(
            customer_subject,
            customer_message.strip(),
            settings.DEFAULT_FROM_EMAIL,
            [service_request.customer.email],
            fail_silently=False,
        )
        print(f"✅ Customer confirmation email sent to: {service_request.customer.email}")
        
    except Exception as e:
        print(f"❌ Customer confirmation email failed: {e}")

def send_provider_notification_emails(service_request):
    """
    Send notification emails to relevant providers
    """
    # Get providers in same location and category
    relevant_providers = CustomUser.objects.filter(
        user_type='provider',
        location__icontains=service_request.location.split(',')[0].strip() if service_request.location else '',
        service_categories=service_request.category
    ).distinct()
    
    provider_count = 0
    for provider in relevant_providers:
        try:
            provider_subject = f'🎯 New Service Request: {service_request.title} - FixFinder'
            provider_message = f"""
Hello {provider.first_name},

🚀 A new service request matching your expertise has been posted in your area!

📋 **Service Request Details:**
• Service: {service_request.title}
• Category: {service_request.category.name}
• Location: {service_request.location}
• Budget: {service_request.budget}
• Request ID: #{service_request.id}
• Posted: {service_request.created_at.strftime('%d %b %Y at %I:%M %p')}

📍 **Customer Location:**
{service_request.location}

💰 **Budget Range:**
{service_request.budget}

📝 **Service Description:**
{service_request.description}

👤 **Customer Contact Information:**
• Name: {service_request.contact_name}
• Phone: {service_request.contact_phone}

🎯 **Why This Request Matches You:**
• Category: {service_request.category.name} matches your expertise
• Location: {service_request.location} is in your service area
• You have experience in this service type

🚀 **How to Respond:**
1. Login to your FixFinder account
2. Go to "Available Requests" section
3. Find this request (ID: #{service_request.id})
4. Click "View Details & Respond"
5. Send your proposal to the customer

💡 **Quick Response Tip:**
• Respond within 24 hours for better chances
• Provide clear pricing and timeline
• Highlight your relevant experience

Don't miss this opportunity! The customer is waiting for responses.

Best regards,
FixFinder Team
            """
            
            send_mail(
                provider_subject,
                provider_message.strip(),
                settings.DEFAULT_FROM_EMAIL,
                [provider.email],
                fail_silently=True,
            )
            provider_count += 1
            print(f"✅ Provider notification sent to: {provider.email}")
            
        except Exception as e:
            print(f"❌ Provider email failed for {provider.email}: {e}")
    
    print(f"📧 Total {provider_count} providers notified about service request #{service_request.id}")

def create_provider_notifications(service_request):
    """
    Create in-app notifications for relevant service providers
    """
    # Get providers in same location and category
    relevant_providers = CustomUser.objects.filter(
        user_type='provider',
        location__icontains=service_request.location.split(',')[0].strip() if service_request.location else '',
        service_categories=service_request.category
    ).distinct()
    
    # Create notifications for each provider
    for provider in relevant_providers:
        Notification.objects.create(
            user=provider,
            title=f"New Service Request: {service_request.title}",
            message=f"A new {service_request.category.name} request has been posted in {service_request.location}.",
            notification_type='service_request'
        )
    
    # Create notification for customer
    Notification.objects.create(
        user=service_request.customer,
        title="Service Request Posted Successfully",
        message=f"Your service request '{service_request.title}' has been posted. Providers will be notified.",
        notification_type='request_posted'
    )



@login_required
def service_requests(request):
    """View user's service requests"""
    user_requests = ServiceRequest.objects.filter(customer=request.user).order_by('-created_at')
    
    context = {
        'service_requests': user_requests,
    }
    return render(request, 'service_requests.html', context)

@login_required
def service_request_detail(request, request_id):
    """View detailed service request and responses, allowing providers to respond."""
    # CustomUser is used instead of User, but the provided code relied on request.user.profile.user_type
    
    # Logic is modified to handle CustomUser (request.user) directly
    service_request = get_object_or_404(ServiceRequest, id=request_id, customer=request.user)
    responses = service_request.responses.all().order_by('-created_at')
    
    is_provider = request.user.user_type == 'provider'
    
    if request.method == 'POST' and is_provider:
        response_form = ServiceResponseForm(request.POST)
        if response_form.is_valid():
            response = response_form.save(commit=False)
            response.service_request = service_request
            response.provider = request.user # CustomUser
            response.save()
            
            # Create notification for customer
            Notification.objects.create(
                user=service_request.customer,
                title=f"New Response for Your Service Request",
                message=f"{request.user.get_full_name()} has responded to your service request.",
                notification_type='response',
                related_booking=None # Generic link
            )
            
            messages.success(request, 'Your response has been sent to the customer.')
            return redirect('service_request_detail', request_id=request_id)
        else:
            messages.error(request, 'Please correct the response errors.')
    else:
        response_form = ServiceResponseForm()
    
    context = {
        'service_request': service_request,
        'responses': responses,
        'response_form': response_form if is_provider else None,
        'is_provider': is_provider
    }
    return render(request, 'service_request_detail.html', context)

@login_required
def available_requests(request):
    """View available service requests for providers based on location and category."""
    user = request.user
    
    if user.user_type != 'provider':
        messages.error(request, 'This page is only available for service providers.')
        return redirect('index')
    
    # Filter requests by provider's registered categories and location (using CustomUser fields)
    available_requests = ServiceRequest.objects.filter(
        status='open',
        location__icontains=user.location.split(',')[0] or '',
        category__in=user.service_categories.all()
    ).exclude(
        Q(customer=user) | Q(responses__provider=user)
    ).distinct().order_by('-created_at')
    
    context = {
        'available_requests': available_requests,
        'user': user,
    }
    return render(request, 'available_requests.html', context)

@login_required
def update_request_status(request, request_id, status):
    """Update service request status (only customer can do this in this view)."""
    service_request = get_object_or_404(ServiceRequest, id=request_id, customer=request.user)
    
    # Ensure status is valid
    valid_statuses = dict(ServiceRequest.STATUS_CHOICES).keys()
    
    if status in valid_statuses:
        service_request.status = status
        service_request.save()
        messages.success(request, f'Service request status updated to {status}.')
    else:
        messages.error(request, 'Invalid status.')
    
    return redirect('service_request_detail', request_id=request_id)


# =======================================================
# 7. Communication Views
# =======================================================

@login_required
def contact_provider(request, provider_id):
    """
    Sends an email message to a specific provider.
    """
    provider = get_object_or_404(CustomUser, id=provider_id, user_type__in=['provider', 'admin'])
    
    if request.method == 'POST':
        message = request.POST.get('message')
        service_id = request.POST.get('service_id')
        
        if not message:
            messages.error(request, 'Please enter a message.')
            return redirect('service_detail', service_id=service_id)
        
        # Send email notification to provider
        try:
            send_mail(
                f'New Message from {request.user.get_full_name()} (FixFinder)',
                f'''
Hello {provider.first_name},

You have received a new message from {request.user.get_full_name()} (Customer):

"{message}"

Customer Details:
Phone: {request.user.phone}
Email: {request.user.email}

If this is related to a specific service, the ID is: {service_id if service_id else 'N/A'}

FixFinder Team
                ''',
                settings.DEFAULT_FROM_EMAIL,
                [provider.email],
                fail_silently=False,
            )
            
            # Send copy to customer
            send_mail(
                'Message Sent Successfully',
                f'Your message has been sent to {provider.get_full_name()} regarding service ID {service_id if service_id else "N/A"}.',
                settings.DEFAULT_FROM_EMAIL,
                [request.user.email],
                fail_silently=False,
            )
            
            messages.success(request, 'Message sent successfully! The provider will contact you soon.')
            
        except Exception as e:
            print(f"Contact email failed: {e}")
            messages.error(request, 'Failed to send message. Please check system logs for details.')
        
        return redirect('dashboard')
    
    # Fallback if accessed via GET
    return redirect('services')

# =======================================================
# 8. API Views
# =======================================================

@login_required
def api_get_notifications(request):
    """Get unread notifications count for AJAX"""
    unread_count = Notification.objects.filter(user=request.user, is_read=False).count()
    return JsonResponse({'unread_count': unread_count})

@login_required
def api_mark_notification_read(request, notification_id):
    """Mark notification as read"""
    notification = get_object_or_404(Notification, id=notification_id, user=request.user)
    notification.is_read = True
    notification.save()
    return JsonResponse({'success': True})



# views.py
@login_required
def profile_notifications(request):
    """
    View all notifications for the user with pagination
    """
    notifications = Notification.objects.filter(user=request.user).order_by('-created_at')
    
    # Mark all as read if specified
    if request.GET.get('mark_read') == 'all':
        updated_count = notifications.update(is_read=True)
        messages.success(request, f'Marked {updated_count} notifications as read.')
        return redirect('profile_notifications')
    
    # Pagination
    paginator = Paginator(notifications, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'unread_count': notifications.filter(is_read=False).count(),
    }
    
    return render(request, 'profile_notifications.html', context)

@login_required
def mark_notification_read(request, notification_id):
    """
    Mark a specific notification as read and redirect back
    """
    notification = get_object_or_404(Notification, id=notification_id, user=request.user)
    notification.is_read = True
    notification.save()
    
    messages.success(request, 'Notification marked as read.')
    
    # Redirect back to the same page or to notifications list
    next_url = request.GET.get('next', 'profile_notifications')
    return redirect(next_url)



# views.py - Edit Service View
@login_required
def edit_service(request, service_id):
    """
    Edit existing service - only service owner can edit
    """
    service = get_object_or_404(Service, id=service_id, provider=request.user)
    categories = ServiceCategory.objects.all()
    
    if request.method == 'POST':
        try:
            # Validate required fields
            required_fields = ['category', 'title', 'description', 'price', 'location', 'experience', 'availability']
            for field in required_fields:
                if not request.POST.get(field):
                    messages.error(request, f'Please fill in the {field.replace("_", " ")} field.')
                    return render(request, 'edit_service.html', {
                        'service': service,
                        'categories': categories
                    })
            
            # Update service
            service.category_id = request.POST.get('category')
            service.title = request.POST.get('title')
            service.description = request.POST.get('description')
            service.price_range = request.POST.get('price')
            service.location = request.POST.get('location')
            service.experience = request.POST.get('experience')
            service.availability = request.POST.get('availability')
            service.is_active = request.POST.get('is_active') == 'true'
            service.save()
            
            # Handle new image uploads
            images = request.FILES.getlist('images')
            for image in images:
                if image.size > 5 * 1024 * 1024:  # 5MB limit
                    messages.warning(request, f'Image {image.name} is too large. Skipped.')
                    continue
                ServiceImage.objects.create(service=service, image=image)
            
            # Handle image deletions
            delete_image_ids = request.POST.getlist('delete_images')
            for image_id in delete_image_ids:
                try:
                    image = ServiceImage.objects.get(id=image_id, service=service)
                    image.delete()
                except ServiceImage.DoesNotExist:
                    pass
            
            messages.success(request, f'Service "{service.title}" updated successfully!')
            return redirect('dashboard')
            
        except Exception as e:
            messages.error(request, f'Error updating service: {str(e)}')
            return render(request, 'edit_service.html', {
                'service': service,
                'categories': categories
            })
    
    return render(request, 'edit_service.html', {
        'service': service,
        'categories': categories
    })




# views.py - Delete Service View
@login_required
def delete_service(request, service_id):
    """
    Delete service - only service owner can delete
    """
    service = get_object_or_404(Service, id=service_id, provider=request.user)
    
    if request.method == 'POST':
        service_title = service.title
        service.delete()
        messages.success(request, f'Service "{service_title}" deleted successfully!')
        return redirect('dashboard')
    
    return render(request, 'delete_service_confirm.html', {'service': service})





@login_required
def provider_profile(request):
    """
    Provider profile management page
    """
    # Check if user is a provider
    if not hasattr(request.user, 'user_type') or request.user.user_type != 'provider':
        messages.error(request, 'You need to be a service provider to access this page.')
        return redirect('dashboard')
    
    # Get provider profile data
    try:
        provider_profile = request.user.providerprofile
    except:
        # Create a default provider profile if it doesn't exist
        provider_profile = None
    
    context = {
        'provider_profile': provider_profile,
        'services': getattr(provider_profile, 'services', []),
        'completed_jobs': getattr(provider_profile, 'completed_jobs', 0),
        'avg_rating': getattr(provider_profile, 'avg_rating', 4.8),
        'response_rate': getattr(provider_profile, 'response_rate', '95%'),
    }
    
    return render(request, 'provider_profile.html', context)




@login_required
def contact_provider(request, provider_id):
    """
    Contact provider form and functionality
    """
    provider = get_object_or_404(CustomUser, id=provider_id, user_type='provider')
    
    if request.method == 'POST':
        message = request.POST.get('message', '').strip()
        service_id = request.POST.get('service_id')
        
        if not message:
            messages.error(request, 'Please enter your message.')
            return render(request, 'contact_provider.html', {'provider': provider})
        
        # Send email to provider
        try:
            send_mail(
                f'New Message from {request.user.get_full_name()} - FixFinder',
                f'''
Message from: {request.user.get_full_name()}
Email: {request.user.email}
Phone: {request.user.phone}

Message:
{message}

Service ID: {service_id if service_id else 'N/A'}

Please respond to the customer at your earliest convenience.

FixFinder Team
                ''',
                settings.DEFAULT_FROM_EMAIL,
                [provider.email],
                fail_silently=False,
            )
            
            # Send confirmation to customer
            send_mail(
                'Message Sent Successfully - FixFinder',
                f'''
Your message has been sent to {provider.get_full_name()}.

Message: {message}

The provider will contact you soon.

Thank you,
FixFinder Team
                ''',
                settings.DEFAULT_FROM_EMAIL,
                [request.user.email],
                fail_silently=True,
            )
            
            messages.success(request, f'Message sent to {provider.get_full_name()} successfully!')
            return redirect('dashboard')
            
        except Exception as e:
            messages.error(request, 'Failed to send message. Please try again.')
    
    return render(request, 'contact_provider.html', {
        'provider': provider,
        'service_id': request.GET.get('service', '')
    })


@login_required
def add_review(request, booking_id):
    """
    Add review for completed booking
    """
    booking = get_object_or_404(Booking, id=booking_id, customer=request.user, status='completed')
    
    # Check if review already exists
    if hasattr(booking, 'review'):
        messages.error(request, 'You have already reviewed this booking.')
        return redirect('booking_detail', booking_id=booking_id)
    
    if request.method == 'POST':
        rating = request.POST.get('rating')
        comment = request.POST.get('comment', '').strip()
        
        if not rating:
            messages.error(request, 'Please select a rating.')
            return render(request, 'add_review.html', {'booking': booking})
        
        try:
            # Create review
            review = Review.objects.create(
                customer=request.user,
                provider=booking.provider,
                service=booking.service,
                booking=booking,
                rating=int(rating),
                comment=comment,
                is_approved=True
            )
            
            # Send notification to provider
            Notification.objects.create(
                user=booking.provider,
                title='New Review Received ⭐',
                message=f'{request.user.get_full_name()} left a {rating}-star review for your service.',
                notification_type='new_review'
            )
            
            messages.success(request, 'Thank you for your review!')
            return redirect('booking_detail', booking_id=booking_id)
            
        except Exception as e:
            messages.error(request, 'Error submitting review. Please try again.')
    
    return render(request, 'add_review.html', {'booking': booking})




@login_required
def accept_booking(request, booking_id):
    """
    Provider accepts a booking
    """
    if request.user.user_type != 'provider':
        messages.error(request, 'Only providers can accept bookings.')
        return redirect('dashboard')
    
    booking = get_object_or_404(Booking, id=booking_id, provider=request.user, status='pending')
    
    booking.status = 'confirmed'
    booking.save()
    
    # Send notification to customer
    Notification.objects.create(
        user=booking.customer,
        title='Booking Confirmed ✅',
        message=f'{request.user.get_full_name()} has accepted your booking request.',
        notification_type='booking_accepted'
    )
    
    # Send email to customer
    try:
        send_mail(
            'Booking Confirmed - FixFinder',
            f'''
Hello {booking.customer.first_name},

Great news! {request.user.get_full_name()} has accepted your booking request.

Service: {booking.service.title if booking.service else booking.service_name}
Date: {booking.service_date}
Time: {booking.service_time}

The provider will contact you soon to confirm the details.

Thank you for choosing FixFinder!

Best regards,
FixFinder Team
            ''',
            settings.DEFAULT_FROM_EMAIL,
            [booking.customer.email],
            fail_silently=True,
        )
    except Exception as e:
        print(f"Email sending failed: {e}")
    
    messages.success(request, 'Booking accepted successfully!')
    return redirect('booking_detail', booking_id=booking_id)

@login_required
def reject_booking(request, booking_id):
    """
    Provider rejects a booking
    """
    if request.user.user_type != 'provider':
        messages.error(request, 'Only providers can reject bookings.')
        return redirect('dashboard')
    
    booking = get_object_or_404(Booking, id=booking_id, provider=request.user, status='pending')
    
    booking.status = 'cancelled'
    booking.save()
    
    # Send notification to customer
    Notification.objects.create(
        user=booking.customer,
        title='Booking Rejected',
        message=f'{request.user.get_full_name()} has declined your booking request.',
        notification_type='booking_rejected'
    )
    
    messages.success(request, 'Booking rejected successfully!')
    return redirect('profile_bookings')


@login_required
def update_booking_status(request, booking_id):
    """
    Update booking status (in_progress, completed)
    """
    booking = get_object_or_404(Booking, id=booking_id, provider=request.user)
    
    new_status = request.GET.get('status')
    valid_statuses = ['in_progress', 'completed']
    
    if new_status not in valid_statuses:
        messages.error(request, 'Invalid status update.')
        return redirect('booking_detail', booking_id=booking_id)
    
    booking.status = new_status
    booking.save()
    
    # Create notification for customer
    status_text = 'started' if new_status == 'in_progress' else 'completed'
    Notification.objects.create(
        user=booking.customer,
        title=f'Service {status_text.capitalize()}',
        message=f'{request.user.get_full_name()} has {status_text} your service.',
        notification_type='status_update'
    )
    
    messages.success(request, f'Booking status updated to {new_status.replace("_", " ")}!')
    return redirect('booking_detail', booking_id=booking_id)