import pandas as pd
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db import transaction
from django.db.models import Q

from .models import Eleve
from CLASSE.models import Classe
from ECOLE.models import Ecole, Inscription
from ECOLE.utils import get_annee_active


def ajouter_eleve(request, ecole_id):
    ecole = get_object_or_404(Ecole, id=ecole_id)
    annee_active = get_annee_active(ecole)
    
    # Protection : impossible d'ajouter un élève sans année scolaire active
    if not annee_active:
        messages.error(request, "Impossible d'ajouter un élève : aucune année scolaire active n'est configurée.")
        return redirect('liste_eleves', ecole_id=ecole.id)
        
    classes = Classe.objects.filter(ecole=ecole)

    if request.method == "POST":
        classe_id = request.POST.get('classe')
        sexe = request.POST.get('sexe')
        
        # Validation basique des champs requis côté serveur
        if not classe_id:
            messages.error(request, "Veuillez sélectionner une classe valide.")
            return render(request, 'eleves/ajouter.html', {'ecole': ecole, 'classes': classes, 'annee_active': annee_active})
            
        if not sexe or sexe not in ['M', 'F']:
            messages.error(request, "Veuillez sélectionner un genre valide (Masculin ou Féminin).")
            return render(request, 'eleves/ajouter.html', {'ecole': ecole, 'classes': classes, 'annee_active': annee_active})

        try:
            with transaction.atomic():
                # 1. Création de l'élève. Le matricule se génère tout seul lors du .save() masqué derrière .create()
                eleve = Eleve.objects.create(
                    nom=request.POST.get('nom', '').strip().upper(),
                    prenom=request.POST.get('prenom', '').strip().title(),
                    sexe=sexe,
                    ecole=ecole,
                    date_naissance=request.POST.get('date_naissance') or None,
                    lieu_naissance=request.POST.get('lieu_naissance', '').strip(),
                    nom_tuteur=request.POST.get('tuteur', '').strip(),
                    telephone_tuteur=request.POST.get('telephone', '').strip(),
                    adresse_tuteur=request.POST.get('adresse_tuteur', '').strip(),
                    photo=request.FILES.get('photo')  # Récupère l'image si elle est fournie
                )

                # 2. Inscription de l'élève dans la classe sélectionnée pour l'année en cours
                classe_obj = Classe.objects.get(id=classe_id, ecole=ecole)
                Inscription.objects.create(
                    eleve=eleve,
                    classe=classe_obj,
                    annee_scolaire=annee_active,
                    mensualite=classe_obj.mensualite
                )
                
            messages.success(request, f"L'élève {eleve.prenom} {eleve.nom} a été inscrit avec succès. Matricule attribué : {eleve.matricule}")
            return redirect('liste_eleves', ecole_id=ecole.id)
            
        except Classe.DoesNotExist:
            messages.error(request, "La classe sélectionnée est introuvable ou n'appartient pas à cette école.")
        except Exception as e:
            messages.error(request, f"Une erreur est survenue lors de la création : {str(e)}")

    return render(request, 'eleves/ajouter.html', {
        'ecole': ecole, 
        'classes': classes,
        'annee_active': annee_active
    })
def liste_eleves(request, ecole_id):
    ecole = get_object_or_404(Ecole, id=ecole_id)
    annee_active = get_annee_active(ecole)
    
    if not annee_active:
        messages.warning(request, "Aucune année scolaire n'est active actuellement.")
        inscriptions = Inscription.objects.none()
    else:
        # On filtre les INSCRIPTIONS de l'année en cours pour n'afficher que les élèves présents
        inscriptions = Inscription.objects.filter(
            annee_scolaire=annee_active,
            eleve__ecole=ecole
        ).select_related('eleve', 'classe').order_by('eleve__nom', 'eleve__prenom')
    
    # Logique de recherche (sur le modèle Eleve via la relation Inscription)
    query = request.GET.get('search')
    if query:
        inscriptions = inscriptions.filter(
            Q(eleve__nom__icontains=query) | 
            Q(eleve__prenom__icontains=query) | 
            Q(eleve__matricule__icontains=query)
        )
    
    # Filtrage par classe depuis le menu déroulant
    classe_id = request.GET.get('classe')
    if classe_id:
        inscriptions = inscriptions.filter(classe_id=classe_id)
        
    classes = Classe.objects.filter(ecole=ecole)

    return render(request, "eleves/liste.html", {
        "ecole": ecole,
        "annee_active": annee_active,
        "inscriptions": inscriptions, # À exploiter dans ta boucle for : "for inscription in inscriptions"
        "classes": classes,
        "search_query": query,
        "selected_classe": int(classe_id) if classe_id else None
    })

