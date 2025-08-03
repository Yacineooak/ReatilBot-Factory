import requests
import json
from datetime import datetime
from typing import Dict, List, Optional

class WhatsAppIntegration:
    """
    Intégration avec l'API WhatsApp Business pour RetailBot Factory
    """
    
    def __init__(self, phone_number_id: str, access_token: str):
        self.phone_number_id = phone_number_id
        self.access_token = access_token
        self.base_url = f"https://graph.facebook.com/v18.0/{phone_number_id}"
        self.headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }
    
    def test_connection(self) -> Dict:
        """
        Tester la connexion à l'API WhatsApp Business
        """
        try:
            response = requests.get(
                f"https://graph.facebook.com/v18.0/{self.phone_number_id}",
                headers=self.headers
            )
            
            if response.status_code == 200:
                data = response.json()
                return {
                    'success': True,
                    'phone_number': data.get('display_phone_number'),
                    'verified_name': data.get('verified_name'),
                    'status': 'connected'
                }
            else:
                return {
                    'success': False,
                    'error': f"Erreur API: {response.status_code}"
                }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def send_text_message(self, to: str, message: str) -> Dict:
        """
        Envoyer un message texte
        """
        try:
            payload = {
                "messaging_product": "whatsapp",
                "to": to,
                "type": "text",
                "text": {
                    "body": message
                }
            }
            
            response = requests.post(
                f"{self.base_url}/messages",
                headers=self.headers,
                json=payload
            )
            
            if response.status_code == 200:
                result = response.json()
                return {
                    'success': True,
                    'message_id': result['messages'][0]['id'],
                    'status': 'sent'
                }
            else:
                return {
                    'success': False,
                    'error': f"Erreur envoi: {response.status_code}",
                    'details': response.text
                }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def send_template_message(self, to: str, template_name: str, language: str = "fr", parameters: List[str] = None) -> Dict:
        """
        Envoyer un message template
        """
        try:
            components = []
            if parameters:
                components.append({
                    "type": "body",
                    "parameters": [{"type": "text", "text": param} for param in parameters]
                })
            
            payload = {
                "messaging_product": "whatsapp",
                "to": to,
                "type": "template",
                "template": {
                    "name": template_name,
                    "language": {
                        "code": language
                    },
                    "components": components
                }
            }
            
            response = requests.post(
                f"{self.base_url}/messages",
                headers=self.headers,
                json=payload
            )
            
            if response.status_code == 200:
                result = response.json()
                return {
                    'success': True,
                    'message_id': result['messages'][0]['id'],
                    'template': template_name,
                    'status': 'sent'
                }
            else:
                return {
                    'success': False,
                    'error': f"Erreur template: {response.status_code}",
                    'details': response.text
                }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def send_interactive_message(self, to: str, header: str, body: str, buttons: List[Dict]) -> Dict:
        """
        Envoyer un message interactif avec boutons
        """
        try:
            interactive_buttons = []
            for i, button in enumerate(buttons[:3]):  # Max 3 boutons
                interactive_buttons.append({
                    "type": "reply",
                    "reply": {
                        "id": f"btn_{i}",
                        "title": button['title'][:20]  # Max 20 caractères
                    }
                })
            
            payload = {
                "messaging_product": "whatsapp",
                "to": to,
                "type": "interactive",
                "interactive": {
                    "type": "button",
                    "header": {
                        "type": "text",
                        "text": header
                    },
                    "body": {
                        "text": body
                    },
                    "action": {
                        "buttons": interactive_buttons
                    }
                }
            }
            
            response = requests.post(
                f"{self.base_url}/messages",
                headers=self.headers,
                json=payload
            )
            
            if response.status_code == 200:
                result = response.json()
                return {
                    'success': True,
                    'message_id': result['messages'][0]['id'],
                    'type': 'interactive',
                    'status': 'sent'
                }
            else:
                return {
                    'success': False,
                    'error': f"Erreur interactive: {response.status_code}",
                    'details': response.text
                }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def send_list_message(self, to: str, header: str, body: str, button_text: str, sections: List[Dict]) -> Dict:
        """
        Envoyer un message avec liste de choix
        """
        try:
            list_sections = []
            for section in sections:
                rows = []
                for row in section.get('rows', [])[:10]:  # Max 10 rows par section
                    rows.append({
                        "id": row['id'],
                        "title": row['title'][:24],  # Max 24 caractères
                        "description": row.get('description', '')[:72]  # Max 72 caractères
                    })
                
                list_sections.append({
                    "title": section['title'][:24],
                    "rows": rows
                })
            
            payload = {
                "messaging_product": "whatsapp",
                "to": to,
                "type": "interactive",
                "interactive": {
                    "type": "list",
                    "header": {
                        "type": "text",
                        "text": header
                    },
                    "body": {
                        "text": body
                    },
                    "action": {
                        "button": button_text[:20],
                        "sections": list_sections
                    }
                }
            }
            
            response = requests.post(
                f"{self.base_url}/messages",
                headers=self.headers,
                json=payload
            )
            
            if response.status_code == 200:
                result = response.json()
                return {
                    'success': True,
                    'message_id': result['messages'][0]['id'],
                    'type': 'list',
                    'status': 'sent'
                }
            else:
                return {
                    'success': False,
                    'error': f"Erreur liste: {response.status_code}",
                    'details': response.text
                }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def send_media_message(self, to: str, media_type: str, media_url: str, caption: str = None) -> Dict:
        """
        Envoyer un message média (image, document, etc.)
        """
        try:
            media_object = {
                "link": media_url
            }
            
            if caption and media_type == "image":
                media_object["caption"] = caption
            
            payload = {
                "messaging_product": "whatsapp",
                "to": to,
                "type": media_type,
                media_type: media_object
            }
            
            response = requests.post(
                f"{self.base_url}/messages",
                headers=self.headers,
                json=payload
            )
            
            if response.status_code == 200:
                result = response.json()
                return {
                    'success': True,
                    'message_id': result['messages'][0]['id'],
                    'media_type': media_type,
                    'status': 'sent'
                }
            else:
                return {
                    'success': False,
                    'error': f"Erreur média: {response.status_code}",
                    'details': response.text
                }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def mark_as_read(self, message_id: str) -> Dict:
        """
        Marquer un message comme lu
        """
        try:
            payload = {
                "messaging_product": "whatsapp",
                "status": "read",
                "message_id": message_id
            }
            
            response = requests.post(
                f"{self.base_url}/messages",
                headers=self.headers,
                json=payload
            )
            
            if response.status_code == 200:
                return {
                    'success': True,
                    'message_id': message_id,
                    'status': 'read'
                }
            else:
                return {
                    'success': False,
                    'error': f"Erreur lecture: {response.status_code}"
                }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def process_webhook(self, webhook_data: Dict) -> Dict:
        """
        Traiter les données du webhook WhatsApp
        """
        try:
            if 'entry' not in webhook_data:
                return {'success': False, 'error': 'Format webhook invalide'}
            
            for entry in webhook_data['entry']:
                for change in entry.get('changes', []):
                    value = change.get('value', {})
                    
                    # Messages entrants
                    if 'messages' in value:
                        for message in value['messages']:
                            return {
                                'success': True,
                                'type': 'message',
                                'from': message['from'],
                                'id': message['id'],
                                'timestamp': message['timestamp'],
                                'message_type': message['type'],
                                'content': self._extract_message_content(message)
                            }
                    
                    # Statuts de livraison
                    elif 'statuses' in value:
                        for status in value['statuses']:
                            return {
                                'success': True,
                                'type': 'status',
                                'id': status['id'],
                                'status': status['status'],
                                'timestamp': status['timestamp'],
                                'recipient_id': status['recipient_id']
                            }
            
            return {'success': True, 'type': 'unknown'}
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def _extract_message_content(self, message: Dict) -> str:
        """
        Extraire le contenu d'un message selon son type
        """
        message_type = message['type']
        
        if message_type == 'text':
            return message['text']['body']
        elif message_type == 'button':
            return message['button']['text']
        elif message_type == 'interactive':
            if 'button_reply' in message['interactive']:
                return message['interactive']['button_reply']['title']
            elif 'list_reply' in message['interactive']:
                return message['interactive']['list_reply']['title']
        elif message_type == 'image':
            return f"[Image] {message.get('image', {}).get('caption', '')}"
        elif message_type == 'document':
            return f"[Document] {message.get('document', {}).get('filename', '')}"
        elif message_type == 'audio':
            return "[Message vocal]"
        elif message_type == 'video':
            return "[Vidéo]"
        
        return f"[{message_type}]"

