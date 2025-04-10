from django.shortcuts import render
from .models import Dht11
from django.utils import timezone
import csv
from django.http import HttpResponse, JsonResponse
from datetime import timedelta
import datetime
from django.shortcuts import redirect
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
import telepot  # Ajout de l'import manquant pour telepot


def home(request):
    return render(request, 'home.html')


def table(request):
    derniere_ligne = Dht11.objects.last()
    if not derniere_ligne:  # Gestion du cas où il n'y a pas de données
        return render(request, 'value.html', {'valeurs': None})

    derniere_date = derniere_ligne.dt
    delta_temps = timezone.now() - derniere_date
    difference_minutes = delta_temps.seconds // 60

    if difference_minutes > 60:
        temps_ecoule = f'il y a {difference_minutes // 60}h {difference_minutes % 60}min'
    else:
        temps_ecoule = f'il y a {difference_minutes} min'

    valeurs = {
        'date': temps_ecoule,
        'id': derniere_ligne.id,
        'temp': derniere_ligne.temp,
        'hum': derniere_ligne.hum
    }
    return render(request, 'value.html', {'valeurs': valeurs})


def download_csv(request):
    model_values = Dht11.objects.all()
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="dht.csv"'
    writer = csv.writer(response)
    writer.writerow(['id', 'temp', 'hum', 'dt'])

    # Utilisation de values_list() directement dans la boucle pour économiser de la mémoire
    for row in model_values.values_list('id', 'temp', 'hum', 'dt'):
        writer.writerow(row)
    return response


def index_view(request):
    return render(request, 'index.html')


def graphiqueTemp(request):
    return render(request, 'ChartTemp.html')


def graphiqueHum(request):
    return render(request, 'ChartHum.html')


def chart_data(request):
    dht = Dht11.objects.all()
    data = {
        'temps': [Dt.dt.strftime("%Y-%m-%d %H:%M:%S") for Dt in dht],  # Formatage des dates
        'temperature': [Temp.temp for Temp in dht],
        'humidity': [Hum.hum for Hum in dht]
    }
    return JsonResponse(data)


def chart_data_jour(request):
    now = timezone.now()
    last_24_hours = now - timedelta(hours=24)
    dht = Dht11.objects.filter(dt__range=(last_24_hours, now))

    data = {
        'temps': [Dt.dt.strftime("%Y-%m-%d %H:%M:%S") for Dt in dht],
        'temperature': [Temp.temp for Temp in dht],
        'humidity': [Hum.hum for Hum in dht]
    }
    return JsonResponse(data)


def chart_data_semaine(request):
    date_debut_semaine = timezone.now() - timedelta(days=7)
    dht = Dht11.objects.filter(dt__gte=date_debut_semaine)

    data = {
        'temps': [Dt.dt.strftime("%Y-%m-%d %H:%M:%S") for Dt in dht],
        'temperature': [Temp.temp for Temp in dht],
        'humidity': [Hum.hum for Hum in dht]
    }
    return JsonResponse(data)


def chart_data_mois(request):
    date_debut_mois = timezone.now() - timedelta(days=30)
    dht = Dht11.objects.filter(dt__gte=date_debut_mois)

    data = {
        'temps': [Dt.dt.strftime("%Y-%m-%d %H:%M:%S") for Dt in dht],
        'temperature': [Temp.temp for Temp in dht],
        'humidity': [Hum.hum for Hum in dht]
    }
    return JsonResponse(data)


def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)  # Connecte l'utilisateur après l'inscription
            return redirect('home')  # Redirige vers la page d'accueil
    else:
        form = UserCreationForm()
    return render(request, 'register.html', {'form': form})


def user_login(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('home')
    else:
        form = AuthenticationForm()
    return render(request, 'login.html', {'form': form})


def user_logout(request):
    logout(request)
    return redirect('home')


def sendtele():
    token = '6662023260:AAG4z48OO9gL8A6szdxg0SOma5hv9gIII1E'
    rece_id = 1242839034
    try:
        bot = telepot.Bot(token)
        bot.sendMessage(rece_id, 'La température dépasse la normale!')
        print("Notification Telegram envoyée avec succès")
    except Exception as e:
        print(f"Erreur lors de l'envoi Telegram: {e}")