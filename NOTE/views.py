import openpyxl
import os
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import HttpResponse
from django.db import transaction
from django.db.models import Sum, Count, Avg, Max, Min
from django.conf import settings

from ECOLE.models import Ecole, AnneeScolaire, Inscription
from CLASSE.models import Classe
from ELEVES.models import Eleve
from .models import Matiere, Note, Coefficient, Bulletin
from .utils import BulletinPDF  # Assure-toi que ton fichier utils.py existe

def get_annee_active_ou_erreur(request, ecole):
    """Fonction utilitaire pour récupérer l'année active d'une école"""
    annee = AnneeScolaire.objects.filter(ecole=ecole, est_active=True).first()
    if not annee:
        messages.error(request, f"Aucune année scolaire n'est configurée comme active pour l'établissement {ecole.nom}.")
    return annee

def selection_saisie(request, ecole_id):
    ecole = get_object_or_404(Ecole, id=ecole_id)
    annee_active = get_annee_active_ou_erreur(request, ecole)
    
    classes = Classe.objects.filter(ecole=ecole)
    coefficients = Coefficient.objects.filter(classe__ecole=ecole).select_related('matiere', 'classe')
    
    return render(request, 'notes/selection.html', {
        'ecole': ecole,
        'annee_active': annee_active,
        'classes': classes,
        'coefficients': coefficients,
        'ecole_id': ecole_id,
        'PERIODES': Note.PERIODES,
        'TYPES_NOTES': Note.TYPES,
    })



def saisie_grille(request, ecole_id):
    ecole = get_object_or_404(Ecole, id=ecole_id)
    annee_active = get_annee_active_ou_erreur(request, ecole)
    
    if not annee_active: 
        return redirect('NOTE:selection_notes', ecole_id=ecole.id)

    # Récupération des paramètres (GET)
    classe_id = request.GET.get('classe')
    matiere_id = request.GET.get('matiere')
    periode = request.GET.get('periode')
    type_note = request.GET.get('type_note')
    focus_eleve_id = request.GET.get('focus') # Permet la surbrillance si on vient de la page de l'élève

    if not all([classe_id, matiere_id, periode, type_note]):
        messages.error(request, "Paramètres de sélection manquants.")
        return redirect('NOTE:selection_notes', ecole_id=ecole.id)

    classe = get_object_or_404(Classe, id=classe_id, ecole=ecole)
    matiere = get_object_or_404(Matiere, id=matiere_id, classe=classe)
    
    # Récupération des inscriptions actives
    inscriptions = Inscription.objects.filter(
        classe=classe, 
        annee_scolaire=annee_active
    ).select_related('eleve').order_by('eleve__nom', 'eleve__prenom')

    eleves = [ins.eleve for ins in inscriptions]

    # Barème dynamique (10 ou 20)
    is_primaire = hasattr(classe, 'niveau') and classe.niveau == 'PRIMAIRE'
    note_max = 10 if is_primaire else 20

    # SAUVEGARDE / MODIFICATION (POST)
    if request.method == 'POST':
        with transaction.atomic():
            for eleve in eleves:
                valeur_note_str = request.POST.get(f"note_{eleve.id}")

                # Si la case contient une valeur
                if valeur_note_str is not None and valeur_note_str.strip() != "":
                    try:
                        valeur_numerique = float(valeur_note_str.replace(',', '.'))
                        if 0 <= valeur_numerique <= note_max:
                            # update_or_create gère à la fois l'ajout et la modification
                            Note.objects.update_or_create(
                                eleve=eleve,
                                matiere=matiere,
                                periode=periode,
                                type_note=type_note,
                                annee_scolaire=annee_active,
                                defaults={'valeur': valeur_numerique}
                            )
                        else:
                            messages.warning(request, f"La note de {eleve.nom} doit être entre 0 et {note_max}.")
                    except ValueError:
                        messages.warning(request, f"Valeur invalide pour {eleve.nom}.")
                
                # Si la case est vidée par le prof, on supprime la note de la base de données
                else:
                    Note.objects.filter(
                        eleve=eleve,
                        matiere=matiere,
                        periode=periode,
                        type_note=type_note,
                        annee_scolaire=annee_active
                    ).delete()
                    
        messages.success(request, f"Notes enregistrées et mises à jour avec succès pour la classe : {classe.nom}")
        return redirect('NOTE:liste_notes_groupes', ecole_id=ecole.id)

    # PRÉPARATION DE L'AFFICHAGE (MODIFICATION)
    notes_existantes = Note.objects.filter(
        eleve__in=eleves,
        matiere=matiere,
        periode=periode,
        type_note=type_note,
        annee_scolaire=annee_active
    )
    # Création du dictionnaire pour le template
    dict_notes = {n.eleve_id: n.valeur for n in notes_existantes}

    # Pour afficher des noms lisibles (ex: "1er Trimestre" au lieu de "TRIMESTRE_1")
    dict_periodes = dict(Note.PERIODES)
    dict_types = dict(Note.TYPES)

    return render(request, 'notes/saisie_grille.html', {
        'ecole': ecole,
        'classe': classe,
        'matiere': matiere,
        'eleves': eleves,       
        'periode': dict_periodes.get(periode, periode),
        'type_note': dict_types.get(type_note, type_note),
        'dict_notes': dict_notes,
        'note_max': note_max,
        'focus_eleve_id': int(focus_eleve_id) if focus_eleve_id else None,
    })
