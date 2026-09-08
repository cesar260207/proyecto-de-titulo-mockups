from django.contrib import admin

from .models import Actividad, Auditoria, Compromiso, Delegacion, Evidencia, MetaMedicion, PerfilUsuario

admin.site.register([Delegacion, PerfilUsuario, Actividad, Evidencia, Compromiso, MetaMedicion, Auditoria])
