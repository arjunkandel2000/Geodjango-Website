from django.contrib import admin
from .models import Shp
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

# Register your models here.

admin.site.register(Shp)