def configuration_matiere(request, ecole_id):
    ecole = get_object_or_404(Ecole, id=ecole_id)
    classes = Classe.objects.filter(ecole=ecole)
    matieres = Matiere.objects.filter(ecole=ecole).select_related('classe')

    if request.method == 'POST':
        nom_matiere = request.POST.get('nom_matiere')
        classe_id = request.POST.get('classe_id')
        coeff_valeur = request.POST.get('coefficient')

        classe_obj = get_object_or_404(Classe, id=classe_id, ecole=ecole)
        
        matiere, created = Matiere.objects.get_or_create(
            nom=nom_matiere.strip(),
            ecole=ecole,
            classe=classe_obj
        )

        if coeff_valeur:
            Coefficient.objects.update_or_create(
                classe=classe_obj,
                matiere=matiere,
                defaults={'valeur': int(coeff_valeur)}
            )
            messages.success(request, f"Configuration enregistrée pour {nom_matiere} ({classe_obj.nom})")
            return redirect('NOTE:liste_matieres', ecole_id=ecole.id)

    return render(request, 'notes/config_matiere.html', {
        'matieres': matieres,
        'classes': classes,
        'ecole_id': ecole_id,
        'ecole': ecole
    })

def liste_matieres_classes(request, ecole_id):
    ecole = get_object_or_404(Ecole, id=ecole_id)
    classes = Classe.objects.filter(ecole=ecole).prefetch_related('coefficient_set__matiere')
    return render(request, 'notes/liste_matieres.html', {
        'classes': classes,
        'ecole_id': ecole_id,
        'ecole': ecole
    })

def import_notes_excel(request, ecole_id):
    ecole = get_object_or_404(Ecole, id=ecole_id)
    annee_active = get_annee_active_ou_erreur(request, ecole)

    if request.method == "POST" and request.FILES.get('excel_file'):
        file = request.FILES['excel_file']
        classe_id = request.POST.get('classe_id')
        periode = request.POST.get('periode')
        type_note = request.POST.get('type_note')
        
        classe = get_object_or_404(Classe, id=classe_id, ecole=ecole)
        
        try:
            wb = openpyxl.load_workbook(file)
            sheet = wb.active
            headers = [cell.value for cell in sheet[1]]
            
            matieres_colonnes = {} 
            for i in range(2, len(headers)):
                nom_matiere = headers[i]
                if nom_matiere:
                    m_obj = Matiere.objects.filter(nom__iexact=nom_matiere.strip(), classe=classe).first()
                    if m_obj:
                        matieres_colonnes[i] = m_obj

            count = 0
            with transaction.atomic():
                for row in sheet.iter_rows(min_row=2, values_only=True):
                    nom, prenom = row[0], row[1]
                    if not nom: continue

                    # Recherche via la table inscription de l'année active
                    inscription = Inscription.objects.filter(
                        eleve__nom__iexact=nom.strip(),
                        eleve__prenom__iexact=prenom.strip(),
                        classe=classe,
                        annee_scolaire=annee_active
                    ).first()
                    
                    if inscription:
                        for col_index, m_obj in matieres_colonnes.items():
                            valeur_note = row[col_index]
                            if valeur_note is not None:
                                Note.objects.update_or_create(
                                    eleve=inscription.eleve,
                                    matiere=m_obj,
                                    periode=periode,
                                    type_note=type_note,
                                    annee_scolaire=annee_active,
                                    defaults={'valeur': float(valeur_note)}
                                )
                        count += 1

            messages.success(request, f"Succès ! Notes de {count} élèves importées pour l'année {annee_active.nom}.")
            return redirect('NOTE:liste_notes_groupes', ecole_id=ecole.id)
        except Exception as e:
            messages.error(request, f"Erreur lors de la lecture du fichier : {e}")

    return render(request, 'notes/import_excel.html', {
        'classes': Classe.objects.filter(ecole=ecole),
        'ecole_id': ecole_id,
        'ecole': ecole,
        'PERIODES': Note.PERIODES,
        'TYPES_NOTES': Note.TYPES,
    })

