# management/commands/create_categories.py
from django.core.management.base import BaseCommand
from myapp.models import ServiceCategory

class Command(BaseCommand):
    help = 'Create default service categories'

    def handle(self, *args, **options):
        categories = [
            {"name": "Plumbing", "icon": "🚰"},
            {"name": "Electrical", "icon": "⚡"},
            {"name": "Cleaning", "icon": "🧹"},
            {"name": "Painting", "icon": "🎨"},
            {"name": "Carpentry", "icon": "🪚"},
            {"name": "AC Repair", "icon": "❄️"},
            {"name": "Appliance Repair", "icon": "🔧"},
            {"name": "Pest Control", "icon": "🐛"},
            {"name": "Moving", "icon": "📦"},
            {"name": "Other", "icon": "🔍"},
        ]
        
        for cat_data in categories:
            category, created = ServiceCategory.objects.get_or_create(
                name=cat_data["name"],
                defaults={"icon": cat_data["icon"]}
            )
            if created:
                self.stdout.write(
                    self.style.SUCCESS(f'Created category: {cat_data["name"]}')
                )
        
        self.stdout.write(
            self.style.SUCCESS('Successfully created all categories!')
        )