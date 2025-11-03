from django.db import models
from django.contrib.auth.models import AbstractUser, Group, Permission, User 
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db.models import Avg 
from django.conf import settings # 👈 FIX: Yeh import zaroori hai
import uuid
from django.utils import timezone
from datetime import timedelta

# =======================================================
# 1. Custom User and Profile Models
# =======================================================

# --- CustomUser Definition (AbstractUser se inherit karke) ---
class CustomUser(AbstractUser):
    """
    Custom User model, jo default Django User ko extend karta hai.
    """
    # SystemCheckError Fix: related_name attribute added to avoid clash with default User groups/permissions
    groups = models.ManyToManyField(
        Group,
        verbose_name=('groups'),
        blank=True,
        help_text=('The groups this user belongs to. A user will get all permissions '
                   'granted to each of their groups.'),
        related_name="custom_user_groups",
        related_query_name="custom_user",
    )
    user_permissions = models.ManyToManyField(
        Permission,
        verbose_name=('user permissions'),
        blank=True,
        help_text=('Specific permissions for this user.'),
        related_name="custom_user_permissions",
        related_query_name="custom_user_permission",
    )
    
    USER_TYPE_CHOICES = (
        ('customer', 'Customer'),
        ('provider', 'Service Provider'),
        ('admin', 'Admin'),
    )
    
    user_type = models.CharField(max_length=20, choices=USER_TYPE_CHOICES, default='customer')
    phone = models.CharField(max_length=15)
    location = models.CharField(max_length=255)
    is_verified = models.BooleanField(default=False)
    registration_date = models.DateTimeField(auto_now_add=True)
    
    # Provider-specific fields
    business_name = models.CharField(max_length=255, blank=True, null=True)
    experience = models.CharField(max_length=50, blank=True, null=True)
    service_categories = models.ManyToManyField('ServiceCategory', blank=True)
    
    def __str__(self):
        return f"{self.get_full_name()} ({self.user_type})"

# --- UserProfile Definition ---
class UserProfile(models.Model):
    """
    Extends the default Django User model (using OneToOneField with Django's default User).
    """
    USER_TYPES = [
        ('customer', 'Customer'),
        ('provider', 'Service Provider'),
        ('admin', 'Administrator'),
    ]
    
    # 👈 FIX: E301 error yahan tha. settings.AUTH_USER_MODEL ka use kiya gaya.
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='profile'
    ) 
    user_type = models.CharField(max_length=20, choices=USER_TYPES, default='customer')
    phone = models.CharField(max_length=15, blank=True, null=True)
    location = models.CharField(max_length=100, blank=True, null=True)
    profile_picture = models.ImageField(upload_to='profile_pics/', blank=True, null=True)
    bio = models.TextField(blank=True, null=True)
    date_of_birth = models.DateField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Provider-specific fields
    business_name = models.CharField(max_length=200, blank=True, null=True)
    experience = models.CharField(max_length=100, blank=True, null=True)
    service_categories = models.JSONField(default=list, blank=True) 
    service_area = models.CharField(max_length=200, blank=True, null=True)
    license_number = models.CharField(max_length=100, blank=True, null=True)
    insurance_info = models.TextField(blank=True, null=True)
    is_verified = models.BooleanField(default=False)
    
    # Settings
    email_notifications = models.BooleanField(default=True)
    sms_notifications = models.BooleanField(default=False)
    profile_visible = models.BooleanField(default=True)
    
    def __str__(self):
        return f"{self.user.username} - {self.user_type}"

# =======================================================
# 2. General Models
# =======================================================

class ServiceCategory(models.Model):
    name = models.CharField(max_length=100)
    icon = models.CharField(max_length=50, default='🔧')
    description = models.TextField(blank=True)
    
    def __str__(self):
        return self.name

class Service(models.Model):
    # ForeignKeys mein CustomUser ka use
    provider = models.ForeignKey(CustomUser, on_delete=models.CASCADE, limit_choices_to={'user_type': 'provider'}, related_name='services_provided') 
    category = models.ForeignKey(ServiceCategory, on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    description = models.TextField()
    price_range = models.CharField(max_length=100)
    location = models.CharField(max_length=255)
    experience = models.CharField(max_length=50)
    availability = models.CharField(max_length=50, default='Available')
    rating = models.FloatField(default=0.0)
    reviews_count = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.title
    
    def update_rating(self):
        """Update rating based on reviews"""
        reviews = self.reviews.all()
        if reviews.exists():
            self.rating = reviews.aggregate(Avg('rating'))['rating__avg'] or 0.0
            self.reviews_count = reviews.count()
            self.save()

class ServiceImage(models.Model):
    service = models.ForeignKey(Service, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='service_images/')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Image for {self.service.title}"

class ContactMessage(models.Model):
    """
    Model to store contact messages received from users.
    """
    SUBJECT_CHOICES = [
        ('general', 'General Inquiry'),
        ('support', 'Technical Support'),
        ('billing', 'Billing & Payments'),
        ('provider', 'Become a Service Provider'),
        ('partnership', 'Business Partnership'),
        ('feedback', 'Feedback & Suggestions'),
        ('complaint', 'Complaint'),
        ('other', 'Other'),
    ]
    
    name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=15, blank=True, null=True)
    subject = models.CharField(max_length=20, choices=SUBJECT_CHOICES)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_resolved = models.BooleanField(default=False)
    
    def __str__(self):
        return f"{self.name} - {self.subject}"
    
    class Meta:
        ordering = ['-created_at']

