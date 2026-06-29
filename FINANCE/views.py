from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Sum, Q
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from decimal import Decimal
from datetime import datetime
import csv, io
from django.db import transaction

from .models import Paiement
from .forms import PaiementForm
from ELEVES.models import Eleve
from CLASSE.models import Classe
from ECOLE.models import Ecole, Inscription, AnneeScolaire
from ECOLE.utils import get_annee_active
from datetime import date


# 1. Ajoute ces deux imports tout en haut de ton fichier views.py
import traceback
from django.http import HttpResponse

# 2. Modifie ta vue comme ceci :
def tableau_bord_finance(request, ecole_id):
    try:
        ecole = get_object_or_404(Ecole, id=ecole_id)
        annee_active = get_annee_active(ecole)

        if not annee_active:
            messages.error(request, "Veuillez activer une année scolaire.")
            return redirect('dashboard_ecole', ecole_id=ecole.id)

        total_encaisse = Paiement.objects.filter(
            annee_scolaire=annee_active
        ).aggregate(total=Sum('montant'))['total'] or 0
        
        nb_eleves = Inscription.objects.filter(annee_scolaire=annee_active).count()
        
        mois_actuel_index = datetime.now().month
        
        nb_retardataires = Inscription.objects.filter(
            annee_scolaire=annee_active
        ).filter(
            Q(dernier_mois_paye__lt=mois_actuel_index) | 
            Q(reliquat_mois_en_cours__gt=0, dernier_mois_paye=mois_actuel_index)
        ).count()

        recent_paiements = Paiement.objects.filter(
            annee_scolaire=annee_active
        ).select_related('eleve').order_by('-date_paiement')[:5]

        return render(request, 'finance/dashboard_finance.html', {
            'total': total_encaisse,
            'nb_eleves': nb_eleves,
            'nb_retards': nb_retardataires,
            'ecole_id': ecole_id,
            'recent_paiements': recent_paiements,
            'ecole': ecole,
            'annee_active': annee_active
        })
        
    except Exception as e:
        # Si ça plante, on intercepte l'erreur et on l'affiche proprement à l'écran
        error_message = f"<h1>Erreur 500 Capturée</h1><p><b>{str(e)}</b></p><pre>{traceback.format_exc()}</pre>"
        return HttpResponse(error_message, status=500)
def ajouter_paiement(request, ecole_id):
    ecole = get_object_or_404(Ecole, id=ecole_id)
    annee_active = get_annee_active(ecole)
    query = request.GET.get('q', '')

    inscriptions = Inscription.objects.filter(annee_scolaire=annee_active).select_related('eleve', 'classe')
    
    if query:
        inscriptions = inscriptions.filter(
            Q(eleve__nom__icontains=query) | Q(eleve__prenom__icontains=query)
        )

    if request.method == "POST":
        inscription_id = request.POST.get('inscription_id')
        inscription = get_object_or_404(Inscription, id=inscription_id)
        eleve = inscription.eleve
        
        montant_verse = Decimal(request.POST.get('montant', 0))
        mois_choisi = int(request.POST.get('mois_concerne'))
        mensualite = inscription.mensualite

        # Sécurité transactionnelle : on s'assure que le paiement ET la mise à jour s'exécutent ensemble
        with transaction.atomic():
            deja_paye = Paiement.objects.filter(
                eleve=eleve, 
                mois_concerne=mois_choisi,
                annee_scolaire=annee_active
            ).exists()

            if deja_paye:
                messages.error(request, f"Le mois choisi a déjà été payé pour {eleve.nom} en {annee_active.nom}.")
                return redirect('ajouter_paiement', ecole_id=ecole_id)

            Paiement.objects.create(
                eleve=eleve,
                montant=montant_verse,
                mois_concerne=mois_choisi,
                annee_scolaire=annee_active
            )

            # Logique de calcul
            if inscription.reliquat_mois_en_cours > 0:
                if montant_verse >= inscription.reliquat_mois_en_cours:
                    montant_verse -= inscription.reliquat_mois_en_cours
                    inscription.reliquat_mois_en_cours = 0
                else:
                    inscription.reliquat_mois_en_cours -= montant_verse
                    montant_verse = 0

            while montant_verse >= mensualite and mensualite > 0:
                inscription.dernier_mois_paye += 1
                montant_verse -= mensualite

            if montant_verse > 0:
                inscription.dernier_mois_paye += 1
                inscription.reliquat_mois_en_cours = mensualite - montant_verse
            
            inscription.save()
            
        messages.success(request, f"Encaissement réussi pour {eleve.nom} !")
        return redirect('liste_paiements', ecole_id=ecole_id)

    return render(request, 'finance/ajouter_paiement.html', {
        'inscriptions': inscriptions,
        'ecole': ecole,
        'MOIS_CHOICES': Paiement.MOIS_CHOICES,
        'annee_active': annee_active
    })

