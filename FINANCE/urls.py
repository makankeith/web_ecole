from django.urls import path
from . import views

urlpatterns = [
    path('<int:ecole_id>/', views.tableau_bord_finance, name='tableau_bord_finance'),
    path('<int:ecole_id>/ajouter/', views.ajouter_paiement, name='ajouter_paiement'),
    path('<int:ecole_id>/liste/', views.liste_paiements, name='liste_paiements'),
    path('<int:ecole_id>/impayes/', views.liste_impayes, name='liste_impayes'),
    path('<int:ecole_id>/import/', views.import_paiements, name='import_paiements'),
    path('<int:ecole_id>/appel-impayes/', views.liste_appel_impayes, name='pdf_appel_impayes'),
    path('ajout/<int:ecole_id>/',     views.ajouter_depense,   name='ajouter_depense'),
    path('liste/<int:ecole_id>/',     views.liste_depenses,    name='liste_depenses'),
]