def obtenir_appreciation(note, is_primaire=False):
    note_echelle = note * 2 if is_primaire else note
    if note_echelle < 5: return "Médiocre"
    elif note_echelle < 10: return "Insuffisant"
    elif note_echelle < 12: return "Passable"
    elif note_echelle < 14: return "Assez Bien"
    elif note_echelle < 16: return "Bien"
    elif note_echelle < 18: return "Très Bien"
    else: return "Excellent"







from NOTE.utils import BulletinPDF 


def generer_bulletins_classe(request, ecole_id):
    ecole = get_object_or_404(Ecole, id=ecole_id)
    annee_active = get_annee_active_ou_erreur(request, ecole)
    
    # Récupération standard et propre
    classe_id = request.GET.get('classe_id')
    periode = request.GET.get('periode', '').upper()
    
    if not classe_id or not periode:
        return HttpResponse("❌ Erreur : Paramètres 'classe_id' ou 'periode' manquants.", status=400)
        
    classe = get_object_or_404(Classe, id=classe_id, ecole=ecole)
    inscriptions = Inscription.objects.filter(classe=classe, annee_scolaire=annee_active).select_related('eleve')
    matieres = Matiere.objects.filter(classe=classe)
    coeffs = {c.matiere_id: c.valeur for c in Coefficient.objects.filter(classe=classe)}

    resultats_classe = []
    
    for ins in inscriptions:
        notes_eleve = Note.objects.filter(eleve=ins.eleve, periode=periode, annee_scolaire=annee_active)
        notes_dict = {}
        for n in notes_eleve:
            if n.matiere_id not in notes_dict: 
                notes_dict[n.matiere_id] = {}
            notes_dict[n.matiere_id][n.type_note] = n.valeur

        total_pts = 0
        total_coefs = 0
        
        for m in matieres:
            n = notes_dict.get(m.id, {})
            c = coeffs.get(m.id, 1)
            
            if periode.startswith('TRIMESTRE'): # Secondaire
                d1 = n.get('DEVOIR_1', None)
                d2 = n.get('DEVOIR_2', None)
                comp = n.get('COMPOSITION', 0)
                
                somme_dev = 0
                nb_dev = 0
                if d1 is not None:
                    somme_dev += d1
                    nb_dev += 1
                if d2 is not None:
                    somme_dev += d2
                    nb_dev += 1
                
                m_dev = (somme_dev / nb_dev) if nb_dev > 0 else 0
                moy_mat = (m_dev + (comp * 2)) / 3 if (comp > 0 or m_dev > 0) else 0
                
                total_pts += (moy_mat * c)
                total_coefs += c
            else: # Primaire
                val = n.get('MENSUELLE', 0)
                total_pts += val
                total_coefs += 1
        
        moy_gen = total_pts / total_coefs if total_coefs > 0 else 0
        resultats_classe.append({
            'eleve': ins.eleve,
            'moyenne': round(moy_gen, 2),
            'total_pts': round(total_pts, 2),
            'total_coefs': total_coefs,
            'notes_dict': notes_dict
        })

    # Tri par moyenne décroissante
    resultats_classe.sort(key=lambda x: x['moyenne'], reverse=True)
    effectif = len(resultats_classe)
    
    with transaction.atomic():
        for i, res in enumerate(resultats_classe):
            res['rang'] = i + 1
            Bulletin.objects.update_or_create(
                eleve=res['eleve'], 
                periode=periode,
                annee_scolaire=annee_active,
                defaults={
                    'classe': classe,
                    'moyenne_generale': res['moyenne'],
                    'total_points': res['total_pts'],
                    'rang': res['rang'],
                    'nombre_eleves': effectif
                }
            )

    # --- GENERATION DU PDF UNIQUE ---
    pdf = BulletinPDF()
    for res in resultats_classe:
        pdf.add_page()
        # ✅ CORRIGÉ : On passe 'classe' en second paramètre
        pdf.generer_tableau(
            ecole, classe, res['eleve'], matieres, res['notes_dict'], 
            coeffs, periode, res['moyenne'], res['rang'], effectif, annee_active.nom
        )

    nom_dossier = f"Bulletins_{classe.id}_{periode}_{annee_active.nom.replace('-', '_')}"
    chemin_dossier = os.path.join(settings.MEDIA_ROOT, 'bulletins', nom_dossier)
    if not os.path.exists(chemin_dossier): 
        os.makedirs(chemin_dossier)
    
    chemin_complet = os.path.join(chemin_dossier, f"Bulletins_{classe.nom}.pdf")
    pdf.output(chemin_complet)

    return HttpResponse(f"✅ Bulletins de l'année {annee_active.nom} générés avec succès : {effectif} élèves traités.")


