from .models import AnneeScolaire

def get_annee_active(ecole):
    """
    Récupère l'année scolaire marquée comme active pour une école donnée.
    Retourne None si aucune année n'est active.
    """
    return AnneeScolaire.objects.filter(ecole=ecole, est_active=True).first()