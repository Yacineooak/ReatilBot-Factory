from flask import Blueprint, jsonify, request
from src.models.base import db
from datetime import datetime
import json
import os

deployment_bp = Blueprint('deployment', __name__)

@deployment_bp.route('/deploy', methods=['POST'])
def deploy_bot():
    """
    Déployer un bot avec la configuration fournie
    """
    try:
        config = request.get_json()
        
        if not config:
            return jsonify({'error': 'Configuration manquante'}), 400
        
        # Valider la configuration
        required_fields = ['name', 'description', 'language', 'platform']
        for field in required_fields:
            if field not in config:
                return jsonify({'error': f'Champ requis manquant: {field}'}), 400
        
        # Créer un ID de déploiement unique
        deployment_id = f"deploy_{int(datetime.utcnow().timestamp())}"
        
        # Sauvegarder la configuration de déploiement
        deployment_config = {
            'id': deployment_id,
            'config': config,
            'status': 'deployed',
            'deployed_at': datetime.utcnow().isoformat(),
            'endpoints': {
                'chat': f'/api/chat/{deployment_id}',
                'webhook': f'/api/webhook/{deployment_id}',
                'status': f'/api/status/{deployment_id}'
            }
        }
        
        # Sauvegarder dans un fichier (en production, utiliser une base de données)
        deployments_dir = os.path.join(os.path.dirname(__file__), '..', 'deployments')
        os.makedirs(deployments_dir, exist_ok=True)
        
        deployment_file = os.path.join(deployments_dir, f'{deployment_id}.json')
        with open(deployment_file, 'w', encoding='utf-8') as f:
            json.dump(deployment_config, f, ensure_ascii=False, indent=2)
        
        return jsonify({
            'success': True,
            'deployment_id': deployment_id,
            'message': 'Bot déployé avec succès',
            'endpoints': deployment_config['endpoints'],
            'config': {
                'name': config['name'],
                'platform': config['platform'],
                'language': config['language']
            }
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@deployment_bp.route('/deployments', methods=['GET'])
def list_deployments():
    """
    Lister tous les déploiements
    """
    try:
        deployments_dir = os.path.join(os.path.dirname(__file__), '..', 'deployments')
        
        if not os.path.exists(deployments_dir):
            return jsonify({'deployments': []})
        
        deployments = []
        for filename in os.listdir(deployments_dir):
            if filename.endswith('.json'):
                filepath = os.path.join(deployments_dir, filename)
                with open(filepath, 'r', encoding='utf-8') as f:
                    deployment = json.load(f)
                    deployments.append({
                        'id': deployment['id'],
                        'name': deployment['config']['name'],
                        'platform': deployment['config']['platform'],
                        'status': deployment['status'],
                        'deployed_at': deployment['deployed_at']
                    })
        
        # Trier par date de déploiement (plus récent en premier)
        deployments.sort(key=lambda x: x['deployed_at'], reverse=True)
        
        return jsonify({'deployments': deployments})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@deployment_bp.route('/deployments/<deployment_id>', methods=['GET'])
def get_deployment(deployment_id):
    """
    Obtenir les détails d'un déploiement spécifique
    """
    try:
        deployments_dir = os.path.join(os.path.dirname(__file__), '..', 'deployments')
        deployment_file = os.path.join(deployments_dir, f'{deployment_id}.json')
        
        if not os.path.exists(deployment_file):
            return jsonify({'error': 'Déploiement non trouvé'}), 404
        
        with open(deployment_file, 'r', encoding='utf-8') as f:
            deployment = json.load(f)
        
        return jsonify(deployment)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@deployment_bp.route('/deployments/<deployment_id>', methods=['DELETE'])
def delete_deployment(deployment_id):
    """
    Supprimer un déploiement
    """
    try:
        deployments_dir = os.path.join(os.path.dirname(__file__), '..', 'deployments')
        deployment_file = os.path.join(deployments_dir, f'{deployment_id}.json')
        
        if not os.path.exists(deployment_file):
            return jsonify({'error': 'Déploiement non trouvé'}), 404
        
        os.remove(deployment_file)
        
        return jsonify({
            'success': True,
            'message': 'Déploiement supprimé avec succès'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@deployment_bp.route('/chat/<deployment_id>', methods=['POST'])
def chat_endpoint(deployment_id):
    """
    Endpoint de chat pour un bot déployé
    """
    try:
        # Charger la configuration du déploiement
        deployments_dir = os.path.join(os.path.dirname(__file__), '..', 'deployments')
        deployment_file = os.path.join(deployments_dir, f'{deployment_id}.json')
        
        if not os.path.exists(deployment_file):
            return jsonify({'error': 'Bot non trouvé'}), 404
        
        with open(deployment_file, 'r', encoding='utf-8') as f:
            deployment = json.load(f)
        
        config = deployment['config']
        data = request.get_json()
        
        if not data or 'message' not in data:
            return jsonify({'error': 'Message manquant'}), 400
        
        user_message = data['message']
        
        # Simuler une réponse du bot basée sur la configuration
        if user_message.lower() in ['bonjour', 'salut', 'hello', 'hi']:
            bot_response = config['behavior']['greeting']
        elif 'produit' in user_message.lower() or 'product' in user_message.lower():
            bot_response = "Je peux vous aider à trouver des produits. Que recherchez-vous exactement ?"
        elif 'commande' in user_message.lower() or 'order' in user_message.lower():
            bot_response = "Pour vérifier votre commande, pouvez-vous me donner votre numéro de commande ?"
        elif 'prix' in user_message.lower() or 'price' in user_message.lower():
            bot_response = "Je peux vous renseigner sur les prix. De quel produit s'agit-il ?"
        else:
            bot_response = config['behavior']['fallback']
        
        return jsonify({
            'response': bot_response,
            'bot_name': config['name'],
            'timestamp': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@deployment_bp.route('/status/<deployment_id>', methods=['GET'])
def bot_status(deployment_id):
    """
    Vérifier le statut d'un bot déployé
    """
    try:
        deployments_dir = os.path.join(os.path.dirname(__file__), '..', 'deployments')
        deployment_file = os.path.join(deployments_dir, f'{deployment_id}.json')
        
        if not os.path.exists(deployment_file):
            return jsonify({'error': 'Bot non trouvé'}), 404
        
        with open(deployment_file, 'r', encoding='utf-8') as f:
            deployment = json.load(f)
        
        return jsonify({
            'status': 'online',
            'deployment_id': deployment_id,
            'name': deployment['config']['name'],
            'platform': deployment['config']['platform'],
            'deployed_at': deployment['deployed_at'],
            'uptime': 'Active'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

