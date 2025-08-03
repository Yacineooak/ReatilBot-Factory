import smtplib
import requests
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, Any, Optional
import os

class NotificationService:
    """
    Service de notification pour l'envoi d'emails, SMS et messages WhatsApp
    """
    
    def __init__(self):
        # Configuration email (à adapter selon le fournisseur)
        self.smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
        self.smtp_port = int(os.getenv('SMTP_PORT', 587))
        self.smtp_username = os.getenv('SMTP_USERNAME', '')
        self.smtp_password = os.getenv('SMTP_PASSWORD', '')
        self.from_email = os.getenv('FROM_EMAIL', 'noreply@retailbot.com')
        
        # Configuration SMS (exemple avec un service générique)
        self.sms_api_url = os.getenv('SMS_API_URL', '')
        self.sms_api_key = os.getenv('SMS_API_KEY', '')
        
        # Configuration WhatsApp Business API
        self.whatsapp_api_url = os.getenv('WHATSAPP_API_URL', '')
        self.whatsapp_token = os.getenv('WHATSAPP_TOKEN', '')
    
    def send_notification(self, channel: str, recipient: str, subject: Optional[str], 
                         message: str, cart_id: Optional[int] = None) -> bool:
        """
        Envoyer une notification via le canal spécifié
        """
        try:
            if channel == 'email':
                return self._send_email(recipient, subject, message, cart_id)
            elif channel == 'sms':
                return self._send_sms(recipient, message, cart_id)
            elif channel == 'whatsapp':
                return self._send_whatsapp(recipient, message, cart_id)
            else:
                print(f"Canal de notification non supporté: {channel}")
                return False
                
        except Exception as e:
            print(f"Erreur lors de l'envoi de notification {channel}: {e}")
            return False
    
    def _send_email(self, recipient: str, subject: str, message: str, cart_id: Optional[int] = None) -> bool:
        """
        Envoyer un email
        """
        try:
            # Créer le message email
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = self.from_email
            msg['To'] = recipient
            
            # Ajouter le lien de récupération si cart_id est fourni
            if cart_id:
                recovery_link = f"https://votre-site.com/recover-cart/{cart_id}"
                message = message.replace('[Finaliser ma commande]', f'<a href="{recovery_link}">Finaliser ma commande</a>')
                message = message.replace('[lien]', recovery_link)
            
            # Version HTML du message
            html_message = f"""
            <html>
                <body>
                    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                        {message.replace(chr(10), '<br>')}
                    </div>
                </body>
            </html>
            """
            
            # Ajouter les parties text et HTML
            text_part = MIMEText(message, 'plain', 'utf-8')
            html_part = MIMEText(html_message, 'html', 'utf-8')
            
            msg.attach(text_part)
            msg.attach(html_part)
            
            # Envoyer l'email
            if self.smtp_username and self.smtp_password:
                server = smtplib.SMTP(self.smtp_server, self.smtp_port)
                server.starttls()
                server.login(self.smtp_username, self.smtp_password)
                server.send_message(msg)
                server.quit()
                return True
            else:
                print("Configuration SMTP manquante")
                return False
                
        except Exception as e:
            print(f"Erreur envoi email: {e}")
            return False
    
    def _send_sms(self, recipient: str, message: str, cart_id: Optional[int] = None) -> bool:
        """
        Envoyer un SMS
        """
        try:
            if not self.sms_api_url or not self.sms_api_key:
                print("Configuration SMS manquante")
                return False
            
            # Ajouter le lien de récupération si cart_id est fourni
            if cart_id:
                recovery_link = f"https://votre-site.com/recover-cart/{cart_id}"
                message = message.replace('[lien]', recovery_link)
            
            # Préparer les données pour l'API SMS
            data = {
                'to': recipient,
                'message': message,
                'api_key': self.sms_api_key
            }
            
            # Envoyer la requête
            response = requests.post(self.sms_api_url, json=data, timeout=30)
            
            if response.status_code == 200:
                return True
            else:
                print(f"Erreur API SMS: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"Erreur envoi SMS: {e}")
            return False
    
    def _send_whatsapp(self, recipient: str, message: str, cart_id: Optional[int] = None) -> bool:
        """
        Envoyer un message WhatsApp Business
        """
        try:
            if not self.whatsapp_api_url or not self.whatsapp_token:
                print("Configuration WhatsApp manquante")
                return False
            
            # Ajouter le lien de récupération si cart_id est fourni
            if cart_id:
                recovery_link = f"https://votre-site.com/recover-cart/{cart_id}"
                message = message.replace('[lien]', recovery_link)
            
            # Headers pour l'API WhatsApp
            headers = {
                'Authorization': f'Bearer {self.whatsapp_token}',
                'Content-Type': 'application/json'
            }
            
            # Préparer les données pour l'API WhatsApp
            data = {
                'messaging_product': 'whatsapp',
                'to': recipient,
                'type': 'text',
                'text': {
                    'body': message
                }
            }
            
            # Envoyer la requête
            response = requests.post(self.whatsapp_api_url, json=data, headers=headers, timeout=30)
            
            if response.status_code == 200:
                return True
            else:
                print(f"Erreur API WhatsApp: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"Erreur envoi WhatsApp: {e}")
            return False
    
    def send_inventory_alert(self, recipients: list, alert_type: str, item_name: str, 
                           current_stock: int, threshold: int) -> Dict[str, bool]:
        """
        Envoyer une alerte d'inventaire
        """
        results = {}
        
        # Générer le message d'alerte
        if alert_type == 'low_stock':
            subject = f"🚨 Alerte Stock Faible - {item_name}"
            message = f"""
            Alerte Stock Faible
            
            Produit: {item_name}
            Stock actuel: {current_stock}
            Seuil minimum: {threshold}
            
            Action requise: Réapprovisionner le stock
            
            RetailBot Factory
            """
        elif alert_type == 'out_of_stock':
            subject = f"🔴 Rupture de Stock - {item_name}"
            message = f"""
            Rupture de Stock
            
            Produit: {item_name}
            Stock actuel: {current_stock}
            
            Action urgente: Réapprovisionner immédiatement
            
            RetailBot Factory
            """
        else:
            subject = f"📦 Alerte Inventaire - {item_name}"
            message = f"""
            Alerte Inventaire
            
            Produit: {item_name}
            Stock actuel: {current_stock}
            
            Veuillez vérifier le stock
            
            RetailBot Factory
            """
        
        # Envoyer à tous les destinataires
        for recipient in recipients:
            if '@' in recipient:  # Email
                results[recipient] = self._send_email(recipient, subject, message)
            else:  # SMS/WhatsApp (numéro de téléphone)
                results[recipient] = self._send_sms(recipient, message)
        
        return results
    
    def send_cod_verification(self, phone: str, order_id: str, customer_name: str) -> bool:
        """
        Envoyer une notification de vérification COD
        """
        message = f"""
        🔔 Vérification de Commande
        
        Bonjour {customer_name},
        
        Votre commande #{order_id} nécessite une vérification.
        
        Merci de confirmer votre commande en répondant OUI à ce message.
        
        RetailBot Factory
        """
        
        return self._send_sms(phone, message)
    
    def test_configuration(self) -> Dict[str, bool]:
        """
        Tester la configuration des services de notification
        """
        results = {
            'email': False,
            'sms': False,
            'whatsapp': False
        }
        
        # Test email
        if self.smtp_username and self.smtp_password:
            try:
                server = smtplib.SMTP(self.smtp_server, self.smtp_port)
                server.starttls()
                server.login(self.smtp_username, self.smtp_password)
                server.quit()
                results['email'] = True
            except:
                results['email'] = False
        
        # Test SMS
        if self.sms_api_url and self.sms_api_key:
            results['sms'] = True  # Simulation, test réel nécessiterait un appel API
        
        # Test WhatsApp
        if self.whatsapp_api_url and self.whatsapp_token:
            results['whatsapp'] = True  # Simulation, test réel nécessiterait un appel API
        
        return results

