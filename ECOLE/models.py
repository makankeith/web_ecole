
from django.db import models

class Ecole(models.Model):
    nom = models.CharField(max_length=100)
    adresse = models.CharField(max_length=200, blank=True)
    telephone = models.CharField(max_length=20, blank=True)
    logo = models.ImageField(upload_to="logos/", null=True, blank=True)

    def __str__(self):
        return self.nom

class AnneeScolaire(models.Model):
    ecole = models.ForeignKey('ECOLE.Ecole', on_delete=models.CASCADE)
    nom = models.CharField(max_length=20) # ex: "2024-2025", "2025-2026"
    est_active = models.BooleanField(default=False) # Détermine l'année en cours de traitement

    class Meta:
        unique_together = ('ecole', 'nom')

    def __str__(self):
        return f"{self.nom} ({self.ecole.nom})"

class Inscription(models.Model):
    """
    C'est LE modèle central. Il représente l'état académique et financier 
    d'un élève pour une année scolaire spécifique.
    """
    eleve = models.ForeignKey('ELEVES.Eleve', on_delete=models.CASCADE, related_name='inscriptions')
    classe = models.ForeignKey('CLASSE.Classe', on_delete=models.CASCADE)
    annee_scolaire = models.ForeignKey(AnneeScolaire, on_delete=models.CASCADE)
    
    # Toutes les informations financières liées à l'année vivent exclusivement ICI
    mensualite = models.DecimalField(max_digits=10, decimal_places=0, default=0)
    dernier_mois_paye = models.PositiveIntegerField(default=0)
    reliquat_mois_en_cours = models.DecimalField(max_digits=10, decimal_places=0, default=0)
    
    date_inscription = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('eleve', 'annee_scolaire') # Sécurité : une inscription max par élève par an

    def __str__(self):
        return f"{self.eleve.nom} {self.eleve.prenom} - {self.classe.nom} ({self.annee_scolaire.nom})"