def import_eleves_excel(request, ecole_id):
    ecole = get_object_or_404(Ecole, id=ecole_id)
    annee_active = get_annee_active(ecole)
    
    if not annee_active:
        messages.error(request, "Veuillez activer une année scolaire avant d'importer des élèves.")
        return redirect('liste_eleves', ecole_id=ecole.id)

    if request.method == 'POST' and request.FILES.get('file_excel'):
        file = request.FILES['file_excel']
        try:
            df = pd.read_excel(file)
            succes = 0
            erreurs = []
            
            with transaction.atomic():
                for index, row in df.iterrows():
                    # Champs obligatoires
                    nom = str(row.get('nom', '')).strip().upper()
                    prenom = str(row.get('prenom', '')).strip().title()
                    nom_classe = str(row.get('classe', '')).strip()
                    
                    # Validation des champs obligatoires
                    if not nom or not prenom or not nom_classe:
                        erreurs.append(f"Ligne {index + 2} : Les champs 'nom', 'prenom' et 'classe' sont obligatoires.")
                        continue
                    
                    try:
                        classe = Classe.objects.get(nom__iexact=nom_classe, ecole=ecole)
                        
                        # Création Eleve
                        eleve = Eleve.objects.create(
                            nom=nom,
                            prenom=prenom,
                            ecole=ecole,
                            sexe=str(row.get('sexe', 'M')).upper()[0] if pd.notnull(row.get('sexe')) else 'M',
                            date_naissance=row.get('date_naissance') if pd.notnull(row.get('date_naissance')) else None,
                            lieu_naissance=str(row.get('lieu_naissance', '')).strip() if pd.notnull(row.get('lieu_naissance')) else None,
                            matricule=str(row.get('matricule', '')).strip() if pd.notnull(row.get('matricule')) and str(row.get('matricule', '')).strip() else None,
                            nom_tuteur=str(row.get('nom_tuteur', '')).strip() if pd.notnull(row.get('nom_tuteur')) and str(row.get('nom_tuteur', '')).strip() else None,
                            telephone_tuteur=str(row.get('telephone_tuteur', '')).strip() if pd.notnull(row.get('telephone_tuteur')) and str(row.get('telephone_tuteur', '')).strip() else None,
                            adresse_tuteur=str(row.get('adresse_tuteur', '')).strip() if pd.notnull(row.get('adresse_tuteur')) else ''
                        )
                        
                        # Création Inscription
                        Inscription.objects.create(
                            eleve=eleve,
                            classe=classe,
                            annee_scolaire=annee_active,
                            mensualite=classe.mensualite
                        )
                        succes += 1
                        
                    except Classe.DoesNotExist:
                        erreurs.append(f"Ligne {index + 2} : La classe '{nom_classe}' n'existe pas.")
            
            # Rapport d'importation
            if succes > 0:
                messages.success(request, f"{succes} élèves importés et inscrits pour l'année {annee_active.nom}.")
            if erreurs:
                for err in erreurs[:5]:
                    messages.warning(request, err)
                if len(erreurs) > 5:
                    messages.warning(request, f"...et {len(erreurs) - 5} autres erreurs.")

        except Exception as e:
            messages.error(request, f"Erreur fatale lors de la lecture du fichier : {e}")
            
    return redirect('liste_eleves', ecole_id=ecole.id)
def profil_eleve(request, ecole_id, eleve_id):
    ecole = get_object_or_404(Ecole, id=ecole_id)
    eleve = get_object_or_404(Eleve, id=eleve_id, ecole=ecole)
    annee_active = get_annee_active(ecole)
    
    inscription_actuelle = Inscription.objects.filter(eleve=eleve, annee_scolaire=annee_active).first()
    
    # CORRECTION ICI : Remplace '-annee_scolaire__date_debut' par '-annee_scolaire__nom' 
    # ou tout autre champ existant dans ton modèle AnneeScolaire
    historique_inscriptions = Inscription.objects.filter(eleve=eleve).order_by('-annee_scolaire__nom')

    return render(request, 'eleves/profil.html', {
        'ecole': ecole,
        'eleve': eleve,
        'annee_active': annee_active,
        'inscription_actuelle': inscription_actuelle,
        'historique_inscriptions': historique_inscriptions
    })
