from django import forms
from . import views
class FiltroSectoresForm(forms.Form):
    sectores = forms.CharField(label='Filtrar por sectores', required=False)
    rut = forms.IntegerField(label='Filtrar por Rut', required=False) 