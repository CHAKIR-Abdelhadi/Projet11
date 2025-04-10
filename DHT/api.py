from .models import Dht11
from .serializers import DHT11serialize
from rest_framework.decorators import api_view
from rest_framework import status
from rest_framework.response import Response
from django.core.mail import send_mail
from django.conf import settings
from twilio.rest import Client
import requests
import logging

# Configurer le logging
logger = logging.getLogger(__name__)


def send_telegram_message(token, chat_id, message):
    """Fonction pour envoyer des messages Telegram"""
    try:
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        payload = {
            'chat_id': chat_id,  # Correction: clé correcte pour l'ID de chat
            'text': message  # Correction: clé correcte pour le message
        }
        response = requests.post(url, data=payload)
        response.raise_for_status()  # Lève une exception pour les codes HTTP 4xx/5xx
        logger.info("Message Telegram envoyé avec succès")
        return True
    except requests.exceptions.RequestException as e:
        logger.error(f"Erreur lors de l'envoi Telegram: {e}")
        return False


@api_view(["GET", "POST"])
def Dlist(request):
    if request.method == "GET":
        try:
            all_data = Dht11.objects.all().order_by('-id')  # Tri par ID descendant
            data_ser = DHT11serialize(all_data, many=True)
            return Response(data_ser.data)
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des données: {e}")
            return Response(
                {"error": "Erreur lors de la récupération des données"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    elif request.method == "POST":
        serializer = DHT11serialize(data=request.data)

        if not serializer.is_valid():
            logger.error(f"Données invalides: {serializer.errors}")
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            # Sauvegarder les données
            dht_instance = serializer.save()
            derniere_temperature = dht_instance.temp
            logger.info(f"Nouvelle donnée enregistrée - Température: {derniere_temperature}")

            # Vérifier si la température dépasse le seuil
            if derniere_temperature > 25:
                alert_message = 'La température dépasse le seuil de 25°C, veuillez intervenir immédiatement pour vérifier et corriger cette situation'

                # Envoyer l'email
                if hasattr(settings, 'EMAIL_HOST_USER') and hasattr(settings, 'ALERT_EMAIL'):
                    try:
                        send_mail(
                            subject='Alerte Température',
                            message=alert_message,
                            from_email=settings.EMAIL_HOST_USER,
                            recipient_list=[settings.ALERT_EMAIL],
                            fail_silently=False
                        )
                        logger.info("Email d'alerte envoyé avec succès")
                    except Exception as e:
                        logger.error(f"Erreur lors de l'envoi de l'email: {e}")

                # Envoyer WhatsApp (si configuré)
                if all(hasattr(settings, attr) for attr in ['TWILIO_ACCOUNT_SID', 'TWILIO_AUTH_TOKEN', 'TWILIO_PHONE_NUMBER', 'ALERT_PHONE_NUMBER']):
                    try:
                        client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
                        message_whatsapp = client.messages.create(
                            from_=f'whatsapp:{settings.TWILIO_PHONE_NUMBER}',
                            body=alert_message,  # Utilisation du message d'alerte cohérent
                            to=f'whatsapp:{settings.ALERT_PHONE_NUMBER}'
                        )
                        logger.info(f"Message WhatsApp envoyé: {message_whatsapp.sid}")
                    except Exception as e:
                        logger.error(f"Erreur lors de l'envoi WhatsApp: {e}")

                # Envoyer Telegram (si configuré)
                if all(hasattr(settings, attr) for attr in ['TELEGRAM_TOKEN', 'TELEGRAM_CHAT_ID']):
                    telegram_sent = send_telegram_message(
                        token=settings.TELEGRAM_TOKEN,
                        chat_id=settings.TELEGRAM_CHAT_ID,
                        message=alert_message  # Utilisation du message d'alerte cohérent
                    )
                    if not telegram_sent:
                        logger.warning("Échec de l'envoi du message Telegram")

            return Response(serializer.data, status=status.HTTP_201_CREATED)

        except Exception as e:
            logger.error(f"Erreur lors de l'enregistrement des données: {e}")
            return Response(
                {"error": "Erreur lors du traitement des données"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )