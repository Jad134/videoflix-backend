from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from users.forms import CustomUserCreationForm
from users.models import CustomUser

# Register your models here.

@admin.register(CustomUser)
class CustomUserAdmin(admin.ModelAdmin):
    add_form = CustomUserCreationForm
    fieldsets = (
        
        (
            'Individuelle Daten',
            {
                'fields': (
                    'custom',
                    'phone',
                    'address',

                )
            }
        ),
        *UserAdmin.fieldsets,
    )
