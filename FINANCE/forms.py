from django import forms
from .models import Paiement

class PaiementForm(forms.ModelForm):
    class Meta:
        model = Paiement
        # On ne laisse que les champs que le caissier doit réellement remplir
        fields = ['montant', 'mois_concerne'] 
        
        widgets = {
            'montant': forms.NumberInput(attrs={
                'class': 'form-control', 
                'placeholder': 'Ex: 15000',
                'style': 'width: 100%; padding: 12px; border-radius: 8px; border: 1px solid #cbd5e1; font-size: 1rem;',
                'min': '0' # Empêche la saisie de montants négatifs
            }),
            'mois_concerne': forms.Select(attrs={
                'class': 'form-control',
                'style': 'width: 100%; padding: 12px; border-radius: 8px; border: 1px solid #cbd5e1; font-size: 1rem; cursor: pointer;'
            }),
        }
        
        labels = {
            'montant': 'Montant versé (FCFA)',
            'mois_concerne': 'Mois de scolarité réglé'
        }
from django import forms
from .models import Depense

class DepenseForm(forms.ModelForm):
    class Meta:
        model = Depense
        fields = ['libelle', 'montant', 'categorie', 'date_depense']
        widgets = {
            'libelle':      forms.TextInput(attrs={'class': 'form-control'}),
            'montant':      forms.NumberInput(attrs={'class': 'form-control'}),
            'categorie':    forms.Select(attrs={'class': 'form-control'}),
            'date_depense': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        }