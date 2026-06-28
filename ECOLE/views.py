from django.shortcuts import render
from django.shortcuts import render
from django.contrib.auth.decorators import login_required

@login_required
def liste_ecoles(request):

    if request.user.is_super_admin or request.is_superuser:
        ecoles = request.user.ecoles.all()
    else:
        ecoles = request.user.ecoles.all()

    return render(request, "ecole/liste.html", {
        "ecoles": ecoles
    })
from django.shortcuts import render, get_object_or_404
from .models import Ecole
# Importe tes autres modèles pour les stats
# from ELEVES.models import Eleve 


from django.shortcuts import render, redirect, get_object_or_404
from .models import Ecole
from .forms import EcoleForm
from django.contrib.auth.decorators import login_required

from django.db.models import Sum
from ELEVES.models import Eleve 
from CLASSE.models import Classe
from NOTE.models import Note 
from FINANCE.models import Paiement

from django.db.models import Count, Sum, Q
from django.utils import timezone



from django.db.models import Sum, Count
from django.shortcuts import render, get_object_or_404
from django.db.models import Sum, Count
from .models import Ecole, Inscription
from CLASSE.models import Classe
from FINANCE.models import Paiement,Depense
from .utils import get_annee_active



def dashboard_ecole(request, ecole_id):
    ecole = get_object_or_404(Ecole, id=ecole_id)
    
    # 1. Récupérer l'année scolaire active via ton utils.py
    annee_active = get_annee_active(ecole)
    
    # Initialisation des variables si aucune année n'est active
    total_eleves = 0
    recettes_mois = 0
    total_depenses = 0
    solde_actuel = 0
    garcons = 0
    filles = 0
    top_classes = []

    if annee_active:
        # 2. Total Élèves (On compte les INSCRIPTIONS de l'année active)
        inscriptions_actives = Inscription.objects.filter(annee_scolaire=annee_active)
        total_eleves = inscriptions_actives.count()
        
        # 3. Recettes de l'année en cours (Paiements liés à l'année active)
        recettes_mois = Paiement.objects.filter(
            annee_scolaire=annee_active
        ).aggregate(Sum('montant'))['montant__sum'] or 0

        # 4. Dépenses de l'année en cours (Filtrées par école et année active)
        total_depenses = Depense.objects.filter(
            ecole=ecole,
            annee_scolaire=annee_active
        ).aggregate(Sum('montant'))['montant__sum'] or 0

        # 5. Calcul du Solde Net
        solde_actuel = recettes_mois - total_depenses

        # 6. Répartition Genre (Basée sur les inscrits de cette année)
        garcons = inscriptions_actives.filter(eleve__sexe__icontains='M').count()
        filles = inscriptions_actives.filter(eleve__sexe__icontains='F').count()

        # 7. Effectifs par Classe
        top_classes = Classe.objects.filter(ecole=ecole).annotate(
            nb_eleves=Count('inscription', filter=Q(inscription__annee_scolaire=annee_active))
        ).order_by('-nb_eleves')

    # 8. Total Classes (Toutes les classes configurées dans l'école)
    total_classes = Classe.objects.filter(ecole=ecole).count()

    context = {
        'ecole': ecole,
        'annee_active': annee_active,
        'total_eleves': total_eleves,
        'total_classes': total_classes,
        'recettes_mois': recettes_mois,
        'total_depenses': total_depenses,
        'solde_actuel': solde_actuel,
        'garcons': garcons,
        'filles': filles,
        'top_classes': top_classes,
    }
    return render(request, 'ecole/dashboard.html', context)
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from django.db import transaction
from .models import Ecole, AnneeScolaire, Inscription
# Assure-toi que l'import de Classe est correct selon ton architecture
from CLASSE.models import Classe 

def generer_nouvelle_annee(request, ecole_id):
    ecole = get_object_or_404(Ecole, id=ecole_id)
    
    with transaction.atomic():
        # 1. Récupérer l'année qui se termine
        annee_actuelle = AnneeScolaire.objects.filter(ecole=ecole, est_active=True).first()
        
        if not annee_actuelle:
            messages.error(request, "Aucune année active trouvée pour cette école.")
            # Correction ici : on redirige vers ton dashboard
            return redirect('dashboard_ecole', pk=ecole_id)

        # 2. Déterminer le nom de la nouvelle année (ex: 2025-2026)
        try:
            parties = annee_actuelle.nom.split('-')
            nouvelle_annee_nom = f"{int(parties[0])+1}-{int(parties[1])+1}"
        except (ValueError, IndexError):
            messages.error(request, "Le format du nom de l'année actuelle est invalide (doit être ex: 2024-2025).")
            return redirect('dashboard_ecole', ecole_id=ecole.id)

        # 3. Créer la nouvelle année
        nouvelle_annee, created = AnneeScolaire.objects.get_or_create(
            ecole=ecole,
            nom=nouvelle_annee_nom,
            defaults={'est_active': False}
        )

        # 4. Transférer les élèves
        anciennes_inscriptions = Inscription.objects.filter(annee_scolaire=annee_actuelle)
        compteur = 0

        for ancienne in anciennes_inscriptions:
            classe_dest = ancienne.classe.classe_suivante
            
            if classe_dest:
                Inscription.objects.get_or_create(
                    eleve=ancienne.eleve,
                    annee_scolaire=nouvelle_annee,
                    defaults={
                        'classe': classe_dest,
                        'mensualite': classe_dest.mensualite,
                        'dernier_mois_paye': 0,
                        'reliquat_mois_en_cours': 0
                    }
                )
                compteur += 1

        # 5. Basculer l'activation
        AnneeScolaire.objects.filter(ecole=ecole).update(est_active=False)
        nouvelle_annee.est_active = True
        nouvelle_annee.save()

    messages.success(request, f"Passation réussie ! {compteur} élèves transférés en {nouvelle_annee.nom}")
    # Correction ici aussi
    return redirect('dashboard_ecole', ecole_id=ecole.id)
def gestion_annees_scolaires(request, ecole_id):
    ecole = get_object_or_404(Ecole, id=ecole_id)
    # Trié par le nom (ex: "2026-2027" s'affichera en haut)
    annees = AnneeScolaire.objects.filter(ecole=ecole).order_by('-nom')
    
    # Trouver l'année actuellement active
    annee_active = annees.filter(est_active=True).first()

    return render(request, 'ecole/gestion_annees.html', {
        'ecole': ecole,
        'annees': annees,
        'annee_active': annee_active
    })

def changer_annee_active(request, ecole_id, annee_id):
    ecole = get_object_or_404(Ecole, id=ecole_id)
    
    # 1. Désactiver toutes les années scolaires de cette école
    AnneeScolaire.objects.filter(ecole=ecole, est_active=True).update(est_active=False)
    
    # 2. Activer la nouvelle année sélectionnée
    nouvelle_annee = get_object_or_404(AnneeScolaire, id=annee_id, ecole=ecole)
    nouvelle_annee.est_active = True
    nouvelle_annee.save()
    
    messages.success(request, f"L'exercice comptable et scolaire a été basculé sur : {nouvelle_annee.nom}")
    
    return redirect('dashboard_ecole', ecole_id=ecole.id)