class TeamMember(models.Model):
    """
    Model for managing team members displayed on the website.
    """
    name = models.CharField(max_length=100, default="Team Member")
    position = models.CharField(max_length=100, default="Position")
    description = models.TextField(default="Description coming soon.")
    image = models.ImageField(upload_to='team/', blank=True, null=True)
    initials = models.CharField(max_length=2, default="FF")
    color = models.CharField(max_length=6, default='3B82F6')   # Without # symbol
    order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['order']
    
    def __str__(self):
        return self.name

class PasswordResetToken(models.Model):
    """
    Model for storing and managing password reset tokens.
    """
    # Use CustomUser as the target
    user = models.ForeignKey(
        CustomUser, 
        on_delete=models.CASCADE
    )
    token = models.UUIDField(default=uuid.uuid4, unique=True) 
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)
    
    def save(self, *args, **kwargs):
        if not self.expires_at:
            self.expires_at = timezone.now() + timedelta(hours=24)
        super().save(*args, **kwargs)
    
    def is_valid(self, *args, **kwargs):
        return not self.is_used and timezone.now() < self.expires_at
    
    def __str__(self):
        return f"Password reset for {self.user.email}"

# =======================================================
# 3. Transactional Models
# =======================================================

# models.py में Booking model में ये correction करें:
class Booking(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('in_progress', 'In Progress'), 
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    )
    
    customer = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='customer_bookings')
    provider = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='provider_bookings')
    
    service = models.ForeignKey(Service, on_delete=models.CASCADE, null=True, blank=True) 
    service_name = models.CharField(max_length=200) 
    service_description = models.TextField() 
    
    # 👇 YEH FIELD CORRECT KARNA HAI
    total_price = models.DecimalField(max_digits=10, decimal_places=2)  # 'price' se change kiya 'total_price' mein
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    booking_date = models.DateTimeField(auto_now_add=True)
    service_date = models.DateField()
    service_time = models.TimeField()
    customer_address = models.TextField()  # Template mein 'address' use ho raha hai
    special_instructions = models.TextField(blank=True, null=True)
    
    def __str__(self):
        return f"Booking #{self.id} - {self.service_name or (self.service.title if self.service else 'No Service')}"

class Review(models.Model):
    # ForeignKeys mein CustomUser ko use kiya gaya
    booking = models.OneToOneField(Booking, on_delete=models.CASCADE, related_name='review')
    customer = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='reviews_given') 
    provider = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='reviews_received') 
    
    service = models.ForeignKey(Service, on_delete=models.CASCADE, related_name='reviews')
    
    rating = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_approved = models.BooleanField(default=True) 
    
    def __str__(self):
        return f"Review by {self.customer.get_full_name()} - {self.rating} stars"
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.service.update_rating()
        
    class Meta:
        pass

class ServiceRequest(models.Model):
    # Choices ko merge kiya gaya hai
    CATEGORY_CHOICES = [
        ('plumbing', 'Plumbing'),
        ('electrical', 'Electrical'),
        ('ac-repair', 'AC Repair'),
        ('carpentry', 'Carpentry'),
        ('appliance', 'Appliance Repair'),
        ('cleaning', 'Cleaning'),
        ('painting', 'Painting'),
        ('other', 'Other'),
    ]
    
    URGENCY_CHOICES = [
        ('low', 'Low - Can wait a few days'),
        ('medium', 'Medium - Need within 24 hours'),
        ('high', 'High - Urgent, need ASAP'),
    ]
    
    BUDGET_CHOICES = [
        ('0-500', '₹0 - ₹500'),
        ('500-1000', '₹500 - ₹1,000'),
        ('1000-2000', '₹1,000 - ₹2,000'),
        ('2000-5000', '₹2,000 - ₹5,000'),
        ('5000+', '₹5,000+'),
    ]
    
    STATUS_CHOICES = [
        ('open', 'Open'),
        ('in_progress', 'In Progress'),
        ('assigned', 'Assigned'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    
    # ForeignKeys mein CustomUser ko use kiya gaya
    customer = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='service_requests')
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES) 
    title = models.CharField(max_length=200)
    description = models.TextField()
    location = models.CharField(max_length=100)
    urgency = models.CharField(max_length=20, choices=URGENCY_CHOICES, default='medium')
    budget = models.CharField(max_length=20, choices=BUDGET_CHOICES, blank=True, null=True)
    contact_name = models.CharField(max_length=100)
    contact_phone = models.CharField(max_length=15)
    
    # Status and timestamps
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='open')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Provider assignment
    assigned_provider = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_requests')
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.title} - {self.customer.username}"

class ServiceResponse(models.Model):
    service_request = models.ForeignKey(ServiceRequest, on_delete=models.CASCADE, related_name='responses')
    provider = models.ForeignKey(CustomUser, on_delete=models.CASCADE) # CustomUser ko use kiya gaya
    message = models.TextField()
    proposed_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    estimated_time = models.CharField(max_length=100, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['created_at']
    
    def __str__(self):
        return f"Response from {self.provider.username} for {self.service_request.title}"

class Notification(models.Model):
    NOTIFICATION_TYPES = [
        ('booking', 'Booking'),
        ('review', 'Review'),
        ('message', 'Message'),
        ('payment', 'Payment'),
        ('system', 'System'),
    ]
    
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='notifications') # CustomUser ko use kiya gaya
    title = models.CharField(max_length=255)
    message = models.TextField()
    notification_type = models.CharField(max_length=50, choices=NOTIFICATION_TYPES)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    related_booking = models.ForeignKey(Booking, on_delete=models.CASCADE, blank=True, null=True) 
    
    def __str__(self):
        return f"Notification for {self.user.get_full_name()} - {self.title}"
    
    class Meta:
        ordering = ['-created_at']
