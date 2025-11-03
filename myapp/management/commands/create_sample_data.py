from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from myapp.models import ServiceCategory, Service, CustomUser
from django.db import transaction
import random
from datetime import datetime, timedelta

class Command(BaseCommand):
    help = 'Create sample data for FixFinder application'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--reset',
            action='store_true',
            help='Delete existing data before creating sample data',
        )
    
    def handle(self, *args, **options):
        reset = options['reset']
        
        if reset:
            self.stdout.write('Deleting existing data...')
            Service.objects.all().delete()
            ServiceCategory.objects.all().delete()
            CustomUser.objects.filter(is_superuser=False).delete()
        
        self.stdout.write('Creating sample data for FixFinder...')
        
        try:
            with transaction.atomic():
                self.create_categories()
                self.create_users()
                self.create_services()
                
            self.stdout.write(
                self.style.SUCCESS('✅ Sample data created successfully!')
            )
            self.print_login_details()
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Error creating sample data: {str(e)}')
            )
    
    def create_categories(self):
        """Create service categories"""
        categories_data = [
            {'name': 'Plumbing', 'icon': '🔧', 'description': 'Professional plumbing services including pipe repairs, fixture installation, and emergency fixes.'},
            {'name': 'Electrical', 'icon': '⚡', 'description': 'Certified electrical work including wiring, repairs, and installations with safety standards.'},
            {'name': 'AC Repair', 'icon': '❄️', 'description': 'AC maintenance, repair, and installation services for all brands and models.'},
            {'name': 'Carpentry', 'icon': '🔨', 'description': 'Custom carpentry work including furniture, doors, windows, and woodwork repairs.'},
            {'name': 'Appliance', 'icon': '🔧', 'description': 'Home appliance repair services for washing machines, refrigerators, and other appliances.'},
            {'name': 'Cleaning', 'icon': '🧽', 'description': 'Professional home and office cleaning services with eco-friendly products.'},
            {'name': 'Painting', 'icon': '🎨', 'description': 'Interior and exterior painting services with quality materials and finishes.'},
            {'name': 'Pest Control', 'icon': '🐜', 'description': 'Professional pest control services for homes and offices with safe chemicals.'},
        ]
        
        for cat_data in categories_data:
            category, created = ServiceCategory.objects.get_or_create(
                name=cat_data['name'],
                defaults={
                    'icon': cat_data['icon'],
                    'description': cat_data['description']
                }
            )
            if created:
                self.stdout.write(f'Created category: {category.name}')
            else:
                self.stdout.write(f'Category already exists: {category.name}')
    
    def create_users(self):
        """Create sample users"""
        CustomUser = get_user_model()
        
        # Admin User
        admin_user, created = CustomUser.objects.get_or_create(
            email='admin@fixfinder.com',
            defaults={
                'username': 'admin@fixfinder.com',
                'first_name': 'Admin',
                'last_name': 'User',
                'user_type': 'admin',
                'phone': '+91 9999999999',
                'location': 'Mumbai, Maharashtra',
                'is_staff': True,
                'is_superuser': True
            }
        )
        if created:
            admin_user.set_password('admin123')
            admin_user.save()
            self.stdout.write('Created admin user: admin@fixfinder.com')
        
        # Sample Providers
        providers_data = [
            {
                'email': 'rajesh.plumbing@fixfinder.com',
                'first_name': 'Rajesh',
                'last_name': 'Kumar',
                'business_name': 'RK Plumbing Services',
                'phone': '+91 9876543210',
                'location': 'Mumbai, Maharashtra',
                'experience': '8 years',
                'categories': ['Plumbing', 'Electrical']
            },
            {
                'email': 'priya.electric@fixfinder.com', 
                'first_name': 'Priya',
                'last_name': 'Sharma',
                'business_name': 'PS Electrical Works',
                'phone': '+91 9876543211',
                'location': 'Delhi, NCR',
                'experience': '6 years',
                'categories': ['Electrical', 'AC Repair']
            },
            {
                'email': 'amit.ac@fixfinder.com',
                'first_name': 'Amit',
                'last_name': 'Verma',
                'business_name': 'CoolBreeze AC Services',
                'phone': '+91 9876543212',
                'location': 'Bangalore, Karnataka',
                'experience': '10 years',
                'categories': ['AC Repair', 'Appliance']
            },
            {
                'email': 'sneha.clean@fixfinder.com',
                'first_name': 'Sneha',
                'last_name': 'Patel',
                'business_name': 'Sparkle Cleaning Services',
                'phone': '+91 9876543213',
                'location': 'Mumbai, Maharashtra',
                'experience': '4 years',
                'categories': ['Cleaning', 'Pest Control']
            }
        ]
        
        for provider_data in providers_data:
            provider, created = CustomUser.objects.get_or_create(
                email=provider_data['email'],
                defaults={
                    'username': provider_data['email'],
                    'first_name': provider_data['first_name'],
                    'last_name': provider_data['last_name'],
                    'user_type': 'provider',
                    'phone': provider_data['phone'],
                    'location': provider_data['location'],
                    'business_name': provider_data['business_name'],
                    'experience': provider_data['experience'],
                    'is_verified': True
                }
            )
            if created:
                provider.set_password('provider123')
                provider.save()
                
                # Add service categories
                for category_name in provider_data['categories']:
                    try:
                        category = ServiceCategory.objects.get(name=category_name)
                        provider.service_categories.add(category)
                    except ServiceCategory.DoesNotExist:
                        self.stdout.write(f'Warning: Category {category_name} not found')
                
                self.stdout.write(f'Created provider: {provider_data["email"]}')
        
        # Sample Customers
        customers_data = [
            {
                'email': 'customer1@fixfinder.com',
                'first_name': 'Rahul',
                'last_name': 'Mehta',
                'phone': '+91 9876543214',
                'location': 'Mumbai, Maharashtra'
            },
            {
                'email': 'customer2@fixfinder.com',
                'first_name': 'Neha',
                'last_name': 'Singh',
                'phone': '+91 9876543215', 
                'location': 'Delhi, NCR'
            },
            {
                'email': 'customer3@fixfinder.com',
                'first_name': 'Arun',
                'last_name': 'Reddy',
                'phone': '+91 9876543216',
                'location': 'Bangalore, Karnataka'
            }
        ]
        
        for customer_data in customers_data:
            customer, created = CustomUser.objects.get_or_create(
                email=customer_data['email'],
                defaults={
                    'username': customer_data['email'],
                    'first_name': customer_data['first_name'],
                    'last_name': customer_data['last_name'],
                    'user_type': 'customer',
                    'phone': customer_data['phone'],
                    'location': customer_data['location'],
                    'is_verified': True
                }
            )
            if created:
                customer.set_password('customer123')
                customer.save()
                self.stdout.write(f'Created customer: {customer_data["email"]}')
    
    def create_services(self):
        """Create sample services"""
        providers = CustomUser.objects.filter(user_type='provider')
        categories = ServiceCategory.objects.all()
        
        services_data = [
            # Plumbing Services
            {
                'title': 'Expert Plumbing Services',
                'description': 'Professional plumbing services including pipe repairs, fixture installation, and emergency fixes. 24/7 availability for urgent issues. We handle all types of plumbing work with guaranteed satisfaction.',
                'category': 'Plumbing',
                'price_range': '₹500-2000',
                'location': 'Mumbai, Maharashtra',
                'experience': '8 years',
                'availability': 'Available Now',
                'rating': 4.8,
                'reviews_count': 156
            },
            {
                'title': 'Emergency Pipe Repair',
                'description': '24/7 emergency pipe repair services for burst pipes, leaks, and blockages. Quick response time with permanent solutions. Water damage restoration also available.',
                'category': 'Plumbing', 
                'price_range': '₹800-3000',
                'location': 'Mumbai, Maharashtra',
                'experience': '5 years',
                'availability': 'Available 24/7',
                'rating': 4.6,
                'reviews_count': 89
            },
            
            # Electrical Services
            {
                'title': 'Certified Electrical Work',
                'description': 'Licensed electrician offering wiring, repair, and installation services with warranty. Specialized in home electrical systems, switchboard upgrades, and safety inspections.',
                'category': 'Electrical',
                'price_range': '₹300-1500',
                'location': 'Delhi, NCR',
                'experience': '12 years',
                'availability': 'Available Now',
                'rating': 4.9,
                'reviews_count': 203
            },
            {
                'title': 'Home Wiring Installation',
                'description': 'Complete home wiring installation and rewiring services. We use high-quality materials and follow all safety standards. Free consultation and estimate.',
                'category': 'Electrical',
                'price_range': '₹2000-8000',
                'location': 'Delhi, NCR',
                'experience': '7 years',
                'availability': 'Available',
                'rating': 4.7,
                'reviews_count': 134
            },
            
            # AC Repair Services
            {
                'title': 'AC Repair & Maintenance',
                'description': 'Complete air conditioning services including repair, maintenance, gas charging, and installation. All brands covered with 90 days service warranty.',
                'category': 'AC Repair',
                'price_range': '₹800-3000',
                'location': 'Bangalore, Karnataka',
                'experience': '10 years',
                'availability': 'Available Now',
                'rating': 4.8,
                'reviews_count': 178
            },
            {
                'title': 'AC Installation Service',
                'description': 'Professional AC installation for all brands including split AC, window AC, and centralized systems. Free site inspection and consultation.',
                'category': 'AC Repair',
                'price_range': '₹1500-5000',
                'location': 'Bangalore, Karnataka',
                'experience': '8 years',
                'availability': 'Available',
                'rating': 4.9,
                'reviews_count': 95
            },
            
            # Cleaning Services
            {
                'title': 'Professional House Cleaning',
                'description': 'Comprehensive house cleaning services including deep cleaning, regular maintenance, and post-construction cleaning. We use eco-friendly products and modern equipment.',
                'category': 'Cleaning',
                'price_range': '₹500-1200',
                'location': 'Mumbai, Maharashtra',
                'experience': '4 years',
                'availability': 'Available Now',
                'rating': 4.7,
                'reviews_count': 167
            },
            {
                'title': 'Office Deep Cleaning',
                'description': 'Complete office cleaning services including carpet cleaning, furniture cleaning, and sanitization. We work after office hours to avoid disruption.',
                'category': 'Cleaning',
                'price_range': '₹800-2500',
                'location': 'Mumbai, Maharashtra',
                'experience': '3 years',
                'availability': 'Available',
                'rating': 4.5,
                'reviews_count': 78
            },
            
            # Carpentry Services
            {
                'title': 'Custom Carpentry Solutions',
                'description': 'Skilled carpentry work including furniture repair, custom woodwork, cabinet making, and installations. We work with all types of wood and materials.',
                'category': 'Carpentry',
                'price_range': '₹600-2500',
                'location': 'Mumbai, Maharashtra',
                'experience': '15 years',
                'availability': 'Available',
                'rating': 4.8,
                'reviews_count': 234
            },
            
            # Appliance Services
            {
                'title': 'Home Appliance Repair',
                'description': 'Expert repair services for washing machines, refrigerators, microwaves, and other home appliances. Genuine spare parts with warranty on service.',
                'category': 'Appliance',
                'price_range': '₹400-1800',
                'location': 'Bangalore, Karnataka',
                'experience': '6 years',
                'availability': 'Available Now',
                'rating': 4.6,
                'reviews_count': 145
            }
        ]
        
        for service_data in services_data:
            # Find appropriate provider for this service
            category = ServiceCategory.objects.get(name=service_data['category'])
            suitable_providers = providers.filter(
                service_categories=category,
                location__icontains=service_data['location'].split(',')[0]
            )
            
            if suitable_providers.exists():
                provider = suitable_providers.first()
            else:
                provider = providers.first()
            
            service, created = Service.objects.get_or_create(
                title=service_data['title'],
                provider=provider,
                defaults={
                    'category': category,
                    'description': service_data['description'],
                    'price_range': service_data['price_range'],
                    'location': service_data['location'],
                    'experience': service_data['experience'],
                    'availability': service_data['availability'],
                    'rating': service_data['rating'],
                    'reviews_count': service_data['reviews_count'],
                    'is_active': True,
                    'is_verified': True
                }
            )
            
            if created:
                self.stdout.write(f'Created service: {service.title}')
    
    def print_login_details(self):
        """Print login credentials for testing"""
        self.stdout.write('\n' + '='*50)
        self.stdout.write(self.style.SUCCESS('🚀 FIXFINDER SAMPLE DATA READY!'))
        self.stdout.write('='*50)
        
        self.stdout.write('\n📧 LOGIN CREDENTIALS:')
        self.stdout.write('-' * 30)
        self.stdout.write('👑 Admin Account:')
        self.stdout.write('   Email: admin@fixfinder.com')
        self.stdout.write('   Password: admin123')
        
        self.stdout.write('\n🔧 Provider Accounts:')
        self.stdout.write('   Email: rajesh.plumbing@fixfinder.com')
        self.stdout.write('   Password: provider123')
        self.stdout.write('   Email: priya.electric@fixfinder.com')
        self.stdout.write('   Password: provider123')
        self.stdout.write('   Email: amit.ac@fixfinder.com') 
        self.stdout.write('   Password: provider123')
        self.stdout.write('   Email: sneha.clean@fixfinder.com')
        self.stdout.write('   Password: provider123')
        
        self.stdout.write('\n👥 Customer Accounts:')
        self.stdout.write('   Email: customer1@fixfinder.com')
        self.stdout.write('   Password: customer123')
        self.stdout.write('   Email: customer2@fixfinder.com')
        self.stdout.write('   Password: customer123')
        self.stdout.write('   Email: customer3@fixfinder.com')
        self.stdout.write('   Password: customer123')
        
        self.stdout.write('\n💡 You can also register new accounts through the website!')
        self.stdout.write('='*50)