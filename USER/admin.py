from django.contrib import admin
from .models import User

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ("username", "is_super_admin")
    filter_horizontal = ("ecoles",)
# Register your models here.
def get_queryset(self, request):
    qs = super().get_queryset(request)

    if request.user.is_super_admin:
        return qs

    return qs.filter(ecole__in=request.user.ecoles.all())
