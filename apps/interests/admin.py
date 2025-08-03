from django.contrib import admin
from .models import Interest

@admin.register(Interest)
class InterestAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'created_at', 'updated_at')
    search_fields = ('name',)
