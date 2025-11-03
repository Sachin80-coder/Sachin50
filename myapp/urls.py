from django.urls import path
from . import views

# app_name removed for global access

urlpatterns = [
    
    # =======================================================
    # 1. General Pages / Public Access
    # =======================================================
    path('', views.index, name='index'),
    path('about/', views.AboutView.as_view(), name='about'),
    path('services/', views.services, name='services'),
    path('service/<int:service_id>/', views.service_detail, name='service_detail'),
    path('contact/', views.contact_view, name='contact'),
    path('privacy-policy/', views.privacy_policy_view, name='privacy_policy'),
    path('terms-of-service/', views.terms_of_service_view, name='terms_of_service'),
    path('booking/<int:booking_id>/', views.booking_detail, name='booking_detail'),
    path('booking/<int:booking_id>/cancel/', views.cancel_booking, name='cancel_booking'),
    
    # =======================================================
    # 2. Authentication & Password Management
    # =======================================================
    path('register/', views.user_register, name='register'),
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
    
  
    path('password-reset/done/', views.password_reset_done, name='password_reset_done'),
    path('password-reset/confirm/<uuid:token>/', views.password_reset_confirm, name='password_reset_confirm'),
    path('password-reset/complete/', views.password_reset_complete, name='password_reset_complete'),
    # Ek hi view ko do names de sakte hain
    path('password-reset/', views.simple_password_reset, name='password_reset_simple'),
    # =======================================================
    # 3. User Dashboard & Profile Management
    # =======================================================
    path('dashboard/', views.dashboard, name='dashboard'),
    path('admin/dashboard/', views.admin_dashboard, name='admin_dashboard'),
    
    path('profile/', views.profile, name='profile'),
    path('profile/edit/', views.profile_edit, name='profile_edit'),
    path('profile/change-password/', views.profile_change_password, name='profile_change_password'),
    path('profile/settings/', views.profile_settings, name='profile_settings'),
    path('profile/delete-account/', views.delete_account, name='delete_account'),
    path('provider-profile/', views.provider_profile, name='provider_profile'),
    
    # Provider/Service Management
    path('service/add/', views.add_service, name='add_service'),

    # Add these URLs
path('contact-provider/<int:provider_id>/', views.contact_provider, name='contact_provider'),
path('add-review/<int:booking_id>/', views.add_review, name='add_review'),
path('accept-booking/<int:booking_id>/', views.accept_booking, name='accept_booking'),
path('reject-booking/<int:booking_id>/', views.reject_booking, name='reject_booking'),
path('update-booking-status/<int:booking_id>/', views.update_booking_status, name='update_booking_status'),
path('profile/bookings/', views.profile_bookings, name='profile_bookings'),
    
    # =======================================================
    # 4. Booking, Request & Review Management
    # =======================================================
    path('profile/bookings/', views.profile_bookings, name='profile_bookings'),
    path('profile/reviews/', views.profile_reviews, name='profile_reviews'),

    path('service/<int:service_id>/book/', views.book_service, name='book_service'), # Unified URL for posting a service request
    path('service-requests/', views.service_requests, name='service_requests'),
    path('service-requests/<int:request_id>/', views.service_request_detail, name='service_request_detail'),
    path('service-requests/<int:request_id>/update/<str:status>/', views.update_request_status, name='update_request_status'),
    path('available-requests/', views.available_requests, name='available_requests'),
    path('service/<int:service_id>/edit/', views.edit_service, name='edit_service'),
    path('service/<int:service_id>/delete/', views.delete_service, name='delete_service'),
    path('post-request/', views.post_service_request, name='post_service_request'),
    path('service-requests/', views.service_requests, name='service_requests'),
    path('service-request/<int:request_id>/', views.service_request_detail, name='service_request_detail'),
    
    # =======================================================
    # 5. Notification Management
    # =======================================================
    path('profile/notifications/', views.profile_notifications, name='profile_notifications'),
    path('profile/notifications/<int:notification_id>/read/', views.mark_notification_read, name='mark_notification_read'),
    path('notifications/', views.profile_notifications, name='profile_notifications'),
    path('notifications/<int:notification_id>/mark-read/', views.mark_notification_read, name='mark_notification_read'),
    
    # API Endpoints (AJAX)
    path('api/notifications/count/', views.api_get_notifications, name='api_get_notifications'),
    path('api/notifications/read/<int:notification_id>/', views.api_mark_notification_read, name='api_mark_notification_read'),
]
