from django import forms
from femtolytics.models import App

class AppForm(forms.ModelForm):
    class Meta:
        model = App
        fields = ['package_name']