import random
from typing import List, Dict, Any, Optional
from src.models.conversation import Product, UserProfile, Message, Conversation, db
from sqlalchemy import func, and_

class RecommendationService:
    """
    Service de recommandation de produits basé sur l'IA
    """
    
    def __init__(self):
        self.recommendation_strategies = [
            'collaborative_filtering',
            'content_based',
            'popularity_based',
            'category_based'
        ]
    
    def get_recommendations(self, user_id: Optional[str] = None, 
                          product_ids: List[int] = None, 
                          category: Optional[str] = None,
                          limit: int = 5) -> List[Dict[str, Any]]:
        """
        Obtenir des recommandations de produits
        """
        recommendations = []
        
        # Stratégie 1: Recommandations basées sur l'utilisateur
        if user_id:
            user_recommendations = self._get_user_based_recommendations(user_id, limit)
            recommendations.extend(user_recommendations)
        
        # Stratégie 2: Recommandations basées sur les produits consultés
        if product_ids:
            product_recommendations = self._get_product_based_recommendations(product_ids, limit)
            recommendations.extend(product_recommendations)
        
        # Stratégie 3: Recommandations par catégorie
        if category:
            category_recommendations = self._get_category_recommendations(category, limit)
            recommendations.extend(category_recommendations)
        
        # Stratégie 4: Produits populaires (fallback)
        if not recommendations:
            popular_recommendations = self._get_popular_products(limit)
            recommendations.extend(popular_recommendations)
        
        # Supprimer les doublons et limiter
        seen_ids = set()
        unique_recommendations = []
        
        for rec in recommendations:
            if rec['id'] not in seen_ids:
                seen_ids.add(rec['id'])
                unique_recommendations.append(rec)
                
                if len(unique_recommendations) >= limit:
                    break
        
        return unique_recommendations
    
    def _get_user_based_recommendations(self, user_id: str, limit: int) -> List[Dict[str, Any]]:
        """
        Recommandations basées sur l'historique de l'utilisateur
        """
        try:
            # Récupérer le profil utilisateur
            user_profile = UserProfile.query.filter_by(user_id=user_id).first()
            
            if not user_profile:
                return []
            
            # Récupérer les conversations de l'utilisateur
            conversations = Conversation.query.filter_by(user_id=user_id).all()
            
            if not conversations:
                return []
            
            # Analyser les intérêts de l'utilisateur à partir des conversations
            interests = self._analyze_user_interests(conversations)
            
            # Recommander des produits basés sur les intérêts
            recommendations = []
            
            for interest in interests:
                products = Product.query.filter(
                    and_(
                        Product.is_active == True,
                        Product.category.contains(interest) | Product.name.contains(interest)
                    )
                ).limit(2).all()
                
                recommendations.extend([self._product_to_recommendation(p) for p in products])
            
            return recommendations[:limit]
            
        except Exception as e:
            print(f"Erreur dans les recommandations utilisateur: {e}")
            return []
    
    def _get_product_based_recommendations(self, product_ids: List[int], limit: int) -> List[Dict[str, Any]]:
        """
        Recommandations basées sur des produits similaires
        """
        try:
            # Récupérer les produits de référence
            reference_products = Product.query.filter(Product.id.in_(product_ids)).all()
            
            if not reference_products:
                return []
            
            recommendations = []
            
            for product in reference_products:
                # Trouver des produits similaires (même catégorie, marque similaire)
                similar_products = Product.query.filter(
                    and_(
                        Product.is_active == True,
                        Product.id != product.id,
                        Product.category == product.category
                    )
                ).limit(3).all()
                
                recommendations.extend([self._product_to_recommendation(p) for p in similar_products])
                
                # Ajouter des produits de la même marque
                if product.brand:
                    brand_products = Product.query.filter(
                        and_(
                            Product.is_active == True,
                            Product.id != product.id,
                            Product.brand == product.brand
                        )
                    ).limit(2).all()
                    
                    recommendations.extend([self._product_to_recommendation(p) for p in brand_products])
            
            return recommendations[:limit]
            
        except Exception as e:
            print(f"Erreur dans les recommandations produit: {e}")
            return []
    
    def _get_category_recommendations(self, category: str, limit: int) -> List[Dict[str, Any]]:
        """
        Recommandations par catégorie
        """
        try:
            products = Product.query.filter(
                and_(
                    Product.is_active == True,
                    Product.category == category
                )
            ).order_by(func.random()).limit(limit).all()
            
            return [self._product_to_recommendation(p) for p in products]
            
        except Exception as e:
            print(f"Erreur dans les recommandations par catégorie: {e}")
            return []
    
    def _get_popular_products(self, limit: int) -> List[Dict[str, Any]]:
        """
        Recommandations basées sur la popularité
        """
        try:
            # Pour l'instant, on simule la popularité avec un ordre aléatoire
            # Dans une vraie implémentation, on utiliserait des métriques de vente
            products = Product.query.filter(Product.is_active == True)\
                                  .order_by(func.random())\
                                  .limit(limit).all()
            
            return [self._product_to_recommendation(p) for p in products]
            
        except Exception as e:
            print(f"Erreur dans les recommandations populaires: {e}")
            return []
    
    def _analyze_user_interests(self, conversations: List[Conversation]) -> List[str]:
        """
        Analyser les intérêts de l'utilisateur à partir de ses conversations
        """
        interests = []
        
        for conversation in conversations:
            for message in conversation.messages:
                if message.sender_type == 'user' and message.entities:
                    # Extraire les catégories et noms de produits mentionnés
                    if 'category' in message.entities:
                        interests.append(message.entities['category'])
                    
                    if 'product_name' in message.entities:
                        interests.append(message.entities['product_name'])
        
        # Retourner les intérêts uniques
        return list(set(interests))
    
    def _product_to_recommendation(self, product: Product) -> Dict[str, Any]:
        """
        Convertir un produit en format de recommandation
        """
        return {
            'id': product.id,
            'name': product.name,
            'description': product.description,
            'price': product.price,
            'currency': product.currency,
            'category': product.category,
            'brand': product.brand,
            'image_url': product.image_url,
            'recommendation_score': random.uniform(0.7, 1.0),  # Score simulé
            'recommendation_reason': self._get_recommendation_reason(product)
        }
    
    def _get_recommendation_reason(self, product: Product) -> str:
        """
        Générer une raison pour la recommandation
        """
        reasons = [
            "Produit populaire dans cette catégorie",
            "Basé sur vos recherches récentes",
            "Clients ayant acheté des produits similaires",
            "Nouvelle arrivée recommandée",
            "Excellent rapport qualité-prix"
        ]
        
        return random.choice(reasons)
    
    def get_trending_products(self, category: Optional[str] = None, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Obtenir les produits tendance
        """
        try:
            query = Product.query.filter(Product.is_active == True)
            
            if category:
                query = query.filter(Product.category == category)
            
            # Simuler les tendances avec un ordre aléatoire
            # Dans une vraie implémentation, on utiliserait des métriques de vente récentes
            products = query.order_by(func.random()).limit(limit).all()
            
            return [self._product_to_recommendation(p) for p in products]
            
        except Exception as e:
            print(f"Erreur dans les produits tendance: {e}")
            return []
    
    def get_cross_sell_recommendations(self, product_id: int, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Recommandations de vente croisée pour un produit donné
        """
        try:
            product = Product.query.get(product_id)
            
            if not product:
                return []
            
            # Logique de vente croisée basée sur la catégorie et le prix
            cross_sell_products = Product.query.filter(
                and_(
                    Product.is_active == True,
                    Product.id != product_id,
                    Product.category == product.category,
                    Product.price <= product.price * 1.5,  # Prix similaire ou légèrement supérieur
                    Product.price >= product.price * 0.5
                )
            ).limit(limit).all()
            
            return [self._product_to_recommendation(p) for p in cross_sell_products]
            
        except Exception as e:
            print(f"Erreur dans les recommandations de vente croisée: {e}")
            return []

