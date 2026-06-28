from django.contrib import admin
from .models import Classe

@admin.register(Classe)
class ClasseAdmin(admin.ModelAdmin):
    list_display = ('nom', 'ecole', 'niveau', 'frais_inscription', 'mensualite', 'classe_suivante')
    list_filter = ('ecole', 'niveau')
    search_fields = ('nom',)
    ordering = ('ecole', 'niveau', 'nom')