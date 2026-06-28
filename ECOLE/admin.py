from django.contrib import admin
from .models import Ecole, AnneeScolaire, Inscription

@admin.register(Ecole)
class EcoleAdmin(admin.ModelAdmin):
    list_display = ('nom', 'telephone', 'adresse')
    search_fields = ('nom', 'telephone')

@admin.register(AnneeScolaire)
class AnneeScolaireAdmin(admin.ModelAdmin):
    list_display = ('nom', 'ecole', 'est_active')
    list_filter = ('ecole', 'est_active')
    list_editable = ('est_active',) # Permet de changer l'année active directement depuis la liste
    ordering = ('-nom',)

@admin.register(Inscription)
class InscriptionAdmin(admin.ModelAdmin):
    list_display = (
        'get_eleve_matricule', 
        'eleve', 
        'classe', 
        'annee_scolaire', 
        'mensualite', 
        'dernier_mois_paye', 
        'reliquat_mois_en_cours'
    )
    list_filter = ('annee_scolaire', 'classe', 'annee_scolaire__ecole')
    search_fields = ('eleve__nom', 'eleve__prenom', 'eleve__matricule')
    date_hierarchy = 'date_inscription' # Ajoute une navigation temporelle en haut
    ordering = ('annee_scolaire', 'classe', 'eleve__nom')

    # Fonctions pour afficher proprement des données liées dans la liste
    @admin.display(ordering='eleve__matricule', description='Matricule')
    def get_eleve_matricule(self, obj):
        return obj.eleve.matricule