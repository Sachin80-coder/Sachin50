from django import forms
from django.contrib.auth.forms import PasswordResetForm, SetPasswordForm
from django.contrib.auth.models import User
# Aapke models ko yahan import kiya jaa raha hai. 
# Maine assume kiya hai ki yeh saare models (.models) mein available hain.
from .models import (
    ContactMessage, 
    UserProfile, 
    ServiceRequest, 
    ServiceResponse
) 

# =======================================================
# 1. Contact Form
# =======================================================

class ContactForm(forms.ModelForm):
    """
    Form for handling customer contact messages.
    """
    class Meta:
        model = ContactMessage
        fields = ['name', 'email', 'phone', 'subject', 'message']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Your Name',
                'required': True
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'Your Email',
                'required': True
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Your Phone Number'
            }),
            'subject': forms.Select(attrs={
                'class': 'form-control',
                'required': True
            }),
            'message': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Your message...',
                'rows': 6,
                'required': True
            }),
        }

# =======================================================
# 2. Authentication and User Forms
# (Using default User model, not CustomUser, as per original code)
# =======================================================

class CustomPasswordResetForm(PasswordResetForm):
    """
    Custom form for initiating the password reset process.
    Includes custom styling and email validation.
    """
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your registered email',
            'required': True,
            # Inline styles maintained as requested
            'style': 'width: 100%; padding: 12px; border: 2px solid #e5e7eb; border-radius: 8px; font-size: 1rem; transition: all 0.3s; outline: none; box-sizing: border-box;'
        })
    )
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        # NOTE: This validation uses django.contrib.auth.models.User
        if not User.objects.filter(email=email, is_active=True).exists():
            raise forms.ValidationError("No account found with this email address.")
        return email

class CustomSetPasswordForm(SetPasswordForm):
    """
    Custom form for setting a new password after successful reset link validation.
    Includes custom styling.
    """
    # new_password1 field is defined in the base SetPasswordForm
    new_password1 = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter new password',
            'required': True,
            # Inline styles maintained as requested
            'style': 'width: 100%; padding: 12px; border: 2px solid #e5e7eb; border-radius: 8px; font-size: 1rem; transition: all 0.3s; outline: none; box-sizing: border-box;'
        })
    )
    # new_password2 field is defined in the base SetPasswordForm
    new_password2 = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Confirm new password',
            'required': True,
            # Inline styles maintained as requested
            'style': 'width: 100%; padding: 12px; border: 2px solid #e5e7eb; border-radius: 8px; font-size: 1rem; transition: all 0.3s; outline: none; box-sizing: border-box;'
        })
    )

class UserProfileForm(forms.ModelForm):
    """
    Form for updating fields in the UserProfile model.
    """
    class Meta:
        model = UserProfile
        fields = [
            'phone', 'location', 'bio', 'date_of_birth',
            'business_name', 'experience', 'service_categories', 
            'service_area', 'license_number', 'insurance_info',
            'email_notifications', 'sms_notifications', 'profile_visible'
        ]
        widgets = {
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'location': forms.TextInput(attrs={'class': 'form-control'}),
            'bio': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'date_of_birth': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'business_name': forms.TextInput(attrs={'class': 'form-control'}),
            'experience': forms.TextInput(attrs={'class': 'form-control'}),
            'service_area': forms.TextInput(attrs={'class': 'form-control'}),
            'license_number': forms.TextInput(attrs={'class': 'form-control'}),
            'insurance_info': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

class UserForm(forms.ModelForm):
    """
    Form for updating basic fields in the default Django User model.
    """
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
        }

class PasswordChangeForm(forms.Form):
    """
    Standard form for changing a user's password (requires current password).
    """
    current_password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Current Password'})
    )
    new_password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'New Password'})
    )
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Confirm New Password'})
    )

# =======================================================
# 3. Service Request and Response Forms
# =======================================================

class ServiceRequestForm(forms.ModelForm):
    """
    Form for customers to submit a request for service.
    Includes custom validation and styling.
    """
    class Meta:
        model = ServiceRequest
        fields = [
            'category', 'title', 'description', 'location', 
            'urgency', 'budget', 'contact_name', 'contact_phone'
        ]
        widgets = {
            'category': forms.HiddenInput(),
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Brief title for your service request',
                'required': True,
                # Inline styles maintained as requested
                'style': 'width: 100%; padding: 14px; border: 2px solid #e5e7eb; border-radius: 8px; font-size: 1rem;'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Describe the problem in detail...',
                'rows': 4,
                'required': True,
                # Inline styles maintained as requested
                'style': 'width: 100%; padding: 14px; border: 2px solid #e5e7eb; border-radius: 8px; font-size: 1rem; resize: vertical;'
            }),
            'location': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Your area/city',
                'required': True,
                # Inline styles maintained as requested
                'style': 'width: 100%; padding: 14px; border: 2px solid #e5e7eb; border-radius: 8px; font-size: 1rem;'
            }),
            'urgency': forms.Select(attrs={
                'class': 'form-control',
                'required': True,
                # Inline styles maintained as requested
                'style': 'width: 100%; padding: 14px; border: 2px solid #e5e7eb; border-radius: 8px; font-size: 1rem;'
            }),
            'budget': forms.Select(attrs={
                'class': 'form-control',
                # Inline styles maintained as requested
                'style': 'width: 100%; padding: 14px; border: 2px solid #e5e7eb; border-radius: 8px; font-size: 1rem;'
            }),
            'contact_name': forms.TextInput(attrs={
                'class': 'form-control',
                'required': True,
                # Inline styles maintained as requested
                'style': 'width: 100%; padding: 12px; border: 2px solid #e5e7eb; border-radius: 8px; font-size: 1rem;'
            }),
            'contact_phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '+91 9876543210',
                'required': True,
                # Inline styles maintained as requested
                'style': 'width: 100%; padding: 12px; border: 2px solid #e5e7eb; border-radius: 8px; font-size: 1rem;'
            }),
        }
    
    def clean_title(self):
        title = self.cleaned_data.get('title')
        if len(title) < 10:
            raise forms.ValidationError("Service title should be at least 10 characters long.")
        return title
    
    def clean_description(self):
        description = self.cleaned_data.get('description')
        if len(description) < 20:
            raise forms.ValidationError("Description should be at least 20 characters long.")
        return description
    
    def clean_contact_phone(self):
        phone = self.cleaned_data.get('contact_phone')
        # Basic phone validation
        if not any(char.isdigit() for char in phone):
            raise forms.ValidationError("Please enter a valid phone number.")
        return phone

class ServiceResponseForm(forms.ModelForm):
    """
    Form for service providers to respond to a ServiceRequest.
    """
    class Meta:
        model = ServiceResponse
        fields = ['message', 'proposed_price', 'estimated_time']
        widgets = {
            'message': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Write your response to the customer...',
                'rows': 4,
                'required': True
            }),
            'proposed_price': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Proposed price in ₹',
                'step': '0.01'
            }),
            'estimated_time': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., 2 hours, 1 day, etc.'
            }),
        }


# forms.py
from django import forms
from .models import ServiceRequest

class ServiceRequestForm(forms.ModelForm):
    class Meta:
        model = ServiceRequest
        fields = ['category', 'title', 'description', 'location', 'budget', 'contact_name', 'contact_phone']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Brief title for your service request'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Describe your problem in detail...',
                'rows': 4
            }),
            'location': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter your location'
            }),
            'budget': forms.Select(attrs={
                'class': 'form-control'
            }),
            'contact_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Your full name'
            }),
            'contact_phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Your phone number'
            }),
        }