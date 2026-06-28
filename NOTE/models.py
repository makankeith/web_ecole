from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator

class Matiere(models.Model):
    nom = models.CharField(max_length=100)
    code = models.CharField(max_length=10, blank=True, null=True) # Ex: MATH, FR
    ecole = models.ForeignKey('ECOLE.Ecole', on_delete=models.CASCADE)
    classe = models.ForeignKey('CLASSE.Classe', on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.nom} - {self.classe.nom}"

class Coefficient(models.Model):
    classe = models.ForeignKey('CLASSE.Classe', on_delete=models.CASCADE)
    matiere = models.ForeignKey(Matiere, on_delete=models.CASCADE)
    valeur = models.PositiveIntegerField(default=1)

    class Meta:
        unique_together = ('classe', 'matiere')

    def __str__(self):
        return f"{self.matiere.nom} ({self.classe.nom}) - Coeff: {self.valeur}"

class Note(models.Model):
    PERIODES = [
        # --- PRIMAIRE ---
        ('OCTOBRE', "Mois d'Octobre"), ('NOVEMBRE', "Mois de Novembre"), ('DECEMBRE', "Mois de Décembre"),
        ('JANVIER', "Mois de Janvier"), ('FEVRIER', "Mois de Février"), ('MARS', "Mois de Mars"),
        ('AVRIL', "Mois d'Avril"), ('MAI', "Mois de Mai"), ('JUIN', "Mois de Juin"),
        # --- SECONDAIRE ---
        ('TRIMESTRE_1', '1er Trimestre'), ('TRIMESTRE_2', '2ème Trimestre'), ('TRIMESTRE_3', '3ème Trimestre'),
    ]

    TYPES = [
        ('MENSUELLE', 'Composition Mensuelle'),
        ('DEVOIR_1', 'Devoir 1'),
        ('DEVOIR_2', 'Devoir 2'),
        ('COMPOSITION', 'Composition'),
    ]

    eleve = models.ForeignKey('ELEVES.Eleve', on_delete=models.CASCADE)
    matiere = models.ForeignKey(Matiere, on_delete=models.CASCADE)
    valeur = models.FloatField(validators=[MinValueValidator(0.0), MaxValueValidator(20.0)])
    periode = models.CharField(max_length=20, choices=PERIODES)
    type_note = models.CharField(max_length=20, choices=TYPES)
    annee_scolaire = models.ForeignKey('ECOLE.AnneeScolaire', on_delete=models.CASCADE)
    date_saisie = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['eleve', 'matiere', 'periode', 'type_note', 'annee_scolaire']

    def __str__(self):
        return f"{self.eleve.nom} - {self.matiere.nom}: {self.valeur} ({self.annee_scolaire.nom})"

class Bulletin(models.Model):
    eleve = models.ForeignKey('ELEVES.Eleve', on_delete=models.CASCADE)
    classe = models.ForeignKey('CLASSE.Classe', on_delete=models.CASCADE)
    annee_scolaire = models.ForeignKey('ECOLE.AnneeScolaire', on_delete=models.CASCADE)
    periode = models.CharField(max_length=50) 
    moyenne_generale = models.FloatField()
    total_points = models.FloatField(default=0)
    rang = models.IntegerField(null=True, blank=True)
    nombre_eleves = models.IntegerField(null=True, blank=True)
    date_creation = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('eleve', 'periode', 'annee_scolaire')

    def __str__(self):
        return f"Bulletin {self.periode} - {self.eleve.nom} ({self.annee_scolaire.nom})"