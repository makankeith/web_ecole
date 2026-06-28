from django.db import models

class Paiement(models.Model):
    MOIS_CHOICES = [
        (1, 'Octobre'), (2, 'Novembre'), (3, 'Décembre'),
        (4, 'Janvier'), (5, 'Février'), (6, 'Mars'),
        (7, 'Avril'), (8, 'Mai'), (9, 'Juin'),
    ]
    
    # 1. Clés étrangères avec related_name pour faciliter les requêtes inverses (ex: eleve.paiements.all())
    eleve = models.ForeignKey('ELEVES.Eleve', on_delete=models.CASCADE, related_name='paiements')
    # L'année scolaire ne doit plus être null, elle est obligatoire pour la comptabilité
    annee_scolaire = models.ForeignKey('ECOLE.AnneeScolaire', on_delete=models.RESTRICT, related_name='paiements')
    
    # 2. Données financières
    montant = models.DecimalField(max_digits=10, decimal_places=0)
    mois_concerne = models.PositiveIntegerField(choices=MOIS_CHOICES)
    date_paiement = models.DateTimeField(auto_now_add=True)


    class Meta:
        verbose_name = "Paiement"
        verbose_name_plural = "Paiements"
        ordering = ['-date_paiement']
        # SÉCURITÉ : Empêche d'enregistrer deux fois le même mois pour le même élève la même année
        unique_together = ['eleve', 'mois_concerne', 'annee_scolaire']

    def __str__(self):
        return f"{self.eleve.prenom} {self.eleve.nom} - {self.montant} F ({self.get_mois_concerne_display()})"
from django.db import models

# Choix des catégories de dépenses pour faciliter les statistiques
class CategorieDepense(models.TextChoices):
    SALAIRE = 'SALAIRE', 'Salaire des profs/personnel'
    FOURNITURE = 'FOURNITURE', 'Achat de fournitures'
    FACTURE = 'FACTURE', 'Paiement facture (Eau, Élec, Internet)'
    REPARATION = 'REPARATION', 'Réparation et Entretien'
    AUTRE = 'AUTRE', 'Autre dépense'

class Depense(models.Model):
    # Liaisons principales
    ecole = models.ForeignKey('ECOLE.Ecole', on_delete=models.CASCADE)
    annee_scolaire = models.ForeignKey('ECOLE.AnneeScolaire', on_delete=models.CASCADE) # Lien avec l'année active
    
    # Informations de la dépense
    libelle = models.CharField(max_length=255, verbose_name="Libellé de la dépense")
    montant = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Montant")
    categorie = models.CharField(max_length=20, choices=CategorieDepense.choices, default=CategorieDepense.AUTRE)
    date_depense = models.DateField(verbose_name="Date de la dépense")
    description = models.TextField(blank=True, null=True)
    
    # Traçabilité
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.libelle} - {self.montant} FCFA ({self.annee_scolaire})"


