import re
from typing import Dict, Any, List
from datetime import datetime, timedelta
from src.models.management import CODOrder, CODRiskLevel, db
import json

class FraudDetectionService:
    """
    Service de détection de fraude pour les commandes COD
    """
    
    def __init__(self):
        # Règles de base pour la détection de fraude
        self.risk_rules = {
            'high_value_threshold': 50000,  # DZD
            'suspicious_cities': ['Unknown', 'Test', ''],
            'phone_patterns': {
                'invalid': [r'^0{10}', r'^1{10}', r'^(\d)\1{9}'],  # Numéros suspects
                'valid': [r'^(05|06|07)\d{8}$']  # Format algérien valide
            },
            'name_patterns': {
                'suspicious': [r'^test', r'^fake', r'^admin', r'^\d+$']
            },
            'address_patterns': {
                'suspicious': [r'^test', r'^fake', r'^admin', r'^\d+$', r'^.{1,5}$']
            }
        }
        
        # Poids des facteurs de risque
        self.risk_weights = {
            'high_order_value': 25,
            'suspicious_phone': 30,
            'suspicious_name': 20,
            'suspicious_address': 15,
            'suspicious_city': 20,
            'repeat_customer_fraud': 40,
            'multiple_orders_same_phone': 15,
            'weekend_order': 5,
            'late_night_order': 10
        }
    
    def analyze_order(self, order) -> Dict[str, Any]:
        """
        Analyser une commande COD pour détecter les risques de fraude
        """
        risk_factors = []
        risk_score = 0
        
        # 1. Analyse de la valeur de la commande
        if order.order_value > self.risk_rules['high_value_threshold']:
            risk_factors.append('high_order_value')
            risk_score += self.risk_weights['high_order_value']
        
        # 2. Analyse du numéro de téléphone
        phone_risk = self._analyze_phone(order.customer_phone)
        if phone_risk:
            risk_factors.append('suspicious_phone')
            risk_score += self.risk_weights['suspicious_phone']
        
        # 3. Analyse du nom du client
        name_risk = self._analyze_name(order.customer_name)
        if name_risk:
            risk_factors.append('suspicious_name')
            risk_score += self.risk_weights['suspicious_name']
        
        # 4. Analyse de l'adresse
        address_risk = self._analyze_address(order.delivery_address)
        if address_risk:
            risk_factors.append('suspicious_address')
            risk_score += self.risk_weights['suspicious_address']
        
        # 5. Analyse de la ville
        city_risk = self._analyze_city(order.city)
        if city_risk:
            risk_factors.append('suspicious_city')
            risk_score += self.risk_weights['suspicious_city']
        
        # 6. Analyse de l'historique du client
        customer_history_risk = self._analyze_customer_history(order.customer_phone)
        if customer_history_risk['has_fraud_history']:
            risk_factors.append('repeat_customer_fraud')
            risk_score += self.risk_weights['repeat_customer_fraud']
        
        if customer_history_risk['multiple_recent_orders']:
            risk_factors.append('multiple_orders_same_phone')
            risk_score += self.risk_weights['multiple_orders_same_phone']
        
        # 7. Analyse temporelle
        time_risk = self._analyze_order_timing()
        if time_risk['is_weekend']:
            risk_factors.append('weekend_order')
            risk_score += self.risk_weights['weekend_order']
        
        if time_risk['is_late_night']:
            risk_factors.append('late_night_order')
            risk_score += self.risk_weights['late_night_order']
        
        # Déterminer le niveau de risque
        risk_level = self._calculate_risk_level(risk_score)
        
        # Déterminer si une vérification est requise
        verification_required = risk_level in [CODRiskLevel.HIGH, CODRiskLevel.VERY_HIGH]
        
        return {
            'score': min(risk_score, 100),  # Limiter à 100
            'level': risk_level.value,
            'factors': risk_factors,
            'verification_required': verification_required,
            'details': {
                'phone_analysis': phone_risk,
                'name_analysis': name_risk,
                'address_analysis': address_risk,
                'city_analysis': city_risk,
                'customer_history': customer_history_risk,
                'timing_analysis': time_risk
            }
        }
    
    def _analyze_phone(self, phone: str) -> bool:
        """
        Analyser le numéro de téléphone pour détecter les anomalies
        """
        if not phone:
            return True
        
        # Nettoyer le numéro
        clean_phone = re.sub(r'[^\d]', '', phone)
        
        # Vérifier les patterns suspects
        for pattern in self.risk_rules['phone_patterns']['invalid']:
            if re.match(pattern, clean_phone):
                return True
        
        # Vérifier le format valide
        valid_format = False
        for pattern in self.risk_rules['phone_patterns']['valid']:
            if re.match(pattern, clean_phone):
                valid_format = True
                break
        
        return not valid_format
    
    def _analyze_name(self, name: str) -> bool:
        """
        Analyser le nom du client pour détecter les anomalies
        """
        if not name or len(name.strip()) < 2:
            return True
        
        name_lower = name.lower().strip()
        
        # Vérifier les patterns suspects
        for pattern in self.risk_rules['name_patterns']['suspicious']:
            if re.match(pattern, name_lower):
                return True
        
        return False
    
    def _analyze_address(self, address: str) -> bool:
        """
        Analyser l'adresse de livraison pour détecter les anomalies
        """
        if not address or len(address.strip()) < 5:
            return True
        
        address_lower = address.lower().strip()
        
        # Vérifier les patterns suspects
        for pattern in self.risk_rules['address_patterns']['suspicious']:
            if re.match(pattern, address_lower):
                return True
        
        return False
    
    def _analyze_city(self, city: str) -> bool:
        """
        Analyser la ville pour détecter les anomalies
        """
        if not city:
            return True
        
        return city.strip() in self.risk_rules['suspicious_cities']
    
    def _analyze_customer_history(self, phone: str) -> Dict[str, Any]:
        """
        Analyser l'historique du client
        """
        # Rechercher les commandes précédentes avec le même numéro
        previous_orders = CODOrder.query.filter_by(customer_phone=phone).all()
        
        # Vérifier s'il y a eu des fraudes confirmées
        fraud_history = any(
            'FRAUDE' in (order.notes or '') 
            for order in previous_orders
        )
        
        # Vérifier les commandes multiples récentes (dernières 24h)
        recent_threshold = datetime.utcnow() - timedelta(hours=24)
        recent_orders = [
            order for order in previous_orders 
            if order.created_at >= recent_threshold
        ]
        
        return {
            'has_fraud_history': fraud_history,
            'multiple_recent_orders': len(recent_orders) > 1,
            'total_previous_orders': len(previous_orders),
            'recent_orders_count': len(recent_orders)
        }
    
    def _analyze_order_timing(self) -> Dict[str, bool]:
        """
        Analyser le timing de la commande
        """
        now = datetime.utcnow()
        
        # Vérifier si c'est le weekend (samedi = 5, dimanche = 6)
        is_weekend = now.weekday() >= 5
        
        # Vérifier si c'est tard le soir ou tôt le matin (22h-6h)
        is_late_night = now.hour >= 22 or now.hour <= 6
        
        return {
            'is_weekend': is_weekend,
            'is_late_night': is_late_night,
            'hour': now.hour,
            'weekday': now.weekday()
        }
    
    def _calculate_risk_level(self, risk_score: float) -> CODRiskLevel:
        """
        Calculer le niveau de risque basé sur le score
        """
        if risk_score >= 70:
            return CODRiskLevel.VERY_HIGH
        elif risk_score >= 50:
            return CODRiskLevel.HIGH
        elif risk_score >= 25:
            return CODRiskLevel.MEDIUM
        else:
            return CODRiskLevel.LOW
    
    def update_fraud_model(self, order, fraud_type: str, details: str):
        """
        Mettre à jour le modèle de détection basé sur les fraudes confirmées
        """
        # Cette méthode permettrait d'améliorer le modèle avec l'apprentissage
        # Pour l'instant, on log les informations pour analyse future
        fraud_data = {
            'order_id': order.order_id,
            'fraud_type': fraud_type,
            'details': details,
            'risk_factors': order.risk_factors,
            'risk_score': order.risk_score,
            'customer_phone': order.customer_phone,
            'city': order.city,
            'order_value': order.order_value,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        # Dans une implémentation réelle, ceci serait sauvegardé dans une base de données
        # pour l'analyse et l'amélioration du modèle
        print(f"Fraude confirmée enregistrée: {json.dumps(fraud_data, indent=2)}")
    
    def get_risk_factors_analysis(self, start_date: datetime) -> List[Dict[str, Any]]:
        """
        Analyser les facteurs de risque les plus fréquents
        """
        # Récupérer toutes les commandes avec facteurs de risque depuis start_date
        orders = CODOrder.query.filter(
            CODOrder.created_at >= start_date,
            CODOrder.risk_factors.isnot(None)
        ).all()
        
        # Compter les occurrences de chaque facteur de risque
        factor_counts = {}
        total_orders = len(orders)
        
        for order in orders:
            if order.risk_factors:
                for factor in order.risk_factors:
                    factor_counts[factor] = factor_counts.get(factor, 0) + 1
        
        # Créer la liste des facteurs triés par fréquence
        risk_factors_analysis = []
        for factor, count in sorted(factor_counts.items(), key=lambda x: x[1], reverse=True):
            percentage = (count / total_orders * 100) if total_orders > 0 else 0
            risk_factors_analysis.append({
                'factor': factor,
                'count': count,
                'percentage': round(percentage, 2),
                'weight': self.risk_weights.get(factor, 0)
            })
        
        return risk_factors_analysis
    
    def get_city_risk_profile(self, city: str) -> Dict[str, Any]:
        """
        Obtenir le profil de risque d'une ville
        """
        # Analyser les commandes des 90 derniers jours pour cette ville
        ninety_days_ago = datetime.utcnow() - timedelta(days=90)
        
        city_orders = CODOrder.query.filter(
            CODOrder.city == city,
            CODOrder.created_at >= ninety_days_ago
        ).all()
        
        if not city_orders:
            return {
                'city': city,
                'total_orders': 0,
                'risk_profile': 'unknown'
            }
        
        # Calculer les statistiques
        total_orders = len(city_orders)
        avg_risk_score = sum(order.risk_score for order in city_orders) / total_orders
        
        fraud_orders = [
            order for order in city_orders 
            if order.notes and 'FRAUDE' in order.notes
        ]
        fraud_rate = len(fraud_orders) / total_orders * 100
        
        # Déterminer le profil de risque de la ville
        if fraud_rate > 20 or avg_risk_score > 60:
            risk_profile = 'high_risk'
        elif fraud_rate > 10 or avg_risk_score > 40:
            risk_profile = 'medium_risk'
        else:
            risk_profile = 'low_risk'
        
        return {
            'city': city,
            'total_orders': total_orders,
            'avg_risk_score': round(avg_risk_score, 2),
            'fraud_rate': round(fraud_rate, 2),
            'fraud_orders': len(fraud_orders),
            'risk_profile': risk_profile
        }

