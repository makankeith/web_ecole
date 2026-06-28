
from django.db import models

class Classe(models.Model):
    NIVEAU_CHOICES = [('PRIMAIRE', 'Primaire'), ('SECONDAIRE', 'Secondaire')]
    nom = models.CharField(max_length=50)
    ecole = models.ForeignKey('ECOLE.Ecole', on_delete=models.CASCADE)
    niveau = models.CharField(max_length=20, choices=NIVEAU_CHOICES)
    frais_inscription = models.DecimalField(max_digits=10, decimal_places=0, default=0)
    mensualite = models.DecimalField(max_digits=10, decimal_places=0, default=0)
    classe_suivante = models.ForeignKey(
        'self', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        help_text="La classe dans laquelle les élèves iront d'année en année"
    )

    def __str__(self):
        return f"{self.nom} ({self.ecole.nom})"