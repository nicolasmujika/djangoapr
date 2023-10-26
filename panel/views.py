import datetime
from django import forms
from django.shortcuts import render, redirect, get_object_or_404
from django.http import  HttpResponse, HttpResponseRedirect
import requests
from .forms import FiltroSectoresForm
from django.utils.timezone import now
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Usuario, Notificacion, Proveedor, Tarifa
from django.contrib.auth import authenticate, login as auth_login  # Cambiamos el alias de la función de login
from django.urls import reverse
from django.contrib.auth.hashers import make_password
from django.contrib.auth import get_user_model
from django.contrib.auth import get_user_model
from django.template import loader
from django.shortcuts import render
from datetime import date
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
from django.template.loader import get_template
from io import BytesIO
from .decorators import user_type_required
from django.http import JsonResponse
import mercadopago
from django.conf import settings

# Create your views here.
TEMPLATE_DIRS = (
    'os.path.join(BASE_DIR, "templates")'
)

#admin
@user_type_required('administrador')
def index(request):
    return render(request, "index.html")
#usuario sin logearse
def inicio(request):
    return render(request, "home/inicio.html")
#operador
@user_type_required('operador')
def perfiloperador(request):
    return render(request, "operador/perfiloperador.html")
#cliente
def perfilcliente(request):
    return render(request, "cliente/perfilcliente.html")
#cliente
def pagina_de_pago(request):
    return render(request, 'cliente/pagina_de_pago.html')
#cliente
def detalle_cliente(request):
    return render(request, 'cliente/detalle_cliente.html')
