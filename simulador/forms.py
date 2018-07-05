from django import forms
from simulador.models import Contribuinte

class ImportarContribuicaoForm(forms.Form):
    arquivo = forms.FileField()

class ImportarIpcaForm(forms.Form):
    arquivo = forms.FileField()