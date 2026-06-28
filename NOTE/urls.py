from django.urls import path
from . import views

app_name = 'NOTE' 

urlpatterns = [
    path('selection/<int:ecole_id>/', views.selection_saisie, name='selection_notes'),
    path('grille/<int:ecole_id>/', views.saisie_grille, name='saisie_grille'),
    path('tableau-de-bord/<int:ecole_id>/', views.liste_notes_groupes, name='liste_notes_groupes'),
    path('config-matiere/<int:ecole_id>/', views.configuration_matiere, name='config_matiere'),
    path('liste-matieres/<int:ecole_id>/', views.liste_matieres_classes, name='liste_matieres'),
    path('detail/<int:ecole_id>/', views.detail_notes_groupe, name='detail_notes_groupe'),
    path('import/<int:ecole_id>/', views.import_notes_excel, name='import_notes_excel'),
    path('ecole/<int:ecole_id>/bulletins/selection/', views.choix_bulletin, name='choix_bulletin'),
    path('ecole/<int:ecole_id>/bulletins/generer/', views.generer_bulletins_classe, name='generer_bulletins_classe'),
]
    