def liste_paiements(request, ecole_id):
    ecole = get_object_or_404(Ecole, id=ecole_id)
    annee_active = get_annee_active(ecole)
    
    # 1. REQUÊTE DE BASE SÉCURISÉE
    # On passe par l'élève pour filtrer par école (eleve__ecole) 
    # On limite strictement à l'année scolaire active (annee_scolaire)
    # On pré-charge les données avec select_related/prefetch_related pour éviter les plantages dans le HTML
    paiements = Paiement.objects.filter(
        eleve__ecole=ecole, 
        annee_scolaire=annee_active
    ).select_related('eleve').order_by('-date_paiement')
    

    # 2. Récupération des paramètres de filtrage
    search_query = request.GET.get('search', '').strip()
    selected_classe = request.GET.get('classe', '').strip()

    # 3. Filtre Texte (Nom ou Prénom)
    if search_query:
        paiements = paiements.filter(
            Q(eleve__nom__icontains=search_query) | 
            Q(eleve__prenom__icontains=search_query)
        )

    # 4. Filtre par Classe
    if selected_classe:
        # On récupère directement les IDs des élèves inscrits dans cette classe pour l'année en cours
        eleves_inscrits_ids = Inscription.objects.filter(
            classe_id=selected_classe,
            annee_scolaire=annee_active
        ).values_list('eleve_id', flat=True)
        
        # On filtre les paiements pour ne garder que ceux de ces élèves
        paiements = paiements.filter(eleve_id__in=eleves_inscrits_ids)
    # 5. Calcul des totaux dynamiques (qui s'adaptent selon les filtres actifs)
    total_collecte = paiements.aggregate(Sum('montant'))['montant__sum'] or 0
    nombre_paiements = paiements.count()
    
    # Récupération des classes pour le `<select>` du template
    classes = Classe.objects.filter(ecole=ecole)

    context = {
        'ecole': ecole,
        'annee_active': annee_active,
        'paiements': paiements,
        'classes': classes,
        'search_query': search_query,
        'selected_classe': selected_classe,
        'total_collecte': total_collecte,
        'nombre_paiements': nombre_paiements,
    }
    
    return render(request, 'finance/liste_paiements.html', context)

def liste_impayes(request, ecole_id):
    ecole = get_object_or_404(Ecole, id=ecole_id)
    annee_active = get_annee_active(ecole)
    
    classes = Classe.objects.filter(ecole=ecole)
    classe_id = request.GET.get('classe')
    mois_index = int(request.GET.get('mois', 1))
    
    resultats = Inscription.objects.none() # Queryset vide par défaut
    
    if classe_id and annee_active:
        # Optimisation : La requête reste pure et ne charge que les relations nécessaires
        resultats = Inscription.objects.filter(
            classe_id=classe_id,
            annee_scolaire=annee_active
        ).filter(
            Q(dernier_mois_paye__lt=mois_index) | 
            Q(reliquat_mois_en_cours__gt=0, dernier_mois_paye=mois_index)
        ).select_related('eleve', 'classe')

    return render(request, 'finance/liste_impayes.html', {
        'resultats': resultats,
        'classes': classes,
        'mois_index': mois_index,
        'ecole_id': ecole_id,
        'annee_active': annee_active,
        'MOIS_CHOICES': Paiement.MOIS_CHOICES,
        'ecole':ecole
    })


