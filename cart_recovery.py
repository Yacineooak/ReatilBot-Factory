from flask import Blueprint, jsonify, request
from src.models.management import AbandonedCart, AbandonedCartItem, CartRecoveryNotification, CartStatus, NotificationStatus, db
from src.services.notification_service import NotificationService
from datetime import datetime, timedelta
import uuid

cart_recovery_bp = Blueprint('cart_recovery', __name__)

# Initialisation du service de notification
notification_service = NotificationService()

@cart_recovery_bp.route('/abandoned-carts', methods=['GET'])
def get_abandoned_carts():
    """
    Récupérer la liste des paniers abandonnés
    """
    try:
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 20))
        status = request.args.get('status')
        
        query = AbandonedCart.query
        
        if status:
            query = query.filter(AbandonedCart.status == CartStatus(status))
        
        # Trier par date d'abandon (plus récent en premier)
        query = query.order_by(AbandonedCart.abandoned_at.desc())
        
        carts = query.paginate(
            page=page, 
            per_page=per_page, 
            error_out=False
        )
        
        return jsonify({
            'carts': [cart.to_dict() for cart in carts.items],
            'total': carts.total,
            'pages': carts.pages,
            'current_page': page,
            'per_page': per_page
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@cart_recovery_bp.route('/abandoned-carts', methods=['POST'])
def create_abandoned_cart():
    """
    Créer un nouveau panier abandonné
    """
    try:
        data = request.json
        
        # Validation des données requises
        required_fields = ['session_id', 'cart_value', 'items']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Champ requis manquant: {field}'}), 400
        
        # Vérifier si le panier existe déjà
        existing_cart = AbandonedCart.query.filter_by(session_id=data['session_id']).first()
        if existing_cart:
            return jsonify({'error': 'Panier déjà enregistré'}), 409
        
        # Créer le panier abandonné
        cart = AbandonedCart(
            session_id=data['session_id'],
            user_id=data.get('user_id'),
            email=data.get('email'),
            phone=data.get('phone'),
            cart_value=data['cart_value'],
            currency=data.get('currency', 'DZD'),
            items_count=len(data['items']),
            status=CartStatus.ABANDONED
        )
        
        db.session.add(cart)
        db.session.flush()  # Pour obtenir l'ID du panier
        
        # Ajouter les articles du panier
        for item_data in data['items']:
            item = AbandonedCartItem(
                cart_id=cart.id,
                product_id=item_data['product_id'],
                product_name=item_data['product_name'],
                product_price=item_data['product_price'],
                quantity=item_data.get('quantity', 1),
                variant_id=item_data.get('variant_id'),
                variant_name=item_data.get('variant_name'),
                image_url=item_data.get('image_url')
            )
            db.session.add(item)
        
        db.session.commit()
        
        # Programmer les notifications de récupération
        schedule_recovery_notifications(cart.id)
        
        return jsonify(cart.to_dict()), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@cart_recovery_bp.route('/abandoned-carts/<int:cart_id>/recover', methods=['POST'])
def trigger_recovery(cart_id):
    """
    Déclencher manuellement une campagne de récupération
    """
    try:
        cart = AbandonedCart.query.get_or_404(cart_id)
        
        if cart.status != CartStatus.ABANDONED:
            return jsonify({'error': 'Le panier n\'est pas dans un état abandonné'}), 400
        
        data = request.json
        channels = data.get('channels', ['email'])  # Par défaut email
        message_template = data.get('message_template', 'default')
        
        notifications_sent = []
        
        for channel in channels:
            if channel == 'email' and cart.email:
                notification = send_recovery_notification(cart, 'email', cart.email, message_template)
                notifications_sent.append(notification)
            elif channel == 'sms' and cart.phone:
                notification = send_recovery_notification(cart, 'sms', cart.phone, message_template)
                notifications_sent.append(notification)
            elif channel == 'whatsapp' and cart.phone:
                notification = send_recovery_notification(cart, 'whatsapp', cart.phone, message_template)
                notifications_sent.append(notification)
        
        # Mettre à jour le compteur de tentatives
        cart.recovery_attempts += 1
        cart.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'message': f'{len(notifications_sent)} notification(s) envoyée(s)',
            'notifications': [notif.to_dict() for notif in notifications_sent]
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@cart_recovery_bp.route('/abandoned-carts/<int:cart_id>/convert', methods=['POST'])
def mark_as_converted(cart_id):
    """
    Marquer un panier comme converti
    """
    try:
        cart = AbandonedCart.query.get_or_404(cart_id)
        data = request.json
        
        cart.status = CartStatus.CONVERTED
        cart.recovered_at = datetime.utcnow()
        cart.conversion_value = data.get('conversion_value', cart.cart_value)
        cart.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify({
            'message': 'Panier marqué comme converti',
            'cart': cart.to_dict()
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@cart_recovery_bp.route('/abandoned-carts/analytics', methods=['GET'])
def get_analytics():
    """
    Obtenir les statistiques de récupération de paniers
    """
    try:
        # Période d'analyse (par défaut 30 derniers jours)
        days = int(request.args.get('days', 30))
        start_date = datetime.utcnow() - timedelta(days=days)
        
        # Statistiques générales
        total_abandoned = AbandonedCart.query.filter(
            AbandonedCart.abandoned_at >= start_date
        ).count()
        
        total_recovered = AbandonedCart.query.filter(
            AbandonedCart.abandoned_at >= start_date,
            AbandonedCart.status == CartStatus.CONVERTED
        ).count()
        
        total_value_abandoned = db.session.query(
            db.func.sum(AbandonedCart.cart_value)
        ).filter(
            AbandonedCart.abandoned_at >= start_date
        ).scalar() or 0
        
        total_value_recovered = db.session.query(
            db.func.sum(AbandonedCart.conversion_value)
        ).filter(
            AbandonedCart.abandoned_at >= start_date,
            AbandonedCart.status == CartStatus.CONVERTED
        ).scalar() or 0
        
        # Taux de récupération
        recovery_rate = (total_recovered / total_abandoned * 100) if total_abandoned > 0 else 0
        
        # Statistiques par canal
        channel_stats = {}
        for channel in ['email', 'sms', 'whatsapp']:
            sent = CartRecoveryNotification.query.filter(
                CartRecoveryNotification.created_at >= start_date,
                CartRecoveryNotification.channel == channel
            ).count()
            
            delivered = CartRecoveryNotification.query.filter(
                CartRecoveryNotification.created_at >= start_date,
                CartRecoveryNotification.channel == channel,
                CartRecoveryNotification.status == NotificationStatus.DELIVERED
            ).count()
            
            clicked = CartRecoveryNotification.query.filter(
                CartRecoveryNotification.created_at >= start_date,
                CartRecoveryNotification.channel == channel,
                CartRecoveryNotification.clicked_at.isnot(None)
            ).count()
            
            channel_stats[channel] = {
                'sent': sent,
                'delivered': delivered,
                'clicked': clicked,
                'delivery_rate': (delivered / sent * 100) if sent > 0 else 0,
                'click_rate': (clicked / delivered * 100) if delivered > 0 else 0
            }
        
        return jsonify({
            'period_days': days,
            'total_abandoned': total_abandoned,
            'total_recovered': total_recovered,
            'recovery_rate': round(recovery_rate, 2),
            'total_value_abandoned': total_value_abandoned,
            'total_value_recovered': total_value_recovered,
            'value_recovery_rate': round((total_value_recovered / total_value_abandoned * 100) if total_value_abandoned > 0 else 0, 2),
            'channel_stats': channel_stats
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def schedule_recovery_notifications(cart_id):
    """
    Programmer les notifications de récupération automatiques
    """
    # Cette fonction serait normalement intégrée avec un système de tâches asynchrones
    # comme Celery. Pour l'instant, on simule la programmation
    pass

def send_recovery_notification(cart, channel, recipient, template='default'):
    """
    Envoyer une notification de récupération
    """
    try:
        # Générer le message basé sur le template
        message_content = generate_recovery_message(cart, template, channel)
        
        # Créer l'enregistrement de notification
        notification = CartRecoveryNotification(
            cart_id=cart.id,
            channel=channel,
            recipient=recipient,
            subject=message_content.get('subject'),
            message=message_content['message'],
            status=NotificationStatus.PENDING
        )
        
        db.session.add(notification)
        db.session.flush()
        
        # Envoyer la notification via le service approprié
        success = notification_service.send_notification(
            channel=channel,
            recipient=recipient,
            subject=message_content.get('subject'),
            message=message_content['message'],
            cart_id=cart.id
        )
        
        if success:
            notification.status = NotificationStatus.SENT
            notification.sent_at = datetime.utcnow()
        else:
            notification.status = NotificationStatus.FAILED
            notification.error_message = "Échec de l'envoi"
        
        db.session.commit()
        return notification
        
    except Exception as e:
        db.session.rollback()
        raise e

def generate_recovery_message(cart, template, channel):
    """
    Générer le contenu du message de récupération
    """
    templates = {
        'default': {
            'email': {
                'subject': 'Vous avez oublié quelque chose dans votre panier !',
                'message': f'''
                Bonjour,
                
                Vous avez laissé {cart.items_count} article(s) dans votre panier d'une valeur de {cart.cart_value} {cart.currency}.
                
                Ne les laissez pas s'échapper ! Finalisez votre commande maintenant.
                
                [Finaliser ma commande]
                
                Cordialement,
                L'équipe RetailBot
                '''
            },
            'sms': {
                'message': f'Votre panier de {cart.cart_value} {cart.currency} vous attend ! Finalisez votre commande: [lien]'
            },
            'whatsapp': {
                'message': f'''🛒 Votre panier vous attend !
                
{cart.items_count} article(s) - {cart.cart_value} {cart.currency}

Finalisez votre commande maintenant: [lien]'''
            }
        }
    }
    
    return templates.get(template, templates['default']).get(channel, templates['default']['email'])

