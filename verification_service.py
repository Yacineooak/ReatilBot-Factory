import random
import string
from typing import Dict, Any
from datetime import datetime, timedelta
from src.services.notification_service import NotificationService

class VerificationService:
    """
    Service de vérification pour les commandes COD à haut risque
    """
    
    def __init__(self):
        self.notification_service = NotificationService()
        
        # Codes de vérification temporaires (en production, utiliser Redis ou base de données)
        self.verification_codes = {}
        
        # Configuration des méthodes de vérification
        self.verification_methods = {
            'phone_call': {
                'name': 'Appel téléphonique',
                'timeout_minutes': 30,
                'max_attempts': 3
            },
            'sms': {
                'name': 'SMS avec code',
                'timeout_minutes': 15,
                'max_attempts': 3
            },
            'whatsapp': {
                'name': 'Message WhatsApp',
                'timeout_minutes': 20,
                'max_attempts': 3
            }
        }
    
    def initiate_verification(self, order_id: int) -> Dict[str, Any]:
        """
        Initier le processus de vérification pour une commande
        """
        try:
            from src.models.management import CODOrder
            
            order = CODOrder.query.get(order_id)
            if not order:
                return {'success': False, 'error': 'Commande non trouvée'}
            
            # Générer un code de vérification
            verification_code = self._generate_verification_code()
            
            # Stocker le code avec expiration
            self.verification_codes[order.order_id] = {
                'code': verification_code,
                'created_at': datetime.utcnow(),
                'expires_at': datetime.utcnow() + timedelta(minutes=15),
                'attempts': 0,
                'verified': False
            }
            
            # Envoyer le code par SMS par défaut
            success = self._send_verification_code(order, verification_code, 'sms')
            
            return {
                'success': success,
                'verification_code': verification_code,  # À retirer en production
                'method': 'sms',
                'expires_in_minutes': 15
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def verify_order(self, order_id: int, method: str = 'sms') -> Dict[str, Any]:
        """
        Vérifier une commande avec la méthode spécifiée
        """
        try:
            from src.models.management import CODOrder
            
            order = CODOrder.query.get(order_id)
            if not order:
                return {'success': False, 'error': 'Commande non trouvée'}
            
            if method == 'phone_call':
                return self._verify_by_phone_call(order)
            elif method == 'sms':
                return self._verify_by_sms(order)
            elif method == 'whatsapp':
                return self._verify_by_whatsapp(order)
            else:
                return {'success': False, 'error': 'Méthode de vérification non supportée'}
                
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def verify_code(self, order_id: str, provided_code: str) -> Dict[str, Any]:
        """
        Vérifier un code de vérification fourni par le client
        """
        try:
            verification_data = self.verification_codes.get(order_id)
            
            if not verification_data:
                return {'success': False, 'error': 'Code de vérification non trouvé'}
            
            # Vérifier l'expiration
            if datetime.utcnow() > verification_data['expires_at']:
                del self.verification_codes[order_id]
                return {'success': False, 'error': 'Code de vérification expiré'}
            
            # Incrémenter les tentatives
            verification_data['attempts'] += 1
            
            # Vérifier le nombre maximum de tentatives
            if verification_data['attempts'] > 3:
                del self.verification_codes[order_id]
                return {'success': False, 'error': 'Nombre maximum de tentatives dépassé'}
            
            # Vérifier le code
            if provided_code == verification_data['code']:
                verification_data['verified'] = True
                return {
                    'success': True,
                    'message': 'Code vérifié avec succès',
                    'verified_at': datetime.utcnow().isoformat()
                }
            else:
                return {
                    'success': False, 
                    'error': 'Code incorrect',
                    'attempts_remaining': 3 - verification_data['attempts']
                }
                
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _verify_by_phone_call(self, order) -> Dict[str, Any]:
        """
        Vérification par appel téléphonique (simulation)
        """
        # Dans une vraie implémentation, ceci déclencherait un appel automatisé
        # ou programmerait un appel manuel
        
        # Simulation d'un appel réussi (70% de chance)
        success = random.random() < 0.7
        
        if success:
            return {
                'success': True,
                'method': 'phone_call',
                'message': f'Appel programmé vers {order.customer_phone}',
                'estimated_call_time': (datetime.utcnow() + timedelta(minutes=5)).isoformat(),
                'instructions': 'Le client recevra un appel dans les 5 prochaines minutes'
            }
        else:
            return {
                'success': False,
                'method': 'phone_call',
                'error': 'Impossible de programmer l\'appel',
                'alternative': 'Essayez la vérification par SMS'
            }
    
    def _verify_by_sms(self, order) -> Dict[str, Any]:
        """
        Vérification par SMS avec code
        """
        # Générer un code de vérification
        verification_code = self._generate_verification_code()
        
        # Stocker le code
        self.verification_codes[order.order_id] = {
            'code': verification_code,
            'created_at': datetime.utcnow(),
            'expires_at': datetime.utcnow() + timedelta(minutes=15),
            'attempts': 0,
            'verified': False
        }
        
        # Envoyer le SMS
        success = self._send_verification_code(order, verification_code, 'sms')
        
        if success:
            return {
                'success': True,
                'method': 'sms',
                'message': f'Code de vérification envoyé par SMS à {order.customer_phone}',
                'expires_in_minutes': 15,
                'verification_code': verification_code  # À retirer en production
            }
        else:
            return {
                'success': False,
                'method': 'sms',
                'error': 'Échec de l\'envoi du SMS',
                'alternative': 'Essayez la vérification par appel téléphonique'
            }
    
    def _verify_by_whatsapp(self, order) -> Dict[str, Any]:
        """
        Vérification par message WhatsApp
        """
        # Générer un code de vérification
        verification_code = self._generate_verification_code()
        
        # Stocker le code
        self.verification_codes[order.order_id] = {
            'code': verification_code,
            'created_at': datetime.utcnow(),
            'expires_at': datetime.utcnow() + timedelta(minutes=20),
            'attempts': 0,
            'verified': False
        }
        
        # Envoyer le message WhatsApp
        success = self._send_verification_code(order, verification_code, 'whatsapp')
        
        if success:
            return {
                'success': True,
                'method': 'whatsapp',
                'message': f'Code de vérification envoyé par WhatsApp à {order.customer_phone}',
                'expires_in_minutes': 20,
                'verification_code': verification_code  # À retirer en production
            }
        else:
            return {
                'success': False,
                'method': 'whatsapp',
                'error': 'Échec de l\'envoi du message WhatsApp',
                'alternative': 'Essayez la vérification par SMS'
            }
    
    def _generate_verification_code(self, length: int = 6) -> str:
        """
        Générer un code de vérification aléatoire
        """
        return ''.join(random.choices(string.digits, k=length))
    
    def _send_verification_code(self, order, code: str, method: str) -> bool:
        """
        Envoyer le code de vérification via la méthode spécifiée
        """
        try:
            if method == 'sms':
                message = f"""
🔐 Code de vérification RetailBot

Commande: #{order.order_id}
Code: {code}

Ce code expire dans 15 minutes.
Répondez avec ce code pour confirmer votre commande.
                """.strip()
                
                return self.notification_service.send_notification(
                    channel='sms',
                    recipient=order.customer_phone,
                    subject=None,
                    message=message
                )
            
            elif method == 'whatsapp':
                message = f"""
🔐 *Code de vérification RetailBot*

Commande: #{order.order_id}
Code: *{code}*

Ce code expire dans 20 minutes.
Répondez avec ce code pour confirmer votre commande.

Merci de votre confiance ! 🛍️
                """.strip()
                
                return self.notification_service.send_notification(
                    channel='whatsapp',
                    recipient=order.customer_phone,
                    subject=None,
                    message=message
                )
            
            return False
            
        except Exception as e:
            print(f"Erreur envoi code de vérification: {e}")
            return False
    
    def get_verification_status(self, order_id: str) -> Dict[str, Any]:
        """
        Obtenir le statut de vérification d'une commande
        """
        verification_data = self.verification_codes.get(order_id)
        
        if not verification_data:
            return {
                'status': 'not_initiated',
                'message': 'Aucune vérification en cours'
            }
        
        # Vérifier l'expiration
        if datetime.utcnow() > verification_data['expires_at']:
            del self.verification_codes[order_id]
            return {
                'status': 'expired',
                'message': 'Code de vérification expiré'
            }
        
        if verification_data['verified']:
            return {
                'status': 'verified',
                'message': 'Commande vérifiée avec succès'
            }
        
        time_remaining = verification_data['expires_at'] - datetime.utcnow()
        minutes_remaining = int(time_remaining.total_seconds() / 60)
        
        return {
            'status': 'pending',
            'message': 'En attente de vérification',
            'attempts': verification_data['attempts'],
            'max_attempts': 3,
            'minutes_remaining': minutes_remaining
        }
    
    def cancel_verification(self, order_id: str) -> Dict[str, Any]:
        """
        Annuler une vérification en cours
        """
        if order_id in self.verification_codes:
            del self.verification_codes[order_id]
            return {
                'success': True,
                'message': 'Vérification annulée'
            }
        else:
            return {
                'success': False,
                'message': 'Aucune vérification en cours pour cette commande'
            }
    
    def get_verification_statistics(self) -> Dict[str, Any]:
        """
        Obtenir les statistiques de vérification
        """
        from src.models.management import CODOrder
        
        # Statistiques des 30 derniers jours
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        
        total_orders = CODOrder.query.filter(
            CODOrder.created_at >= thirty_days_ago
        ).count()
        
        verification_required = CODOrder.query.filter(
            CODOrder.created_at >= thirty_days_ago,
            CODOrder.verification_required == True
        ).count()
        
        verified_orders = CODOrder.query.filter(
            CODOrder.created_at >= thirty_days_ago,
            CODOrder.verification_status == 'verified'
        ).count()
        
        failed_verifications = CODOrder.query.filter(
            CODOrder.created_at >= thirty_days_ago,
            CODOrder.verification_status == 'failed'
        ).count()
        
        # Calculs des taux
        verification_rate = (verification_required / total_orders * 100) if total_orders > 0 else 0
        success_rate = (verified_orders / verification_required * 100) if verification_required > 0 else 0
        
        return {
            'period_days': 30,
            'total_orders': total_orders,
            'verification_required': verification_required,
            'verified_orders': verified_orders,
            'failed_verifications': failed_verifications,
            'verification_rate': round(verification_rate, 2),
            'success_rate': round(success_rate, 2),
            'active_verifications': len(self.verification_codes)
        }

