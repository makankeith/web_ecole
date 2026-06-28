from django.urls import path
from . import views
urlpatterns = [
    path('<int:ecole_id>/', views.liste_eleves, name='liste_eleves'),
    path('<int:ecole_id>/ajouter/', views.ajouter_eleve, name='ajouter_eleve'),
    path('<int:ecole_id>/profil/<int:eleve_id>/', views.profil_eleve, name='profil_eleve'),
    path('<int:ecole_id>/import-excel/', views.import_eleves_excel, name='import_eleves_excel'),
    path('<int:ecole_id>/eleve/<int:eleve_id>/modifier/', views.modifier_eleve, name='modifier_eleve'),
    
    path('<int:ecole_id>/passation/', views.gestion_passation_classe, name='gestion_passation_masse'),
]