def liste_notes_groupes(request, ecole_id):
    ecole = get_object_or_404(Ecole, id=ecole_id)
    annee_active = get_annee_active_ou_erreur(request, ecole)
    
    groupes = Note.objects.filter(
        matiere__ecole=ecole, 
        annee_scolaire=annee_active,
        eleve__inscriptions__annee_scolaire=annee_active  
    ).values(
        'eleve__inscriptions__classe__id',
        'eleve__inscriptions__classe__nom',
        'matiere__id',
        'matiere__nom',
        'periode',
        'type_note'
    ).annotate(total_notes=Count('id', distinct=True)).distinct()

    return render(request, 'notes/liste_notes_groupes.html', {
        'groupes': groupes,
        'ecole_id': ecole_id,
        'ecole': ecole,
        'annee_active': annee_active
    })


def detail_notes_groupe(request, ecole_id):
    ecole = get_object_or_404(Ecole, id=ecole_id)
    annee_active = get_annee_active_ou_erreur(request, ecole)
    
    c_id = request.GET.get('classe')
    m_id = request.GET.get('matiere')
    p = request.GET.get('periode')
    t = request.GET.get('type') or request.GET.get('type_note')

    if not c_id or not m_id or not p or not t:
        messages.error(request, "Impossible d'afficher les détails : paramètres de sélection manquants.")
        return redirect('NOTE:liste_notes_groupes', ecole_id=ecole.id)

    classe = get_object_or_404(Classe, id=c_id, ecole=ecole)
    matiere = get_object_or_404(Matiere, id=m_id, classe=classe)

    notes = Note.objects.filter(
        annee_scolaire=annee_active,
        eleve__inscriptions__classe=classe,
        eleve__inscriptions__annee_scolaire=annee_active, 
        matiere=matiere,
        periode=p,
        type_note=t
    ).select_related('eleve').order_by('eleve__nom', 'eleve__prenom').distinct()

    is_primaire = (classe.niveau == 'PRIMAIRE')
    note_max = 10 if is_primaire else 20
    seuil = 5 if is_primaire else 10

    for n in notes:
        n.appreciation = obtenir_appreciation(n.valeur, is_primaire)

    stats = notes.aggregate(moyenne=Avg('valeur'), max_note=Max('valeur'), min_note=Min('valeur'))

    return render(request, 'notes/detail_notes.html', {
        'ecole': ecole,
        'notes': notes,
        'classe': classe,
        'matiere': matiere,
        'periode': p,
        'type_note': t,
        'stats': stats,
        'note_max': note_max,
        'seuil': seuil,
    })

def choix_bulletin(request, ecole_id):
    ecole = get_object_or_404(Ecole, id=ecole_id)
    classes = Classe.objects.filter(ecole=ecole).order_by('niveau', 'nom')
    
    return render(request, 'notes/selection_bulletins.html', {
        'ecole': ecole,
        'classes': classes
    })