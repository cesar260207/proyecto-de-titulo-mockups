from django import forms

from .models import Actividad, Compromiso, Delegacion, Evidencia


class DelegacionForm(forms.ModelForm):
    class Meta:
        model = Delegacion
        fields = ['nombre', 'territorio', 'enfasis', 'activa']
        widgets = {'enfasis': forms.Textarea(attrs={'rows': 4})}


class ActividadForm(forms.ModelForm):
    class Meta:
        model = Actividad
        fields = ['delegacion', 'fecha', 'tipo_atencion', 'descripcion', 'accion', 'item_medicion', 'contacto', 'telefono']
        widgets = {'fecha': forms.DateInput(attrs={'type': 'date'}), 'descripcion': forms.Textarea(attrs={'rows': 3}), 'accion': forms.Textarea(attrs={'rows': 3})}


class EvidenciaForm(forms.ModelForm):
    class Meta:
        model = Evidencia
        fields = ['archivo', 'comentario']
        widgets = {'comentario': forms.Textarea(attrs={'rows': 2})}


class CompromisoForm(forms.ModelForm):
    class Meta:
        model = Compromiso
        fields = ['delegacion', 'responsable', 'solicitante', 'territorio', 'descripcion', 'fecha_comprometida', 'estado', 'observacion']
        widgets = {'fecha_comprometida': forms.DateInput(attrs={'type': 'date'}), 'descripcion': forms.Textarea(attrs={'rows': 3}), 'observacion': forms.Textarea(attrs={'rows': 2})}
