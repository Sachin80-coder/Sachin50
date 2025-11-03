from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User # Default User model
from .models import (
    CustomUser, 
    ServiceCategory, 
    Service, 
    ServiceImage, 
    Booking, 
    Review, 
    ServiceRequest, 
    ServiceResponse, 
    Notification,
    UserProfile # Added UserProfile to the imports for registration
)

# =======================================================
# 1. Custom User Model Registration
# =======================================================

# Step 1: Default User model ko unregister karein (Clash avoid karne ke liye)
try:
    admin.site.unregister(User) 
except admin.sites.NotRegistered:
    pass

# CustomUser model ke liye Admin class (UserAdmin se inherit kiya gaya)
@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    # list_display, list_filter, ordering: Sab CustomUser fields ke mutabik
    list_display = (
        'username', 
        'email', 
        'first_name', 
        'last_name', 
        'is_staff', 
        'user_type', 
        'is_verified', 
        'registration_date' 
    )

    list_filter = (
        'is_staff', 
        'is_superuser', 
        'is_active', 
        'user_type', 
        'is_verified'
    )
    
    ordering = ('registration_date',)

    # Admin change form mein custom fields
    fieldsets = UserAdmin.fieldsets + (
        ('FixFinder User Data', {'fields': (
            'user_type', 
            'phone', 
            'location', 
            'is_verified',
            'business_name', 
            'experience', 
            'service_categories'
        )}),
    )
    
    # Admin add user form mein custom fields
    add_fieldsets = UserAdmin.add_fieldsets + (
        (None, {
            'classes': ('wide',),
            'fields': (
                'user_type', 
                'phone', 
                'location'
            ),
        }),
    )


# =======================================================
# 2. Inline Models
# =======================================================
class ServiceImageInline(admin.TabularInline):
    model = ServiceImage
    extra = 1

# =======================================================
# 3. Main Model Registration
# =======================================================

@admin.register(ServiceCategory)
class ServiceCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'icon']
    search_fields = ['name']

@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ['title', 'provider', 'category', 'location', 'is_active', 'is_verified', 'rating', 'reviews_count']
    list_filter = ['category', 'is_active', 'is_verified', 'created_at']
    search_fields = ['title', 'description', 'provider__username']
    inlines = [ServiceImageInline]
    actions = ['make_verified', 'make_unverified']

    @admin.action(description='Mark selected services as verified')
    def make_verified(self, request, queryset):
        queryset.update(is_verified=True)
    
    @admin.action(description='Mark selected services as unverified')
    def make_unverified(self, request, queryset):
        queryset.update(is_verified=False)
    
@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    # 'list_display' mein 'price' ki jagah 'total_price' use karein
    list_display = (
        'id', 
        'customer', 
        'provider', 
        'service_name', 
        'status', 
        'service_date',
        'service_time',
        'total_price', # 👈 FIX: 'price' se 'total_price' kar diya gaya hai
        'booking_date'
    )
    list_filter = ('status', 'booking_date', 'service_date')
    search_fields = ('customer__username', 'provider__username', 'service_name')


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ['service', 'customer', 'rating', 'created_at', 'is_approved']
    list_filter = ['rating', 'is_approved', 'created_at']
    search_fields = ['comment', 'service__title', 'customer__username']
    raw_id_fields = ['booking', 'customer', 'provider', 'service']

@admin.register(ServiceRequest)
class ServiceRequestAdmin(admin.ModelAdmin):
    list_display = ['title', 'customer', 'category', 'location', 'urgency', 'status', 'created_at']
    list_filter = ['category', 'urgency', 'status', 'created_at']
    search_fields = ['title', 'description', 'customer__username', 'location']
    date_hierarchy = 'created_at'

@admin.register(ServiceResponse)
class ServiceResponseAdmin(admin.ModelAdmin):
    list_display = ['provider', 'service_request', 'proposed_price', 'created_at']
    list_filter = ['created_at']
    search_fields = ['provider__username', 'service_request__title', 'message']
    readonly_fields = ['created_at']

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['user', 'title', 'notification_type', 'is_read', 'created_at']
    list_filter = ['is_read', 'notification_type']
    search_fields = ['user__username', 'title', 'message']
    list_per_page = 20

@admin.register(UserProfile) # UserProfile ko register kiya gaya
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'user_type', 'phone', 'location', 'is_verified']
    list_filter = ['user_type', 'is_verified', 'created_at']
    search_fields = ['user__username', 'user__email', 'phone', 'business_name']
