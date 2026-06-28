from django.urls import path
from . import views

urlpatterns = [
    path('<int:ecole_id>/', views.liste_classes, name='liste_classes'),
    path('<int:ecole_id>/ajouter/', views.ajouter_classe, name='ajouter_classe'), 
    path('<int:ecole_id>/modifier/<int:classe_id>/', views.modifier_classe, name='modifier_classe'),
    path('ecole/<int:ecole_id>/classe/<int:classe_id>/exporter/', views.exporter_classe_excel, name='exporter_classe_excel'),
]