def liste_appel_impayes(request, ecole_id):
    ecole = get_object_or_404(Ecole, id=ecole_id)
    annee_active = get_annee_active(ecole)
    classes = Classe.objects.filter(ecole=ecole)
    
    classe_id = request.GET.get('classe')
    mois_index = request.GET.get('mois')

    resultats = Inscription.objects.none()
    classe_nom = ""
    mois_nom = ""

    if classe_id and mois_index and annee_active:
        mois_index = int(mois_index)
        mois_dict = dict(Paiement.MOIS_CHOICES)
        mois_nom = mois_dict.get(mois_index, "")
        
        selected_classe = get_object_or_404(Classe, id=classe_id)
        classe_nom = selected_classe.nom

        resultats = Inscription.objects.filter(
            classe_id=classe_id,
            annee_scolaire=annee_active
        ).filter(
            Q(dernier_mois_paye__lt=mois_index) | 
            Q(reliquat_mois_en_cours__gt=0, dernier_mois_paye=mois_index)
        ).select_related('eleve').order_by('eleve__nom', 'eleve__prenom')

    return render(request, 'finance/pdf_appel_impayes.html', {
        'ecole_id': ecole_id,
        'classes': classes,  
        'MOIS_CHOICES': Paiement.MOIS_CHOICES,
        'resultats': resultats,
        'classe_nom': classe_nom,
        'mois_nom': mois_nom,
        'mois_index': mois_index,
        'annee_active': annee_active,
        
    })


def import_paiements(request, ecole_id):
    ecole = get_object_or_404(Ecole, id=ecole_id)
    annee_active = get_annee_active(ecole)

    if request.method == "POST" and request.FILES.get('file'):
        file = request.FILES['file']
        
        if not file.name.endswith('.csv'):
            messages.error(request, "Merci d'utiliser un fichier au format .csv")
            return redirect('import_paiements', ecole_id=ecole_id)

        try:
            decoded_file = file.read().decode('utf-8')
            io_string = io.StringIO(decoded_file)
            reader = csv.reader(io_string, delimiter=',')
            next(reader, None)  # next(..., None) évite l'erreur si le fichier est vide

            succes_count = 0
            erreurs = []

            # transaction.atomic garantit que si une erreur survient à la ligne 50, 
            # les 49 précédentes ne sont pas enregistrées pour éviter un état corrompu.
            with transaction.atomic():
                for row in reader:
                    if not row or len(row) < 4: 
                        continue
                    
                    try:
                        nom, prenom = row[0].strip(), row[1].strip()
                        montant_verse = Decimal(row[2].strip())
                        mois_index = int(row[3].strip())

                        inscription = Inscription.objects.select_related('eleve').get(
                            eleve__nom__iexact=nom, 
                            eleve__prenom__iexact=prenom, 
                            annee_scolaire=annee_active,
                            eleve__ecole_id=ecole_id
                        )

                        Paiement.objects.create(
                            eleve=inscription.eleve,
                            annee_scolaire=annee_active,
                            montant=montant_verse,
                            mois_concerne=mois_index
                        )

                        mensualite = inscription.mensualite
                        
                        if inscription.reliquat_mois_en_cours > 0:
                            if montant_verse >= inscription.reliquat_mois_en_cours:
                                montant_verse -= inscription.reliquat_mois_en_cours
                                inscription.reliquat_mois_en_cours = 0
                            else:
                                inscription.reliquat_mois_en_cours -= montant_verse
                                montant_verse = 0

                        while montant_verse >= mensualite and mensualite > 0:
                            inscription.dernier_mois_paye += 1
                            montant_verse -= mensualite

                        if montant_verse > 0:
                            inscription.dernier_mois_paye += 1
                            inscription.reliquat_mois_en_cours = mensualite - montant_verse
                        
                        inscription.save()
                        succes_count += 1

                    except Inscription.DoesNotExist:
                        erreurs.append(f"Élève introuvable : {row[0]} {row[1]}")
                    except (IndexError, ValueError) as e:
                        erreurs.append(f"Format invalide ligne {reader.line_num}: {row[0]}")

            if erreurs:
                messages.warning(request, f"{succes_count} importés. {len(erreurs)} erreurs (ex: {', '.join(erreurs[:3])})")
            else:
                messages.success(request, f"Importation réussie : {succes_count} paiements enregistrés.")

        except Exception as e:
            messages.error(request, f"Erreur critique lors de la lecture : {str(e)}")

        return redirect('liste_paiements', ecole_id=ecole_id)

    return render(request, 'finance/import.html', {'ecole': ecole, 'annee_active': annee_active})
