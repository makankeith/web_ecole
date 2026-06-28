from django.contrib import admin
from django.contrib import admin
from .models import Matiere, Coefficient, Note, Bulletin

@admin.register(Coefficient)
class CoefficientAdmin(admin.ModelAdmin):
    list_display = ('matiere', 'classe', 'valeur')
    list_filter = ('classe', 'matiere')

# Register your models here.
@admin.register(Matiere)
class MatiereAdmin(admin.ModelAdmin):
    list_display = ('nom', 'classe', 'ecole', 'code')
    list_filter = ('classe', 'ecole')
    search_fields = ('nom', 'code')

@admin.register(Note)
class NoteAdmin(admin.ModelAdmin):
    # AJOUT de annee_scolaire dans le display et le filter
    list_display = ('eleve', 'matiere', 'valeur', 'periode', 'type_note', 'annee_scolaire')
    list_filter = ('annee_scolaire', 'periode', 'type_note', 'matiere__classe')
    search_fields = ('eleve__nom', 'eleve__prenom', 'matiere__nom')

@admin.register(Bulletin)
class BulletinAdmin(admin.ModelAdmin):
    # AJOUT de annee_scolaire
    list_display = ('eleve', 'classe', 'periode', 'moyenne_generale', 'rang', 'annee_scolaire')
    list_filter = ('annee_scolaire', 'classe', 'periode')
    readonly_fields = ('date_creation',)