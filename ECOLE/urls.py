from django.urls import path
from . import views

urlpatterns = [
    path('', views.liste_ecoles, name='liste_ecoles'),
    path('dashboard/<int:ecole_id>/', views.dashboard_ecole, name='dashboard_ecole'),
    path('ecole/<int:ecole_id>/passation/', views.generer_nouvelle_annee, name='lancer_passation'),
    
   
    path('ecole/<int:ecole_id>/annees/', views.gestion_annees_scolaires, name='gestion_annees_scolaires'),
    path('ecole/<int:ecole_id>/annees/activer/<int:annee_id>/', views.changer_annee_active, name='changer_annee_active'),
]