from django.shortcuts import render, redirect
from django.db.models import Sum
from .models import Depense, CategorieDepense
from .forms import DepenseForm


def ajouter_depense(request, ecole_id):
    ecole = get_object_or_404(Ecole, id=ecole_id)
    annee_active = get_annee_active(ecole)

    # Sécurité : impossible d'ajouter une dépense sans année scolaire active
    if not annee_active:
        messages.error(request, "Impossible d'ajouter une dépense : aucune année scolaire active n'est configurée.")
        return redirect('liste_depenses', ecole_id=ecole.id)

    if request.method == 'POST':
        form = DepenseForm(request.POST)
        if form.is_valid():
            depense = form.save(commit=False)
            depense.ecole = ecole
            depense.annee_scolaire = annee_active # <-- Application de la nouvelle logique ici
            depense.save()
            
            messages.success(request, f"La dépense '{depense.libelle}' a été enregistrée avec succès.")
            return redirect('liste_depenses', ecole_id=ecole.id)
        else:
            messages.error(request, "Veuillez corriger les erreurs dans le formulaire.")
    else:
        form = DepenseForm()

    return render(request, 'finance/ajout.html', {
        'form': form, 
        'ecole': ecole,
        'annee_active': annee_active,
        'today': date.today()
    })

def liste_depenses(request, ecole_id):
    ecole = get_object_or_404(Ecole, id=ecole_id)
    annee_active = get_annee_active(ecole)

    # 1. Base de données des dépenses STRICTEMENT limitée à l'année active
    if annee_active:
        base_qs = Depense.objects.filter(ecole=ecole, annee_scolaire=annee_active)
    else:
        base_qs = Depense.objects.none() # S'il n'y a pas d'année, on retourne une liste vide

    # qs servira pour les filtres, base_qs sert pour les totaux globaux de l'année
    qs = base_qs.order_by('-date_depense')

    # 2. Récupération des paramètres GET
    categorie_filtre = request.GET.get('categorie', '')
    date_debut       = request.GET.get('date_debut', '')
    date_fin         = request.GET.get('date_fin', '')

    # 3. Application des filtres
    if categorie_filtre:
        qs = qs.filter(categorie=categorie_filtre)
    if date_debut:
        qs = qs.filter(date_depense__gte=date_debut)
    if date_fin:
        qs = qs.filter(date_depense__lte=date_fin)

    # 4. Fonction utilitaire pour calculer les totaux par catégorie
    def total_cat(cat):
        return base_qs.filter(categorie=cat).aggregate(Sum('montant'))['montant__sum'] or 0

    total_global = base_qs.aggregate(Sum('montant'))['montant__sum'] or 0
    total_filtre = qs.aggregate(Sum('montant'))['montant__sum'] or 0

    context = {
        'ecole': ecole,
        'annee_active': annee_active,
        'depenses': qs,
        'categories': CategorieDepense.choices,
        'categorie_filtre': categorie_filtre,
        'date_debut': date_debut,
        'date_fin': date_fin,
        
        # Totaux
        'total': total_global,
        'total_filtre': total_filtre,
        
        # Totaux par catégories (Ajuste les clés selon les vrais choix de ton TextChoices dans models.py)
        'total_salaire': total_cat('SALAIRE'),
        'total_pedagogie': total_cat('PEDAGOGIE'), 
        'total_fonctionnement': total_cat('FONCTIONNEMENT'),
        'total_divers': total_cat('DIVERS'),
    }
    
    return render(request, 'finance/liste.html', context)
