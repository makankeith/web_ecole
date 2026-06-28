from django.contrib import admin
from .models import Eleve
from ECOLE.models import Inscription # Importation pour l'historique des inscriptions

class InscriptionInline(admin.TabularInline):
    model = Inscription
    extra = 0 # Évite d'afficher des lignes vides inutiles
    fields = ('annee_scolaire', 'classe', 'mensualite', 'dernier_mois_paye', 'reliquat_mois_en_cours')
    readonly_fields = ('date_inscription',)

@admin.register(Eleve)
class EleveAdmin(admin.ModelAdmin):
    list_display = ('matricule', 'nom', 'prenom', 'sexe', 'ecole', 'telephone_tuteur', 'est_inscrit')
    list_filter = ('ecole', 'sexe', 'est_inscrit')
    search_fields = ('nom', 'prenom', 'matricule', 'nom_tuteur', 'telephone_tuteur')
    ordering = ('nom', 'prenom')
    
    # Intégration de l'historique annuel directement dans la fiche d'identité civile
    inlines = [InscriptionInline]
    
    # Organisation de la fiche d'édition par sections (facultatif mais très propre)
    fieldsets = (
        ("Identité Civile", {
            'fields': ('matricule', 'nom', 'prenom', 'sexe', 'date_naissance', 'lieu_naissance', 'photo')
        }),
        ("Rattachement", {
            'fields': ('ecole', 'est_inscrit')
        }),
        ("Parents / Tuteur", {
            'fields': ('nom_tuteur', 'telephone_tuteur', 'adresse_tuteur')
        }),
    )