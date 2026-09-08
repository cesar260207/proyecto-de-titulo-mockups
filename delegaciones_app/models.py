from django.conf import settings
from django.core.validators import FileExtensionValidator, MinValueValidator
from django.db import models


class Delegacion(models.Model):
	nombre = models.CharField(max_length=120, unique=True)
	territorio = models.CharField(max_length=180)
	enfasis = models.TextField()
	activa = models.BooleanField(default=True)

	class Meta:
		ordering = ['nombre']
		verbose_name = 'delegación'
		verbose_name_plural = 'delegaciones'

	def __str__(self):
		return self.nombre


class PerfilUsuario(models.Model):
	ROLES = [
		('administrador', 'Administrador'),
		('coordinador', 'Coordinador'),
		('delegado', 'Delegado'),
		('funcionario', 'Funcionario'),
		('verificador', 'Verificador'),
		('consulta', 'Consulta'),
	]
	usuario = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='perfil')
	rol = models.CharField(max_length=20, choices=ROLES, default='consulta')
	delegacion = models.ForeignKey(Delegacion, on_delete=models.PROTECT, null=True, blank=True, related_name='perfiles')
	cargo = models.CharField(max_length=120, blank=True)

	def __str__(self):
		return f'{self.usuario.get_full_name() or self.usuario.username} - {self.get_rol_display()}'


class Actividad(models.Model):
	ESTADOS = [('borrador', 'Borrador'), ('pendiente', 'Pendiente de revisión'), ('aprobada', 'Aprobada'), ('rechazada', 'Rechazada')]
	codigo = models.CharField(max_length=32, unique=True, editable=False)
	funcionario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='actividades')
	delegacion = models.ForeignKey(Delegacion, on_delete=models.PROTECT, related_name='actividades')
	fecha = models.DateField()
	tipo_atencion = models.CharField(max_length=100)
	descripcion = models.TextField()
	accion = models.TextField()
	item_medicion = models.CharField(max_length=160)
	contacto = models.CharField(max_length=160, blank=True)
	telefono = models.CharField(max_length=40, blank=True)
	estado = models.CharField(max_length=20, choices=ESTADOS, default='pendiente')
	creada = models.DateTimeField(auto_now_add=True)
	actualizada = models.DateTimeField(auto_now=True)

	class Meta:
		ordering = ['-fecha', '-creada']

	def __str__(self):
		return f'{self.codigo} - {self.descripcion[:50]}'


class Evidencia(models.Model):
	actividad = models.ForeignKey(Actividad, on_delete=models.CASCADE, related_name='evidencias')
	archivo = models.FileField(upload_to='evidencias/%Y/%m/', validators=[FileExtensionValidator(['jpg', 'jpeg', 'png', 'pdf'])])
	comentario = models.TextField(blank=True)
	aprobada = models.BooleanField(null=True, blank=True)
	revisada_por = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True, blank=True, related_name='evidencias_revisadas')
	creada = models.DateTimeField(auto_now_add=True)


class Compromiso(models.Model):
	ESTADOS = [('ingresado', 'Ingresado'), ('pendiente', 'Pendiente'), ('proceso', 'En proceso'), ('realizado', 'Realizado')]
	folio = models.CharField(max_length=30, unique=True)
	delegacion = models.ForeignKey(Delegacion, on_delete=models.PROTECT, related_name='compromisos')
	responsable = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='compromisos')
	solicitante = models.CharField(max_length=160)
	territorio = models.CharField(max_length=160)
	descripcion = models.TextField()
	fecha_comprometida = models.DateField()
	estado = models.CharField(max_length=20, choices=ESTADOS, default='ingresado')
	observacion = models.TextField(blank=True)
	creado = models.DateTimeField(auto_now_add=True)


class MetaMedicion(models.Model):
	delegacion = models.ForeignKey(Delegacion, on_delete=models.PROTECT, related_name='metas')
	nombre = models.CharField(max_length=160)
	objetivo = models.PositiveIntegerField(validators=[MinValueValidator(1)])
	avance = models.PositiveIntegerField(default=0)
	ponderador = models.DecimalField(max_digits=5, decimal_places=2, default=0)
	periodo_inicio = models.DateField()
	periodo_termino = models.DateField()
	tope_cumplimiento = models.DecimalField(max_digits=5, decimal_places=2, default=150)
	activa = models.BooleanField(default=True)

	@property
	def cumplimiento(self):
		return min((self.avance / self.objetivo) * 100, float(self.tope_cumplimiento))


class Auditoria(models.Model):
	usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
	accion = models.CharField(max_length=80)
	entidad = models.CharField(max_length=80)
	identificador = models.CharField(max_length=80)
	detalle = models.JSONField(default=dict)
	fecha = models.DateTimeField(auto_now_add=True)