#admin
@user_type_required('administrador')
def generar_boleta_pdf(request):

    
    # Obtener el usuario actual
    usuario = request.user

    # Comprobar si el usuario tiene el campo "rut" definido y no es nulo
    if hasattr(usuario, 'rut') and usuario.rut:
        rut = usuario.rut
    else:
        rut = "RUT del Cliente"

    # Comprobar si el usuario tiene los campos "nombres" y "apellidos" definidos
    if hasattr(usuario, 'nombres') and hasattr(usuario, 'apellidos'):
        nombres = usuario.nombres
        apellidos = usuario.apellidos
    else:
        nombres = "Nombre del Cliente"
        apellidos = "Apellidos del Cliente"

    # Otros datos de la boleta (puedes obtenerlos de tu base de datos)
    numero_boleta = "12345"
    consumo_metros_cubicos = 100
    total_pagar = "$250.00"

    # Determinar el tipo de usuario y obtener los datos específicos
    if usuario.usuario_tipo == 'cliente':
        sector = usuario.sectores
    else:
        # Maneja otros tipos de usuarios (operador, administrador) si es necesario
        sector = ""

    context = {
        'numero_boleta': numero_boleta,
        'nombres': nombres,
        'apellidos': apellidos,
        'rut': rut,
        'consumo_metros_cubicos': consumo_metros_cubicos,
        'sector': sector,
        'total_pagar': total_pagar
    }

    template = get_template('boleta_template.html')
    html = template.render(context)

    # Crear un objeto BytesIO para el PDF
    response = BytesIO()
    pdf = pisa.pisaDocument(BytesIO(html.encode("UTF-8")), response)

    if not pdf.err:
        response = HttpResponse(response.getvalue(), content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="boleta.pdf"'
        return response
    
    return HttpResponse("Error al generar la boleta PDF")


def login_view(request):
    if request.method == 'POST':
        email = request.POST['email']  # Cambia 'username' por 'email'
        password = request.POST['password']
        user = authenticate(request, email=email, password=password)  # Cambia 'username' por 'email'

        if user is not None:
            login(request, user)
            if user.usuario_tipo == 'operador':
                return redirect('perfiloperador')  # Redirigir al usuario operador a la página de iniciocli.html
            elif user.usuario_tipo == 'administrador':
                return redirect('index')  # Redirigir al usuario administrador a la página index.html
            else:
                messages.error(request, 'Usuario no válido')  # Mensaje de error si el tipo de usuario no es operador ni administrador
        else:
            messages.error(request, 'Credenciales incorrectas')

    return render(request, 'home/login.html')

#LOGIN RUT
def login_rut(request):
    if request.method == 'POST':
        rut = request.POST['rut']  # Asumiendo que el campo se llama 'rut' en tu formulario
        try:
            usuario = Usuario.objects.get(rut=rut)
            if usuario.usuario_tipo == 'cliente':
                # Autenticar al usuario y redirigir a su perfil
                login(request, usuario)
                return HttpResponseRedirect(reverse('perfilcliente'))
            elif usuario.usuario_tipo == 'operador':
                return HttpResponseRedirect(reverse('login'))
            elif usuario.usuario_tipo == 'administrador':
                return HttpResponseRedirect(reverse('login'))
        except Usuario.DoesNotExist:
            messages.error(request, 'Usuario no encontrado')

    return render(request, "home/login_rut.html")



#admin y operador    
# Vista para listar a todos los usuarios tipo cliente
def lista_clientes(request):
    usuarios = Usuario.objects.filter(usuario_tipo='cliente')  # Filtrar solo usuarios de tipo 'cliente'

    if request.method == 'POST':
        form = FiltroSectoresForm(request.POST)
        if form.is_valid():
            sectores = form.cleaned_data['sectores']
            if sectores:
                usuarios = usuarios.filter(sectores=sectores)

            # Agregar el filtro por rut
            rut = form.cleaned_data.get('rut')

            if rut:
                usuarios = usuarios.filter(rut=rut)

    return render(request, 'usuarios/lista.html', {'form': form, 'usuarios': usuarios})


@user_type_required(['administrador', 'operador'])
def lista(request):
    if request.method == 'POST':
        correo = request.POST.get('correo')
        if correo:
            try:
                user = Usuario.objects.get(correo=correo, usuario_tipo='cliente')
                user.delete()
                messages.success(request, f'Cliente {correo} eliminado correctamente.')
            except Usuario.DoesNotExist:
                messages.error(request, f'Cliente con correo {correo} no encontrado.')
        else:
            messages.error(request, 'Debes proporcionar un correo para eliminar un cliente.')

    usuarios = Usuario.objects.filter(usuario_tipo='cliente')
    datos = {'usuarios': usuarios}
    return render(request, "usuarios/lista.html", datos)


def autenticar_usuario_por_rut(request, rut):
    # Intenta autenticar al usuario por su rut
    user = authenticate(request, rut=rut)

    if user is not None:
        # Si el usuario existe, inicia sesión
        login(request, user)
        return HttpResponse("Autenticado con éxito")
    else:
        # Si el usuario no existe, devuelve un mensaje de error o redirige a donde sea necesario
        return HttpResponse("Error de autenticación")



#admin
@user_type_required('administrador')
# Vista para agregar un usuario tipo cliente
def agregar(request):
    if request.method == 'POST':
        nombre = request.POST.get('nombre')
        apellido = request.POST.get('apellido')
        rut = request.POST.get('rut')
        correo = request.POST.get('correo')
        telefono = request.POST.get('telefono')
        sectores = request.POST.get('sectores')
        numero_medidor = request.POST.get('numero_medidor')  # Obtén el valor del campo "numero_medidor"
        usuario_tipo = 'cliente'

        # Crea un usuario sin contraseña
        usuario = Usuario(
            email=correo,
            nombres=nombre,
            apellidos=apellido,
            rut=rut,
            telefono=telefono,
            usuario_tipo=usuario_tipo,
            sectores=sectores,
            numero_medidor=numero_medidor  # Asigna el valor del campo numero_medidor
        )

        # Guarda el usuario sin contraseña
        usuario.save()

        # Intenta autenticar al usuario por rut
        user = authenticate(request, rut=rut)

        if user is not None:
            # Si el usuario existe, inicia sesión
            login(request, user)
            return redirect('lista')  # Redirige a la página de lista o a donde desees

    return render(request, "usuarios/agregar.html")

#admin
@user_type_required('administrador')
# Vista para actualizar un usuario tipo cliente
def actualizar(request, user_id):
    user = Usuario.objects.get(id=user_id)

    if request.method == 'POST':
        user.nombres = request.POST.get('nombre')
        user.apellidos = request.POST.get('apellido')
        user.rut = request.POST.get('rut')
        user.email = request.POST.get('correo')
        user.telefono = request.POST.get('telefono')
        user.sectores = request.POST.get('sectores')  # Actualizar sectores
        user.save()
        return redirect('lista')

    datos = {'usuario': user}
    return render(request, "usuarios/actualizar.html", datos)

#admin
@user_type_required('administrador')
# Vista para eliminar un usuario tipo cliente
def eliminar(request):
    if request.method == 'POST':
        correo = request.POST.get('correo')  # Obtiene el correo del formulario POST
        try:
            usuario = Usuario.objects.get(email=correo, usuario_tipo='cliente')
            usuario.delete()
            return redirect('lista')  # Redirige a la lista de clientes después de eliminar
        except Usuario.DoesNotExist:
            # Maneja el caso donde no se encuentra al cliente
            return HttpResponse("Cliente no encontrado")

    users = Usuario.objects.filter(usuario_tipo='cliente')
    datos = {'usuarios': users}
    return render(request, "usuarios/lista.html", datos)

#admin
# Vista para listar a todos los usuarios tipo operador
from django.contrib import messages

@user_type_required('administrador')
def listaop(request):
    if request.method == 'POST':
        username = request.POST.get('username_op')
        if username:
            try:
                user = Usuario.objects.get(username=username, usuario_tipo='operador')
                user.delete()
                messages.success(request, f'Operador {username} eliminado correctamente.')
            except Usuario.DoesNotExist:
                messages.error(request, f'Operador con username {username} no encontrado.')
        else:
            messages.error(request, 'Debes proporcionar un username para eliminar un operador.')

    operadores = Usuario.objects.filter(usuario_tipo='operador')
    datos = {'operadores': operadores}
    return render(request, "operador/olista.html", datos)

#admin
@user_type_required('administrador')
# Vista para agregar un usuario tipo operador
def agregarop(request):
    if request.method == 'POST':
        nombre = request.POST.get('nombre_op')
        apellido = request.POST.get('apellido_op')
        rut = request.POST.get('rut_op')
        correo = request.POST.get('correo_op')
        contrasena = request.POST.get('password')
        telefono = request.POST.get('telefono_op')
        usuario_tipo = 'operador'

        # Utiliza get_user_model() para obtener el modelo de usuario personalizado
        User = get_user_model()

        # Crea un nuevo usuario operador con contraseña segura
        operador = User(
            email=correo,
            nombres=nombre,
            apellidos=apellido,
            rut=rut,
            telefono=telefono,
            usuario_tipo=usuario_tipo
        )
        operador.set_password(contrasena)  # Almacena la contraseña de manera segura
        operador.save()

        return redirect('listaop')

    return render(request, "operador/oagregar.html")
"""
# Vista para actualizar un usuario tipo operador
def actualizarop(request, user_id):
    user = Usuario.objects.get(id=user_id)

    if request.method == 'POST':
        user.nombres = request.POST.get('nombre')
        user.apellidos = request.POST.get('apellido')
        user.rut = request.POST.get('rut')
        user.email = request.POST.get('correo')
        user.telefono = request.POST.get('telefono')
        user.save()
        return redirect('listaop')

    datos = {'usuario': user}
    return render(request, "operador/oactualizar.html", datos)
"""
#admin
@user_type_required('administrador')
# Vista para eliminar un usuario tipo operador
def eliminarop(request, email):
    if request.method == 'POST':
        try:
            usuario = Usuario.objects.get(email=email, usuario_tipo='operador')
            usuario.delete()
            return redirect('listaop')  # Redirige a la lista de operadores después de eliminar
        except Usuario.DoesNotExist:
            # Maneja el caso donde no se encuentra al operador
            return HttpResponse("Operador no encontrado")

    operadores = Usuario.objects.filter(usuario_tipo='operador')
    datos = {'operadores': operadores}
    return render(request, "operador/olista.html", datos)
#admin
@user_type_required('administrador')
def ingresos(request):
    return render(request, "finanzas/ingresos.html")
#admin
@user_type_required('administrador')
def egresos(request):
    return render(request, "finanzas/egresos.html")
#admin
@user_type_required('administrador')
def saldo(request):
    return render(request, "finanzas/saldo.html")

#admin, operador y cliente
@user_type_required(['administrador', 'operador'])
def crear_notificacion(request):
    if request.method == 'POST':
        titulo = request.POST.get('titulo')
        mensaje = request.POST.get('mensaje')
        Notificacion.objects.create(titulo=titulo, mensaje=mensaje)
        return redirect('centro_notificaciones')
    return render(request, 'notificaciones/crear_notificacion.html')
#admin, operador y cliente
@user_type_required(['administrador', 'operador'])
def centro_notificaciones(request):
    notificaciones = Notificacion.objects.all()
    return render(request, 'notificaciones/centro_notificaciones.html', {'notificaciones': notificaciones})
#admin
@user_type_required('administrador')
def eliminar_notificacion(request, notificacion_id):
    if request.method == 'POST':
        try:
            notificacion = Notificacion.objects.get(id=notificacion_id)
            notificacion.delete()
            return redirect('centro_notificaciones')
        except Notificacion.DoesNotExist:
            messages.error(request, 'La notificación no existe.')
    
    # Si no es una solicitud POST o la notificación no se encuentra, redirige nuevamente a 'centro_notificaciones'
    return redirect('centro_notificaciones')
#cliente
def crear_notificacioncli(request):
    if request.method == 'POST':
        titulo = request.POST.get('titulo')
        mensaje = request.POST.get('mensaje')
        Notificacion.objects.create(titulo=titulo, mensaje=mensaje)
        return redirect('centro_notificacionescli')
    return render(request, 'cliente/crear_notificacioncli.html')
#cliente
def centro_notificacionescli(request):
    notificaciones = Notificacion.objects.all()
    return render(request, 'cliente/centro_notificacionescli.html', {'notificaciones': notificaciones})
#admin
@user_type_required('administrador')
def agregar_proveedor(request):
    if request.method == 'POST':
        nombre = request.POST.get('nombre')
        telefono = request.POST.get('telefono')
        giro = request.POST.get('giro')
        servicio = request.POST.get('servicio')
        categoria = request.POST.get('categoria')

        Proveedor.objects.create(
            nombre=nombre,
            telefono=telefono,
            giro=giro,
            servicio=servicio,
            categoria=categoria
        )

        return redirect('lista_proveedores')  # Redirige a la vista de lista de proveedores después de agregar uno

    return render(request, 'proveedores/agregar_proveedor.html')
#admin
@user_type_required('administrador')
def lista_proveedores(request):
    proveedores = Proveedor.objects.all()
    return render(request, 'proveedores/proveedores.html', {'proveedores': proveedores})
#admin
@user_type_required('administrador')
def eliminar_proveedor(request, proveedor_id):
    if request.method == 'POST':
        try:
            proveedor = Proveedor.objects.get(pk=proveedor_id)
            proveedor.delete()
            return redirect('lista_proveedores')  # Redirige a la lista de proveedores después de eliminar
        except Proveedor.DoesNotExist:
            # Maneja el caso donde no se encuentra al proveedor
            return HttpResponse("Proveedor no encontrado")

    proveedores = Proveedor.objects.all()
    datos = {'proveedores': proveedores}
    return render(request, "proveedores/proveedores.html", datos)

#admin
@user_type_required('administrador')
def agregar_tarifa(request):
    if request.method == 'POST':
        nombre = request.POST.get('nombre')
        monto = request.POST.get('monto')
        descripcion = request.POST.get('descripcion')

        Tarifa.objects.create(
            nombre=nombre,
            monto=monto,
            descripcion=descripcion
        )

        return redirect('lista_tarifas') 

    return render(request, 'tarifas/tarifas.html')
#admin
@user_type_required('administrador')
def lista_tarifas(request):
    tarifas = Tarifa.objects.all()
    return render(request, 'tarifas/lista_tarifas.html', {'tarifas': tarifas})
#admin
@user_type_required('administrador')
def eliminar_tarifa(request, tarifa_id):
    if request.method == 'POST':
        try:
            tarifa = Tarifa.objects.get(pk=tarifa_id)
            tarifa.delete()
            return redirect('lista_tarifas')  
        except Tarifa.DoesNotExist:
            # Maneja el caso donde no se encuentra la tarifa
            return HttpResponse("Tarifa no encontrada")

    tarifas = Tarifa.objects.all()
    datos = {'tarifas': tarifas}
    return render(request, "tarifas/lista_tarifas.html", datos)
#cliente
def boleta(request):
    return render(request, "cliente/boleta.html")

def volver(request):
    return render(request, "volver.html")

def logout_view(request):
    logout(request)
    return redirect('inicio')



def crear_preferencia(request):
    sdk = mercadopago.SDK(settings.MERCADO_PAGO_ACCESS_TOKEN)

    preference_data = {
        "items": [
            {
                "id": "item-ID-1234",
                "title": "Meu produto",
                "currency_id": "BRL",
                "picture_url": "https://www.mercadopago.com/org-img/MP3/home/logomp3.gif",
                "description": "Descrição do Item",
                "category_id": "art",
                "quantity": 1,
                "unit_price": 75.76
            }
        ],
        # ... Otras configuraciones de preferencia ...
    }

    preference_response = sdk.preference().create(preference_data)
    preference = preference_response["response"]

    return JsonResponse({"preference_id": preference["id"]})

def mercadopago(request):
    # Realiza una llamada a la vista crear_preferencia para obtener el ID de preferencia
    response = requests.get("http://127.0.0.1:8000/panel/crear_preferencia/")
    if response.status_code == 200:
        preference_id = response.json().get("preference_id", "")
    else:
        preference_id = ""

    return render(request, 'mercadopago.html', {'preference_id': preference_id})