from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin

class UsuarioManager(BaseUserManager):
    def create_user(self, email, nombres, apellidos, rut, telefono, password=None, usuario_tipo='cliente', numero_medidor=None):
        if usuario_tipo in ['operador', 'administrador'] and not email:
            raise ValueError('Los usuarios de tipo "operador" y "administrador" deben tener un correo electrónico o un username.')

        usuario = self.model(
            email=self.normalize_email(email) if email and usuario_tipo == 'cliente' else None,
            nombres=nombres,
            apellidos=apellidos,
            rut=rut,
            telefono=telefono,
            usuario_tipo=usuario_tipo
        )

        if email:
            usuario.email = self.normalize_email(email)

        if usuario_tipo in ['operador', 'administrador'] and not email:
            raise ValueError('Los usuarios de tipo "operador" y "administrador" deben tener un correo electrónico o un username.')

        usuario.set_password(password)
        usuario.save()
        return usuario

    def create_superuser(self, email, nombres, apellidos, rut, telefono, password, usuario_tipo='administrador', numero_medidor=None):
        usuario = self.create_user(
            email=email if email else None,
            nombres=nombres,
            apellidos=apellidos,
            rut=rut,
            telefono=telefono,
            password=password,
            usuario_tipo=usuario_tipo
        )
        usuario.usuario_administrador = True
        usuario.save()
        return usuario

class Usuario(AbstractBaseUser, PermissionsMixin):
    TIPOS_DE_USUARIO = (
        ('cliente', 'Cliente'),
        ('operador', 'Operador'),
        ('administrador', 'Administrador'),
    )

    email = models.EmailField('Correo electrónico', unique=True, max_length=254, blank=True, null=True)
    nombres = models.CharField('Nombres', max_length=200)
    apellidos = models.CharField('Apellidos', max_length=200)
    rut = models.IntegerField('Rut', null=True)
    telefono = models.IntegerField('Telefono')
    usuario_activo = models.BooleanField(default=True)
    usuario_administrador = models.BooleanField(default=False)
    usuario_tipo = models.CharField('Tipo de usuario', max_length=15, choices=TIPOS_DE_USUARIO, default='cliente')
    sectores = models.CharField('Sectores', max_length=255, blank=True, null=True)
    numero_medidor = models.CharField('Número de Medidor', max_length=255, blank=True, null=True)
    objects = UsuarioManager()


    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['nombres', 'apellidos', 'rut', 'telefono']

    def __str__(self):
        return f'{self.nombres}, {self.apellidos}'

class Notificacion(models.Model):
    titulo = models.CharField(max_length=100)
    mensaje = models.TextField()
    fecha_envio = models.DateTimeField(auto_now_add=True)

    def str(self):
        return self.titulo
    
class Proveedor(models.Model):
    nombre = models.CharField(max_length=100)
    telefono = models.CharField(max_length=15)
    giro = models.CharField(max_length=100)
    servicio = models.CharField(max_length=100)
    categoria = models.CharField(max_length=100)

    def str(self):
        return self.nombre

class Tarifa(models.Model):
    nombre = models.CharField(max_length=100)
    monto = models.DecimalField(max_digits=10, decimal_places=2)
    descripcion = models.TextField()

    def str(self):
        return self.nombre
    
class Config_tarifa(models.Model):
    nom_config_tarifa = models.CharField(max_length=50)
    desc_config_tarifa = models.CharField(max_length=50)

    def str(self):
        return self.nom_config_tarifa
    
class Detalle_pago(models.Model):
    fecha_ini_dpago = models.DateField()
    fecha_fin_dpago = models.DateField()
    monto_dpago = models.CharField(max_length=30)
    metro_cubico = models.CharField(max_length=30)


    def str(self):
        return self.fecha_ini_dpago

class Subsidio(models.Model):
    nombre_subsidio = models.CharField(max_length=30)
    desc_subsidio = models.CharField(max_length=30)
    porcentaje_subsidio = models.CharField(max_length=30)

    def str(self):
        return self.nombre_subsidio
    
class Interes(models.Model):
    tipo_interes = models.CharField(max_length=30)
    porcentaje_interes = models.CharField(max_length=30)

    def str(self):
        return self.tipo_interes

class Convenio(models.Model):
    conv_vigente = models.CharField(max_length=10)
    num_meses = models.CharField(max_length=20)
    cant_cuotas = models.CharField(max_length=25)
    cuota_no_paga = models.CharField(max_length=25)
    monto_a_pago = models.CharField(max_length=25)

    def str(self):
        return self.conv_vigente
    
class costo(models.Model):
    monto_total_costo = models.DecimalField(max_digits=10, decimal_places=2)
    insumo_costo = models.CharField(max_length=25)
    gasto_opr_costo = models.DecimalField(max_digits=10, decimal_places=2)
    rrhh_costo = models.DecimalField(max_digits=10, decimal_places=2)
    otro_costo = models.CharField(max_length=25)

    def str(self):
        return self.monto_total_costo

class Registro_sistema (models.Model):
    fecha_registro = models.DateField()
    accion = models.CharField(max_length=25)

    def str(self):
        return self.fecha_registro

class Detalle_factura(models.Model):
    fecha_emision = models.DateField()
    fecha_vencimiento = models.DateField()
    monto_total = models.CharField(max_length=25)
    estado = models.CharField(max_length=25)

    def str(self):
        return self.fecha_emision
    
class Detalle_boleta(models.Model):
    montoneto_boleta = models.CharField(max_length=25)
    iva_boleta = models.CharField(max_length=25)
    total_boleta = models.CharField(max_length=25)
    

    def str(self):
        return self.montoneto_boleta

