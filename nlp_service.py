import re
import json
from typing import Dict, List, Any
import openai
import os

class NLPService:
    """
    Service de traitement du langage naturel pour le chatbot
    """
    
    def __init__(self):
        # Configuration OpenAI
        openai.api_key = os.getenv('OPENAI_API_KEY')
        openai.api_base = os.getenv('OPENAI_API_BASE')
        
        # Définition des intents et leurs mots-clés
        self.intent_patterns = {
            'greeting': {
                'fr': ['bonjour', 'salut', 'hello', 'bonsoir', 'bonne journée'],
                'ar': ['مرحبا', 'أهلا', 'السلام عليكم', 'صباح الخير', 'مساء الخير'],
                'en': ['hello', 'hi', 'good morning', 'good evening', 'hey']
            },
            'goodbye': {
                'fr': ['au revoir', 'à bientôt', 'bye', 'merci', 'bonne journée'],
                'ar': ['وداعا', 'إلى اللقاء', 'شكرا', 'مع السلامة'],
                'en': ['goodbye', 'bye', 'see you', 'thanks', 'have a good day']
            },
            'product_search': {
                'fr': ['chercher', 'rechercher', 'trouver', 'produit', 'article', 'acheter'],
                'ar': ['بحث', 'العثور', 'منتج', 'شراء', 'أريد'],
                'en': ['search', 'find', 'product', 'buy', 'looking for', 'want']
            },
            'order_status': {
                'fr': ['commande', 'statut', 'suivi', 'livraison', 'où est'],
                'ar': ['طلب', 'حالة', 'تتبع', 'توصيل', 'أين'],
                'en': ['order', 'status', 'tracking', 'delivery', 'where is']
            },
            'price_inquiry': {
                'fr': ['prix', 'coût', 'combien', 'tarif'],
                'ar': ['سعر', 'كلفة', 'كم', 'ثمن'],
                'en': ['price', 'cost', 'how much', 'rate']
            },
            'help': {
                'fr': ['aide', 'aider', 'assistance', 'support'],
                'ar': ['مساعدة', 'دعم', 'مساندة'],
                'en': ['help', 'assist', 'support']
            }
        }
        
        # Patterns pour extraire les entités
        self.entity_patterns = {
            'product_name': r'(?:chercher|rechercher|trouver|acheter|بحث|العثور|شراء|search|find|buy)\s+(?:un|une|le|la|des|les)?\s*([a-zA-Zàâäéèêëïîôöùûüÿç\u0600-\u06FF\s]+)',
            'price_range': r'(?:entre|من|between)\s*(\d+)\s*(?:et|إلى|and)\s*(\d+)',
            'category': r'(?:catégorie|فئة|category)\s*:?\s*([a-zA-Zàâäéèêëïîôöùûüÿç\u0600-\u06FF\s]+)'
        }
    
    def process_message(self, message: str, language: str = 'fr') -> Dict[str, Any]:
        """
        Traiter un message utilisateur et extraire l'intent et les entités
        """
        message_lower = message.lower()
        
        # Détection de l'intent
        intent = self._detect_intent(message_lower, language)
        
        # Extraction des entités
        entities = self._extract_entities(message, language)
        
        # Calcul du score de confiance
        confidence = self._calculate_confidence(message_lower, intent, language)
        
        # Si la confiance est faible, utiliser OpenAI pour une analyse plus poussée
        if confidence < 0.6:
            try:
                enhanced_result = self._enhance_with_openai(message, language)
                if enhanced_result:
                    intent = enhanced_result.get('intent', intent)
                    entities.update(enhanced_result.get('entities', {}))
                    confidence = max(confidence, enhanced_result.get('confidence', 0.6))
            except Exception as e:
                print(f"Erreur OpenAI: {e}")
        
        return {
            'intent': intent,
            'entities': entities,
            'confidence': confidence,
            'original_message': message
        }
    
    def _detect_intent(self, message: str, language: str) -> str:
        """
        Détecter l'intent principal du message
        """
        best_intent = 'unknown'
        best_score = 0
        
        for intent, patterns in self.intent_patterns.items():
            lang_patterns = patterns.get(language, patterns.get('fr', []))
            score = 0
            
            for pattern in lang_patterns:
                if pattern in message:
                    score += 1
            
            # Normaliser le score
            if lang_patterns:
                score = score / len(lang_patterns)
            
            if score > best_score:
                best_score = score
                best_intent = intent
        
        return best_intent if best_score > 0 else 'unknown'
    
    def _extract_entities(self, message: str, language: str) -> Dict[str, Any]:
        """
        Extraire les entités du message
        """
        entities = {}
        
        # Extraction du nom de produit
        product_match = re.search(self.entity_patterns['product_name'], message, re.IGNORECASE)
        if product_match:
            entities['product_name'] = product_match.group(1).strip()
        
        # Extraction de la fourchette de prix
        price_match = re.search(self.entity_patterns['price_range'], message, re.IGNORECASE)
        if price_match:
            entities['price_min'] = int(price_match.group(1))
            entities['price_max'] = int(price_match.group(2))
        
        # Extraction de la catégorie
        category_match = re.search(self.entity_patterns['category'], message, re.IGNORECASE)
        if category_match:
            entities['category'] = category_match.group(1).strip()
        
        # Extraction des nombres
        numbers = re.findall(r'\d+', message)
        if numbers:
            entities['numbers'] = [int(n) for n in numbers]
        
        return entities
    
    def _calculate_confidence(self, message: str, intent: str, language: str) -> float:
        """
        Calculer le score de confiance pour l'intent détecté
        """
        if intent == 'unknown':
            return 0.0
        
        patterns = self.intent_patterns.get(intent, {}).get(language, [])
        if not patterns:
            return 0.3
        
        matches = sum(1 for pattern in patterns if pattern in message)
        confidence = min(matches / len(patterns) * 2, 1.0)  # Max 1.0
        
        # Bonus pour les messages plus longs et structurés
        if len(message.split()) > 3:
            confidence += 0.1
        
        return min(confidence, 1.0)
    
    def _enhance_with_openai(self, message: str, language: str) -> Dict[str, Any]:
        """
        Utiliser OpenAI pour une analyse NLP plus avancée
        """
        try:
            prompt = f"""
            Analysez ce message client dans un contexte de commerce électronique.
            Message: "{message}"
            Langue: {language}
            
            Retournez un JSON avec:
            - intent: l'intention principale (greeting, product_search, order_status, price_inquiry, help, goodbye, unknown)
            - entities: les entités extraites (product_name, category, price_min, price_max, etc.)
            - confidence: score de confiance (0.0 à 1.0)
            
            Réponse JSON uniquement:
            """
            
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=200,
                temperature=0.1
            )
            
            result = response.choices[0].message.content.strip()
            return json.loads(result)
            
        except Exception as e:
            print(f"Erreur lors de l'analyse OpenAI: {e}")
            return None
    
    def get_intent_suggestions(self, language: str = 'fr') -> List[str]:
        """
        Obtenir des suggestions d'intents pour l'interface utilisateur
        """
        suggestions = {
            'fr': [
                "Rechercher un produit",
                "Vérifier ma commande",
                "Voir les prix",
                "Obtenir de l'aide"
            ],
            'ar': [
                "البحث عن منتج",
                "التحقق من طلبي",
                "عرض الأسعار",
                "الحصول على المساعدة"
            ],
            'en': [
                "Search for a product",
                "Check my order",
                "View prices",
                "Get help"
            ]
        }
        
        return suggestions.get(language, suggestions['fr'])

