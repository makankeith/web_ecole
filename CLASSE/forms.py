from django import forms
from .models import Classe

class ClasseForm(forms.ModelForm):
    class Meta:
        model = Classe
        fields = ['nom', 'niveau', 'frais_inscription', 'mensualite', 'classe_suivante']
        widgets = {
            'nom': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: 10ème CG'}),
            'niveau': forms.Select(attrs={'class': 'form-control'}),
            'frais_inscription': forms.NumberInput(attrs={'class': 'form-control'}),
            'mensualite': forms.NumberInput(attrs={'class': 'form-control'}),
            'classe_suivante': forms.Select(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        # On extrait l'école passée depuis la vue
        ecole = kwargs.pop('ecole', None)
        super().__init__(*args, **kwargs)
        
        if ecole:
            # On filtre pour n'afficher que les classes de cette école
            self.fields['classe_suivante'].queryset = Classe.objects.filter(ecole=ecole)
            
        # Si on est en train de modifier une classe existante, on l'exclut de sa propre liste
        if self.instance and self.instance.pk:
            self.fields['classe_suivante'].queryset = self.fields['classe_suivante'].queryset.exclude(pk=self.instance.pk)