def modifier_eleve(request, ecole_id, eleve_id):
    ecole = get_object_or_404(Ecole, id=ecole_id)
    eleve = get_object_or_404(Eleve, id=eleve_id, ecole=ecole)
    
    if request.method == "POST":
        try:
            with transaction.atomic():
                eleve.nom = request.POST.get('nom', '').strip().upper()
                eleve.prenom = request.POST.get('prenom', '').strip().title()
                eleve.date_naissance = request.POST.get('date_naissance') or None
                eleve.sexe = request.POST.get('sexe')
                eleve.nom_tuteur = request.POST.get('tuteur', '').strip()
                eleve.telephone_tuteur = request.POST.get('telephone', '').strip()
                eleve.save()
                
            messages.success(request, f"Le profil de {eleve.prenom} {eleve.nom} a été mis à jour.")
            return redirect('profil_eleve', ecole_id=ecole.id, eleve_id=eleve.id)
            
        except Exception as e:
            messages.error(request, f"Erreur lors de la modification : {str(e)}")
            
    return render(request, 'eleves/modifier.html', {
        'ecole': ecole,
        'eleve': eleve
    })


from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db import transaction
from ECOLE.models import Ecole, AnneeScolaire, Inscription
from CLASSE.models import Classe

def gestion_passation_classe(request, ecole_id):
    ecole = get_object_or_404(Ecole, id=ecole_id)
    classes = Classe.objects.filter(ecole=ecole)
    annees = AnneeScolaire.objects.filter(ecole=ecole)
    
    # Trouver l'année scolaire actuellement active pour l'école
    annee_active = annee_grid = AnneeScolaire.objects.filter(ecole=ecole, est_active=True).first()
    
    classe_id = request.GET.get('classe')
    eleves_inscrits = []
    classe_selectionnee = None
    classe_superieure_suggeree = None
    
    if classe_id:
        classe_selectionnee = get_object_or_404(Classe, id=classe_id, ecole=ecole)
        classe_superieure_suggeree = classe_selectionnee.classe_suivante
        
        # On récupère les inscriptions des élèves de cette classe POUR L'ANNÉE EN COURS (ACTIVE)
        if annee_active:
            eleves_inscrits = Inscription.objects.filter(
                annee_scolaire=annee_active,
                classe=classe_selectionnee
            ).select_related('eleve')

    if request.method == "POST":
        inscriptions_ids = request.POST.getlist('eleves_ids')
        nouvelle_annee_id = request.POST.get('nouvelle_annee')
        nouvelle_classe_id = request.POST.get('nouvelle_classe')
        
        if not inscriptions_ids:
            messages.warning(request, "Veuillez sélectionner au moins un élève pour la passation.")
            return redirect('gestion_passation_masse', ecole_id=ecole.id)
            
        nouvelle_classe = get_object_or_404(Classe, id=nouvelle_classe_id, ecole=ecole)
        
        try:
            with transaction.atomic():
                compteur = 0
                for ins_id in inscriptions_ids:
                    # Récupérer l'ancienne inscription
                    ancienne_inscription = Inscription.objects.get(id=ins_id)
                    
                    # Sécurité : On vérifie si l'élève n'est pas déjà inscrit pour la nouvelle année cible
                    deja_inscrit = Inscription.objects.filter(
                        eleve=ancienne_inscription.eleve,
                        annee_scolaire_id=nouvelle_annee_id
                    ).exists()
                    
                    if not deja_inscrit:
                        # Création de la nouvelle inscription pour la nouvelle année
                        # On réinitialise la mensualité par défaut de la nouvelle classe
                        Inscription.objects.create(
                            eleve=ancienne_inscription.eleve,
                            classe=nouvelle_classe,
                            annee_scolaire_id=nouvelle_annee_id,
                            mensualite=nouvelle_classe.mensualite,
                            dernier_mois_paye=0,
                            reliquat_mois_en_cours=0
                        )
                        compteur += 1
                        
            messages.success(request, f"Opération terminée. {compteur} élève(s) transféré(s) avec succès vers la nouvelle année.")
            return redirect('gestion_passation_masse', ecole_id=ecole.id)
            
        except Exception as e:
            messages.error(request, f"Une erreur système est survenue : {str(e)}")

    return render(request, 'eleves/passation_masse.html', {
        'ecole': ecole,
        'classes': classes,
        'annees': annees,
        'annee_active': annee_active,
        'eleves_inscrits': eleves_inscrits,
        'classe_selectionnee': classe_selectionnee,
        'classe_superieure_suggeree': classe_superieure_suggeree,
    })