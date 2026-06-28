from django import forms
from .models import Ecole

class EcoleForm(forms.ModelForm):
    class Meta:
        model = Ecole
        fields = ['nom', 'adresse', 'telephone', 'logo']
        widgets = {
            'nom': forms.TextInput(attrs={'class': 'form-control'}),
            'adresse': forms.TextInput(attrs={'class': 'form-control'}),
            'telephone': forms.TextInput(attrs={'class': 'form-control'}),
        }