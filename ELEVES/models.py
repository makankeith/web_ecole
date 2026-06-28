import datetime
from django.db import models

class Eleve(models.Model):
    SEXE_CHOICES = [('M', 'Masculin'), ('F', 'Féminin')]

    # Identité civile fixe
    nom = models.CharField(max_length=50)
    prenom = models.CharField(max_length=50)
    date_naissance = models.DateField(blank=True, null=True)
    lieu_naissance = models.CharField(max_length=100, blank=True, null=True)
    sexe = models.CharField(max_length=1, choices=SEXE_CHOICES)
    matricule = models.CharField(max_length=20, unique=True, blank=True, null=True)
    
    # Rattachement à l'entité globale de l'école
    ecole = models.ForeignKey('ECOLE.Ecole', on_delete=models.CASCADE)

    # Coordonnées des parents (social)
    nom_tuteur = models.CharField(max_length=100, blank=True, null=True)
    telephone_tuteur = models.CharField(max_length=20, blank=True, null=True)
    adresse_tuteur = models.CharField(max_length=200, blank=True)

    # État général au sein de l'établissement
    photo = models.ImageField(upload_to='eleves/', blank=True, null=True)
    est_inscrit = models.BooleanField(default=True)
    date_creation = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.nom} {self.prenom}"

    def save(self, *args, **kwargs):
        # Génération automatique du matricule uniquement à la création (si non défini)
        if not self.matricule:
            # 1. Extraction des initiales ou des 3 premières lettres
            nom_ecole = self.ecole.nom.strip()
            mots = nom_ecole.split()
            
            if len(mots) >= 2:
                # Prend la première lettre de chaque mot (jusqu'à 3 mots)
                prefixe = "".join([m[0] for m in mots[:3]]).upper()
            else:
                # Si un seul mot, prend les 3 premières lettres
                prefixe = nom_ecole[:3].upper()
                
            # 2. Récupération des deux derniers chiffres de l'année en cours
            annee = str(datetime.date.today().year)[-2:]
            
            # 3. Calcul du compteur incrémentiel avec sécurité anti-collision
            base_compteur = Eleve.objects.filter(ecole=self.ecole).count() + 1
            
            while True:
                potentiel_matricule = f"{prefixe}-{annee}-{str(base_compteur).zfill(4)}"
                # Si ce matricule n'existe pas encore, on le valide
                if not Eleve.objects.filter(matricule=potentiel_matricule).exists():
                    self.matricule = potentiel_matricule
                    break
                # Sinon, on incrémente jusqu'à en trouver un de libre
                base_compteur += 1
                
        super().save(*args, **kwargs)