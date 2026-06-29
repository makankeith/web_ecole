from django.contrib import admin
from .models import User

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ("username", "is_super_admin")
    filter_horizontal = ("ecoles",)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_super_admin:
            return qs
        return qs.filter(ecole__in=request.user.ecoles.all())

    # AJOUTE CETTE MÉTHODE ICI :
    def save_model(self, request, obj, form, change):
        # Si le mot de passe est en texte brut (ne commence pas par l'algo de hachage de Django)
        if obj.password and not obj.password.startswith(('pbkdf2_sha256$', 'bcrypt$', 'argon2$')):
            obj.set_password(obj.password) # Cette ligne effectue le hachage sécurisé
        super().save_model(request, obj, form, change)