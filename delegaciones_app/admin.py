from django.contrib import admin

from .models import Actividad, Auditoria, CatalogoItem, Compromiso, Delegacion, Evidencia, MetaMedicion, PerfilUsuario, PeriodoMedicion

admin.site.register([Delegacion, PerfilUsuario, CatalogoItem, PeriodoMedicion, Actividad, Evidencia, Compromiso, MetaMedicion, Auditoria])
