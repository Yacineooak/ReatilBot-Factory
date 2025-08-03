from flask import Blueprint, jsonify, request
from src.models.conversation import Conversation, Message, Product, UserProfile, db
from src.services.nlp_service import NLPService
from src.services.recommendation_service import RecommendationService
import uuid
from datetime import datetime

chatbot_bp = Blueprint('chatbot', __name__)

# Initialisation des services
nlp_service = NLPService()
recommendation_service = RecommendationService()

@chatbot_bp.route('/chat', methods=['POST'])
def chat():
    """
    Endpoint principal pour traiter les messages du chatbot
    """
    try:
        data = request.json
        
        # Validation des données d'entrée
        if not data or 'message' not in data:
            return jsonify({'error': 'Message requis'}), 400
        
        user_message = data['message']
        session_id = data.get('session_id', str(uuid.uuid4()))
        user_id = data.get('user_id')
        platform = data.get('platform', 'website')
        language = data.get('language', 'fr')
        
        # Récupérer ou créer la conversation
        conversation = Conversation.query.filter_by(session_id=session_id).first()
        if not conversation:
            conversation = Conversation(
                session_id=session_id,
                user_id=user_id,
                platform=platform,
                language=language
            )
            db.session.add(conversation)
            db.session.commit()
        
        # Sauvegarder le message utilisateur
        user_msg = Message(
            conversation_id=conversation.id,
            sender_type='user',
            content=user_message
        )
        db.session.add(user_msg)
        
        # Traitement NLP du message
        nlp_result = nlp_service.process_message(user_message, language)
        
        # Mettre à jour le message avec les résultats NLP
        user_msg.intent = nlp_result.get('intent')
        user_msg.entities = nlp_result.get('entities')
        user_msg.confidence = nlp_result.get('confidence')
        
        # Générer la réponse du bot
        bot_response = generate_bot_response(nlp_result, conversation, language)
        
        # Sauvegarder la réponse du bot
        bot_msg = Message(
            conversation_id=conversation.id,
            sender_type='bot',
            content=bot_response['message']
        )
        db.session.add(bot_msg)
        
        # Mettre à jour le timestamp de la conversation
        conversation.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'session_id': session_id,
            'response': bot_response['message'],
            'intent': nlp_result.get('intent'),
            'confidence': nlp_result.get('confidence'),
            'suggestions': bot_response.get('suggestions', []),
            'products': bot_response.get('products', [])
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@chatbot_bp.route('/conversations/<session_id>', methods=['GET'])
def get_conversation(session_id):
    """
    Récupérer l'historique d'une conversation
    """
    conversation = Conversation.query.filter_by(session_id=session_id).first()
    if not conversation:
        return jsonify({'error': 'Conversation non trouvée'}), 404
    
    return jsonify(conversation.to_dict())

@chatbot_bp.route('/conversations/<session_id>/close', methods=['POST'])
def close_conversation(session_id):
    """
    Fermer une conversation
    """
    conversation = Conversation.query.filter_by(session_id=session_id).first()
    if not conversation:
        return jsonify({'error': 'Conversation non trouvée'}), 404
    
    conversation.status = 'closed'
    conversation.updated_at = datetime.utcnow()
    db.session.commit()
    
    return jsonify({'message': 'Conversation fermée avec succès'})

@chatbot_bp.route('/products/search', methods=['GET'])
def search_products():
    """
    Rechercher des produits
    """
    query = request.args.get('q', '')
    category = request.args.get('category')
    limit = int(request.args.get('limit', 10))
    
    products_query = Product.query.filter(Product.is_active == True)
    
    if query:
        products_query = products_query.filter(
            Product.name.contains(query) | 
            Product.description.contains(query)
        )
    
    if category:
        products_query = products_query.filter(Product.category == category)
    
    products = products_query.limit(limit).all()
    
    return jsonify([product.to_dict() for product in products])

@chatbot_bp.route('/products/recommendations', methods=['POST'])
def get_recommendations():
    """
    Obtenir des recommandations de produits
    """
    data = request.json
    user_id = data.get('user_id')
    product_ids = data.get('product_ids', [])
    limit = data.get('limit', 5)
    
    recommendations = recommendation_service.get_recommendations(
        user_id=user_id,
        product_ids=product_ids,
        limit=limit
    )
    
    return jsonify(recommendations)

def generate_bot_response(nlp_result, conversation, language):
    """
    Générer la réponse du bot basée sur l'intent détecté
    """
    intent = nlp_result.get('intent', 'unknown')
    entities = nlp_result.get('entities', {})
    
    # Réponses par défaut selon la langue
    responses = {
        'fr': {
            'greeting': "Bonjour ! Je suis votre assistant shopping. Comment puis-je vous aider aujourd'hui ?",
            'product_search': "Je vais vous aider à trouver des produits. Que recherchez-vous ?",
            'order_status': "Pour vérifier le statut de votre commande, pouvez-vous me donner votre numéro de commande ?",
            'unknown': "Je ne suis pas sûr de comprendre. Pouvez-vous reformuler votre question ?",
            'goodbye': "Merci de votre visite ! N'hésitez pas à revenir si vous avez d'autres questions."
        },
        'ar': {
            'greeting': "مرحبا! أنا مساعدك للتسوق. كيف يمكنني مساعدتك اليوم؟",
            'product_search': "سأساعدك في العثور على المنتجات. ماذا تبحث عنه؟",
            'order_status': "للتحقق من حالة طلبك، هل يمكنك إعطائي رقم الطلب؟",
            'unknown': "لست متأكدا من فهمي. هل يمكنك إعادة صياغة سؤالك؟",
            'goodbye': "شكرا لزيارتك! لا تتردد في العودة إذا كان لديك أسئلة أخرى."
        },
        'en': {
            'greeting': "Hello! I'm your shopping assistant. How can I help you today?",
            'product_search': "I'll help you find products. What are you looking for?",
            'order_status': "To check your order status, can you give me your order number?",
            'unknown': "I'm not sure I understand. Can you rephrase your question?",
            'goodbye': "Thank you for your visit! Feel free to come back if you have other questions."
        }
    }
    
    lang_responses = responses.get(language, responses['fr'])
    
    response = {
        'message': lang_responses.get(intent, lang_responses['unknown']),
        'suggestions': [],
        'products': []
    }
    
    # Logique spécifique selon l'intent
    if intent == 'product_search':
        # Rechercher des produits basés sur les entités
        product_name = entities.get('product_name')
        category = entities.get('category')
        
        if product_name or category:
            products_query = Product.query.filter(Product.is_active == True)
            
            if product_name:
                products_query = products_query.filter(
                    Product.name.contains(product_name)
                )
            
            if category:
                products_query = products_query.filter(Product.category == category)
            
            products = products_query.limit(5).all()
            response['products'] = [product.to_dict() for product in products]
            
            if products:
                if language == 'fr':
                    response['message'] = f"J'ai trouvé {len(products)} produit(s) pour vous :"
                elif language == 'ar':
                    response['message'] = f"وجدت {len(products)} منتج(ات) لك:"
                else:
                    response['message'] = f"I found {len(products)} product(s) for you:"
    
    elif intent == 'greeting':
        # Ajouter des suggestions pour commencer
        if language == 'fr':
            response['suggestions'] = [
                "Rechercher des produits",
                "Voir les offres du jour",
                "Statut de ma commande"
            ]
        elif language == 'ar':
            response['suggestions'] = [
                "البحث عن المنتجات",
                "عروض اليوم",
                "حالة طلبي"
            ]
        else:
            response['suggestions'] = [
                "Search products",
                "Today's offers",
                "My order status"
            ]
    
    return response

