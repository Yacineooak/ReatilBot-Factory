from flask import Blueprint, jsonify, request
from src.integrations.shopify_integration import ShopifyIntegration
from src.integrations.whatsapp_integration import WhatsAppIntegration
from datetime import datetime
import json

integrations_bp = Blueprint('integrations', __name__)

@integrations_bp.route('/integrations/shopify/test', methods=['POST'])
def test_shopify_connection():
    """
    Tester la connexion Shopify
    """
    try:
        data = request.get_json()
        shop_domain = data.get('shop_domain')
        access_token = data.get('access_token')
        
        if not shop_domain or not access_token:
            return jsonify({'error': 'Domaine et token requis'}), 400
        
        shopify = ShopifyIntegration(shop_domain, access_token)
        result = shopify.test_connection()
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@integrations_bp.route('/integrations/shopify/products', methods=['POST'])
def get_shopify_products():
    """
    Récupérer les produits Shopify
    """
    try:
        data = request.get_json()
        shop_domain = data.get('shop_domain')
        access_token = data.get('access_token')
        limit = data.get('limit', 50)
        
        shopify = ShopifyIntegration(shop_domain, access_token)
        products = shopify.get_products(limit)
        
        return jsonify({
            'success': True,
            'products': products,
            'count': len(products)
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@integrations_bp.route('/integrations/shopify/search', methods=['POST'])
def search_shopify_products():
    """
    Rechercher des produits Shopify
    """
    try:
        data = request.get_json()
        shop_domain = data.get('shop_domain')
        access_token = data.get('access_token')
        query = data.get('query', '')
        
        shopify = ShopifyIntegration(shop_domain, access_token)
        products = shopify.search_products(query)
        
        return jsonify({
            'success': True,
            'products': products,
            'query': query,
            'count': len(products)
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@integrations_bp.route('/integrations/shopify/order/<order_id>', methods=['POST'])
def get_shopify_order(order_id):
    """
    Récupérer une commande Shopify
    """
    try:
        data = request.get_json()
        shop_domain = data.get('shop_domain')
        access_token = data.get('access_token')
        
        shopify = ShopifyIntegration(shop_domain, access_token)
        order = shopify.get_order(order_id)
        
        if order:
            return jsonify({
                'success': True,
                'order': order
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Commande non trouvée'
            }), 404
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@integrations_bp.route('/integrations/shopify/abandoned-carts', methods=['POST'])
def get_shopify_abandoned_carts():
    """
    Récupérer les paniers abandonnés Shopify
    """
    try:
        data = request.get_json()
        shop_domain = data.get('shop_domain')
        access_token = data.get('access_token')
        
        shopify = ShopifyIntegration(shop_domain, access_token)
        checkouts = shopify.get_abandoned_checkouts()
        
        return jsonify({
            'success': True,
            'abandoned_carts': checkouts,
            'count': len(checkouts)
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@integrations_bp.route('/integrations/whatsapp/test', methods=['POST'])
def test_whatsapp_connection():
    """
    Tester la connexion WhatsApp Business
    """
    try:
        data = request.get_json()
        phone_number_id = data.get('phone_number_id')
        access_token = data.get('access_token')
        
        if not phone_number_id or not access_token:
            return jsonify({'error': 'Phone number ID et token requis'}), 400
        
        whatsapp = WhatsAppIntegration(phone_number_id, access_token)
        result = whatsapp.test_connection()
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@integrations_bp.route('/integrations/whatsapp/send-message', methods=['POST'])
def send_whatsapp_message():
    """
    Envoyer un message WhatsApp
    """
    try:
        data = request.get_json()
        phone_number_id = data.get('phone_number_id')
        access_token = data.get('access_token')
        to = data.get('to')
        message = data.get('message')
        message_type = data.get('type', 'text')
        
        if not all([phone_number_id, access_token, to, message]):
            return jsonify({'error': 'Paramètres manquants'}), 400
        
        whatsapp = WhatsAppIntegration(phone_number_id, access_token)
        
        if message_type == 'text':
            result = whatsapp.send_text_message(to, message)
        elif message_type == 'template':
            template_name = data.get('template_name')
            language = data.get('language', 'fr')
            parameters = data.get('parameters', [])
            result = whatsapp.send_template_message(to, template_name, language, parameters)
        else:
            return jsonify({'error': 'Type de message non supporté'}), 400
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@integrations_bp.route('/integrations/whatsapp/send-interactive', methods=['POST'])
def send_whatsapp_interactive():
    """
    Envoyer un message interactif WhatsApp
    """
    try:
        data = request.get_json()
        phone_number_id = data.get('phone_number_id')
        access_token = data.get('access_token')
        to = data.get('to')
        header = data.get('header')
        body = data.get('body')
        buttons = data.get('buttons', [])
        
        if not all([phone_number_id, access_token, to, header, body]):
            return jsonify({'error': 'Paramètres manquants'}), 400
        
        whatsapp = WhatsAppIntegration(phone_number_id, access_token)
        result = whatsapp.send_interactive_message(to, header, body, buttons)
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@integrations_bp.route('/integrations/whatsapp/webhook', methods=['GET', 'POST'])
def whatsapp_webhook():
    """
    Webhook pour recevoir les messages WhatsApp
    """
    if request.method == 'GET':
        # Vérification du webhook
        verify_token = request.args.get('hub.verify_token')
        challenge = request.args.get('hub.challenge')
        
        # En production, vérifier le token
        if verify_token == 'your_verify_token':
            return challenge
        else:
            return 'Token invalide', 403
    
    elif request.method == 'POST':
        # Traitement des messages entrants
        try:
            webhook_data = request.get_json()
            
            # Traiter le webhook (simulation)
            result = {
                'success': True,
                'timestamp': datetime.utcnow().isoformat(),
                'processed': True
            }
            
            # En production, traiter les messages avec WhatsAppIntegration
            # whatsapp = WhatsAppIntegration(phone_number_id, access_token)
            # result = whatsapp.process_webhook(webhook_data)
            
            return jsonify(result)
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500

@integrations_bp.route('/integrations/available', methods=['GET'])
def get_available_integrations():
    """
    Lister les intégrations disponibles
    """
    integrations = [
        {
            'id': 'shopify',
            'name': 'Shopify',
            'description': 'Intégration avec votre boutique Shopify',
            'features': [
                'Récupération des produits',
                'Recherche de produits',
                'Gestion des commandes',
                'Paniers abandonnés',
                'Gestion de l\'inventaire'
            ],
            'required_fields': [
                {'name': 'shop_domain', 'label': 'Domaine de la boutique', 'type': 'text'},
                {'name': 'access_token', 'label': 'Token d\'accès', 'type': 'password'}
            ]
        },
        {
            'id': 'woocommerce',
            'name': 'WooCommerce',
            'description': 'Intégration avec WooCommerce',
            'features': [
                'Récupération des produits',
                'Gestion des commandes',
                'Synchronisation de l\'inventaire'
            ],
            'required_fields': [
                {'name': 'site_url', 'label': 'URL du site', 'type': 'url'},
                {'name': 'consumer_key', 'label': 'Clé consommateur', 'type': 'text'},
                {'name': 'consumer_secret', 'label': 'Secret consommateur', 'type': 'password'}
            ]
        },
        {
            'id': 'whatsapp',
            'name': 'WhatsApp Business',
            'description': 'Bot WhatsApp Business',
            'features': [
                'Messages texte',
                'Messages template',
                'Messages interactifs',
                'Médias',
                'Webhook'
            ],
            'required_fields': [
                {'name': 'phone_number_id', 'label': 'ID du numéro de téléphone', 'type': 'text'},
                {'name': 'access_token', 'label': 'Token d\'accès', 'type': 'password'}
            ]
        },
        {
            'id': 'messenger',
            'name': 'Facebook Messenger',
            'description': 'Bot Facebook Messenger',
            'features': [
                'Messages texte',
                'Messages template',
                'Quick replies',
                'Boutons',
                'Webhook'
            ],
            'required_fields': [
                {'name': 'page_id', 'label': 'ID de la page', 'type': 'text'},
                {'name': 'access_token', 'label': 'Token d\'accès', 'type': 'password'}
            ]
        }
    ]
    
    return jsonify({
        'success': True,
        'integrations': integrations,
        'count': len(integrations)
    })

@integrations_bp.route('/integrations/test-all', methods=['POST'])
def test_all_integrations():
    """
    Tester toutes les intégrations configurées
    """
    try:
        data = request.get_json()
        integrations_config = data.get('integrations', {})
        
        results = {}
        
        # Test Shopify
        if integrations_config.get('shopify', {}).get('enabled'):
            shopify_config = integrations_config['shopify']
            shopify = ShopifyIntegration(
                shopify_config.get('shop_domain'),
                shopify_config.get('access_token')
            )
            results['shopify'] = shopify.test_connection()
        
        # Test WhatsApp
        if integrations_config.get('whatsapp', {}).get('enabled'):
            whatsapp_config = integrations_config['whatsapp']
            whatsapp = WhatsAppIntegration(
                whatsapp_config.get('phone_number_id'),
                whatsapp_config.get('access_token')
            )
            results['whatsapp'] = whatsapp.test_connection()
        
        # Autres intégrations (simulation)
        if integrations_config.get('woocommerce', {}).get('enabled'):
            results['woocommerce'] = {
                'success': True,
                'status': 'connected (simulation)',
                'message': 'WooCommerce intégration simulée'
            }
        
        if integrations_config.get('messenger', {}).get('enabled'):
            results['messenger'] = {
                'success': True,
                'status': 'connected (simulation)',
                'message': 'Messenger intégration simulée'
            }
        
        return jsonify({
            'success': True,
            'results': results,
            'tested_count': len(results)
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

