from django.contrib import admin
from django.contrib import admin
from .models import Paiement
@admin.register(Paiement)
class PaiementAdmin(admin.ModelAdmin):
    # AJOUT de annee_scolaire
    list_display = ('eleve', 'montant', 'get_mois_display', 'annee_scolaire', 'date_paiement')
    list_filter = ('annee_scolaire', 'mois_concerne', 'date_paiement')
    search_fields = ('eleve__nom', 'eleve__prenom')
    date_hierarchy = 'date_paiement' # Ajoute un calendrier de navigation en haut

    def get_mois_display(self, obj):
        return obj.get_mois_concerne_display()
    get_mois_display.short_description = "Mois"