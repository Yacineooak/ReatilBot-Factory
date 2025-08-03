from flask import Blueprint, jsonify, request
from src.models.base import db
from src.models.conversation import Conversation, Message
from src.models.management import AbandonedCart, CODOrder, InventoryItem, InventoryAlert
from datetime import datetime, timedelta
import json

analytics_bp = Blueprint('analytics', __name__)

@analytics_bp.route('/analytics/dashboard', methods=['GET'])
def get_dashboard_overview():
    """
    Obtenir les métriques principales du tableau de bord
    """
    try:
        # Période d'analyse (par défaut 30 derniers jours)
        days = int(request.args.get('days', 30))
        start_date = datetime.utcnow() - timedelta(days=days)
        
        # Métriques des conversations
        total_conversations = Conversation.query.filter(
            Conversation.created_at >= start_date
        ).count()
        
        total_messages = Message.query.filter(
            Message.timestamp >= start_date
        ).count()
        
        avg_messages_per_conversation = (total_messages / total_conversations) if total_conversations > 0 else 0
        
        # Métriques des paniers abandonnés
        total_abandoned_carts = AbandonedCart.query.filter(
            AbandonedCart.abandoned_at >= start_date
        ).count()
        
        recovered_carts = AbandonedCart.query.filter(
            AbandonedCart.abandoned_at >= start_date,
            AbandonedCart.status == 'converted'
        ).count()
        
        cart_recovery_rate = (recovered_carts / total_abandoned_carts * 100) if total_abandoned_carts > 0 else 0
        
        total_cart_value = db.session.query(
            db.func.sum(AbandonedCart.cart_value)
        ).filter(
            AbandonedCart.abandoned_at >= start_date
        ).scalar() or 0
        
        recovered_value = db.session.query(
            db.func.sum(AbandonedCart.conversion_value)
        ).filter(
            AbandonedCart.abandoned_at >= start_date,
            AbandonedCart.status == 'converted'
        ).scalar() or 0
        
        # Métriques COD
        total_cod_orders = CODOrder.query.filter(
            CODOrder.created_at >= start_date
        ).count()
        
        high_risk_orders = CODOrder.query.filter(
            CODOrder.created_at >= start_date,
            CODOrder.risk_level.in_(['high', 'very_high'])
        ).count()
        
        verified_orders = CODOrder.query.filter(
            CODOrder.created_at >= start_date,
            CODOrder.verification_status == 'verified'
        ).count()
        
        # Métriques d'inventaire
        total_inventory_items = InventoryItem.query.filter(
            InventoryItem.is_active == True
        ).count()
        
        low_stock_items = InventoryItem.query.filter(
            InventoryItem.is_active == True,
            InventoryItem.current_stock <= InventoryItem.min_stock_threshold
        ).count()
        
        active_alerts = InventoryAlert.query.filter(
            InventoryAlert.is_resolved == False
        ).count()
        
        return jsonify({
            'period_days': days,
            'conversations': {
                'total': total_conversations,
                'total_messages': total_messages,
                'avg_messages_per_conversation': round(avg_messages_per_conversation, 2)
            },
            'cart_recovery': {
                'total_abandoned': total_abandoned_carts,
                'recovered': recovered_carts,
                'recovery_rate': round(cart_recovery_rate, 2),
                'total_value': total_cart_value,
                'recovered_value': recovered_value,
                'value_recovery_rate': round((recovered_value / total_cart_value * 100) if total_cart_value > 0 else 0, 2)
            },
            'cod_management': {
                'total_orders': total_cod_orders,
                'high_risk_orders': high_risk_orders,
                'risk_percentage': round((high_risk_orders / total_cod_orders * 100) if total_cod_orders > 0 else 0, 2),
                'verified_orders': verified_orders,
                'verification_rate': round((verified_orders / total_cod_orders * 100) if total_cod_orders > 0 else 0, 2)
            },
            'inventory': {
                'total_items': total_inventory_items,
                'low_stock_items': low_stock_items,
                'stock_health_percentage': round(((total_inventory_items - low_stock_items) / total_inventory_items * 100) if total_inventory_items > 0 else 0, 2),
                'active_alerts': active_alerts
            }
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@analytics_bp.route('/analytics/conversations/trends', methods=['GET'])
def get_conversation_trends():
    """
    Obtenir les tendances des conversations
    """
    try:
        days = int(request.args.get('days', 30))
        start_date = datetime.utcnow() - timedelta(days=days)
        
        # Conversations par jour
        daily_conversations = db.session.query(
            db.func.date(Conversation.created_at).label('date'),
            db.func.count(Conversation.id).label('count')
        ).filter(
            Conversation.created_at >= start_date
        ).group_by(
            db.func.date(Conversation.created_at)
        ).order_by('date').all()
        
        # Messages par jour
        daily_messages = db.session.query(
            db.func.date(Message.timestamp).label('date'),
            db.func.count(Message.id).label('count')
        ).filter(
            Message.timestamp >= start_date
        ).group_by(
            db.func.date(Message.timestamp)
        ).order_by('date').all()
        
        # Intentions les plus fréquentes
        top_intents = db.session.query(
            Message.intent,
            db.func.count(Message.id).label('count')
        ).filter(
            Message.timestamp >= start_date,
            Message.intent.isnot(None)
        ).group_by(
            Message.intent
        ).order_by(
            db.func.count(Message.id).desc()
        ).limit(10).all()
        
        return jsonify({
            'daily_conversations': [
                {'date': str(conv.date), 'count': conv.count}
                for conv in daily_conversations
            ],
            'daily_messages': [
                {'date': str(msg.date), 'count': msg.count}
                for msg in daily_messages
            ],
            'top_intents': [
                {'intent': intent.intent, 'count': intent.count}
                for intent in top_intents
            ]
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@analytics_bp.route('/analytics/revenue/trends', methods=['GET'])
def get_revenue_trends():
    """
    Obtenir les tendances de revenus (paniers récupérés)
    """
    try:
        days = int(request.args.get('days', 30))
        start_date = datetime.utcnow() - timedelta(days=days)
        
        # Revenus récupérés par jour
        daily_revenue = db.session.query(
            db.func.date(AbandonedCart.recovered_at).label('date'),
            db.func.sum(AbandonedCart.conversion_value).label('revenue'),
            db.func.count(AbandonedCart.id).label('orders')
        ).filter(
            AbandonedCart.recovered_at >= start_date,
            AbandonedCart.status == 'converted'
        ).group_by(
            db.func.date(AbandonedCart.recovered_at)
        ).order_by('date').all()
        
        # Valeur moyenne des paniers par jour
        daily_avg_cart = db.session.query(
            db.func.date(AbandonedCart.abandoned_at).label('date'),
            db.func.avg(AbandonedCart.cart_value).label('avg_value')
        ).filter(
            AbandonedCart.abandoned_at >= start_date
        ).group_by(
            db.func.date(AbandonedCart.abandoned_at)
        ).order_by('date').all()
        
        # Performance par canal de récupération
        channel_performance = db.session.query(
            db.func.json_extract(AbandonedCart.recovery_attempts, '$.channel').label('channel'),
            db.func.count(AbandonedCart.id).label('attempts'),
            db.func.sum(db.case([(AbandonedCart.status == 'converted', 1)], else_=0)).label('conversions')
        ).filter(
            AbandonedCart.abandoned_at >= start_date
        ).group_by('channel').all()
        
        return jsonify({
            'daily_revenue': [
                {
                    'date': str(rev.date),
                    'revenue': float(rev.revenue or 0),
                    'orders': rev.orders
                }
                for rev in daily_revenue
            ],
            'daily_avg_cart_value': [
                {
                    'date': str(cart.date),
                    'avg_value': float(cart.avg_value or 0)
                }
                for cart in daily_avg_cart
            ],
            'channel_performance': [
                {
                    'channel': perf.channel or 'unknown',
                    'attempts': perf.attempts,
                    'conversions': perf.conversions,
                    'conversion_rate': round((perf.conversions / perf.attempts * 100) if perf.attempts > 0 else 0, 2)
                }
                for perf in channel_performance
            ]
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@analytics_bp.route('/analytics/risk/analysis', methods=['GET'])
def get_risk_analysis():
    """
    Analyse des risques COD
    """
    try:
        days = int(request.args.get('days', 30))
        start_date = datetime.utcnow() - timedelta(days=days)
        
        # Distribution des niveaux de risque
        risk_distribution = db.session.query(
            CODOrder.risk_level,
            db.func.count(CODOrder.id).label('count'),
            db.func.avg(CODOrder.order_value).label('avg_value')
        ).filter(
            CODOrder.created_at >= start_date
        ).group_by(
            CODOrder.risk_level
        ).all()
        
        # Évolution du risque par jour
        daily_risk = db.session.query(
            db.func.date(CODOrder.created_at).label('date'),
            db.func.avg(CODOrder.risk_score).label('avg_risk_score'),
            db.func.count(CODOrder.id).label('total_orders')
        ).filter(
            CODOrder.created_at >= start_date
        ).group_by(
            db.func.date(CODOrder.created_at)
        ).order_by('date').all()
        
        # Top villes à risque
        city_risk = db.session.query(
            CODOrder.city,
            db.func.count(CODOrder.id).label('total_orders'),
            db.func.avg(CODOrder.risk_score).label('avg_risk_score'),
            db.func.sum(db.case([(CODOrder.risk_level.in_(['high', 'very_high']), 1)], else_=0)).label('high_risk_orders')
        ).filter(
            CODOrder.created_at >= start_date
        ).group_by(
            CODOrder.city
        ).having(
            db.func.count(CODOrder.id) >= 5  # Au moins 5 commandes
        ).order_by(
            db.func.avg(CODOrder.risk_score).desc()
        ).limit(10).all()
        
        return jsonify({
            'risk_distribution': [
                {
                    'risk_level': dist.risk_level,
                    'count': dist.count,
                    'avg_value': float(dist.avg_value or 0)
                }
                for dist in risk_distribution
            ],
            'daily_risk_trends': [
                {
                    'date': str(risk.date),
                    'avg_risk_score': float(risk.avg_risk_score or 0),
                    'total_orders': risk.total_orders
                }
                for risk in daily_risk
            ],
            'top_risk_cities': [
                {
                    'city': city.city,
                    'total_orders': city.total_orders,
                    'avg_risk_score': float(city.avg_risk_score or 0),
                    'high_risk_orders': city.high_risk_orders,
                    'risk_percentage': round((city.high_risk_orders / city.total_orders * 100) if city.total_orders > 0 else 0, 2)
                }
                for city in city_risk
            ]
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@analytics_bp.route('/analytics/inventory/insights', methods=['GET'])
def get_inventory_insights():
    """
    Insights sur l'inventaire
    """
    try:
        # Top articles à faible stock
        low_stock_items = InventoryItem.query.filter(
            InventoryItem.is_active == True,
            InventoryItem.current_stock <= InventoryItem.min_stock_threshold
        ).order_by(
            InventoryItem.current_stock
        ).limit(10).all()
        
        # Articles les plus vendus (basé sur les mouvements récents)
        from src.models.management import InventoryMovement
        
        top_selling_items = db.session.query(
            InventoryItem.product_name,
            InventoryItem.current_stock,
            db.func.sum(InventoryMovement.quantity).label('total_sold')
        ).join(
            InventoryMovement, InventoryItem.id == InventoryMovement.item_id
        ).filter(
            InventoryMovement.movement_type == 'out',
            InventoryMovement.created_at >= datetime.utcnow() - timedelta(days=30)
        ).group_by(
            InventoryItem.id
        ).order_by(
            db.func.sum(InventoryMovement.quantity).desc()
        ).limit(10).all()
        
        # Distribution par catégorie
        category_distribution = db.session.query(
            InventoryItem.category,
            db.func.count(InventoryItem.id).label('count'),
            db.func.sum(InventoryItem.current_stock).label('total_stock'),
            db.func.sum(InventoryItem.current_stock * InventoryItem.cost_price).label('total_value')
        ).filter(
            InventoryItem.is_active == True,
            InventoryItem.cost_price.isnot(None)
        ).group_by(
            InventoryItem.category
        ).all()
        
        # Alertes par type
        alert_types = db.session.query(
            InventoryAlert.alert_type,
            InventoryAlert.severity,
            db.func.count(InventoryAlert.id).label('count')
        ).filter(
            InventoryAlert.is_resolved == False
        ).group_by(
            InventoryAlert.alert_type,
            InventoryAlert.severity
        ).all()
        
        return jsonify({
            'low_stock_items': [
                {
                    'product_name': item.product_name,
                    'current_stock': item.current_stock,
                    'min_threshold': item.min_stock_threshold,
                    'category': item.category
                }
                for item in low_stock_items
            ],
            'top_selling_items': [
                {
                    'product_name': item.product_name,
                    'current_stock': item.current_stock,
                    'total_sold': item.total_sold
                }
                for item in top_selling_items
            ],
            'category_distribution': [
                {
                    'category': cat.category or 'Non catégorisé',
                    'count': cat.count,
                    'total_stock': cat.total_stock,
                    'total_value': float(cat.total_value or 0)
                }
                for cat in category_distribution
            ],
            'active_alerts': [
                {
                    'alert_type': alert.alert_type,
                    'severity': alert.severity,
                    'count': alert.count
                }
                for alert in alert_types
            ]
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@analytics_bp.route('/analytics/performance/kpis', methods=['GET'])
def get_performance_kpis():
    """
    KPIs de performance globale
    """
    try:
        days = int(request.args.get('days', 30))
        start_date = datetime.utcnow() - timedelta(days=days)
        
        # Calcul des KPIs
        
        # 1. Taux de résolution des conversations
        total_conversations = Conversation.query.filter(
            Conversation.created_at >= start_date
        ).count()
        
        resolved_conversations = Conversation.query.filter(
            Conversation.created_at >= start_date,
            Conversation.status == 'resolved'
        ).count()
        
        conversation_resolution_rate = (resolved_conversations / total_conversations * 100) if total_conversations > 0 else 0
        
        # 2. Temps de réponse moyen (simulé)
        avg_response_time = 2.5  # En secondes (à calculer réellement avec timestamps)
        
        # 3. Satisfaction client (simulé basé sur les conversations résolues)
        customer_satisfaction = min(95, 70 + (conversation_resolution_rate * 0.3))
        
        # 4. ROI de la récupération de paniers
        total_abandoned_value = db.session.query(
            db.func.sum(AbandonedCart.cart_value)
        ).filter(
            AbandonedCart.abandoned_at >= start_date
        ).scalar() or 0
        
        recovered_value = db.session.query(
            db.func.sum(AbandonedCart.conversion_value)
        ).filter(
            AbandonedCart.abandoned_at >= start_date,
            AbandonedCart.status == 'converted'
        ).scalar() or 0
        
        cart_recovery_roi = (recovered_value / total_abandoned_value * 100) if total_abandoned_value > 0 else 0
        
        # 5. Efficacité de la détection de fraude
        total_cod_orders = CODOrder.query.filter(
            CODOrder.created_at >= start_date
        ).count()
        
        prevented_fraud = CODOrder.query.filter(
            CODOrder.created_at >= start_date,
            CODOrder.verification_status == 'failed'
        ).count()
        
        fraud_prevention_rate = (prevented_fraud / total_cod_orders * 100) if total_cod_orders > 0 else 0
        
        # 6. Santé de l'inventaire
        total_items = InventoryItem.query.filter(InventoryItem.is_active == True).count()
        healthy_items = InventoryItem.query.filter(
            InventoryItem.is_active == True,
            InventoryItem.current_stock > InventoryItem.min_stock_threshold,
            InventoryItem.current_stock < InventoryItem.max_stock_threshold
        ).count()
        
        inventory_health_score = (healthy_items / total_items * 100) if total_items > 0 else 0
        
        return jsonify({
            'period_days': days,
            'kpis': {
                'conversation_resolution_rate': {
                    'value': round(conversation_resolution_rate, 2),
                    'unit': '%',
                    'description': 'Taux de résolution des conversations',
                    'target': 85,
                    'status': 'good' if conversation_resolution_rate >= 85 else 'warning' if conversation_resolution_rate >= 70 else 'critical'
                },
                'avg_response_time': {
                    'value': avg_response_time,
                    'unit': 'secondes',
                    'description': 'Temps de réponse moyen',
                    'target': 3.0,
                    'status': 'good' if avg_response_time <= 3.0 else 'warning' if avg_response_time <= 5.0 else 'critical'
                },
                'customer_satisfaction': {
                    'value': round(customer_satisfaction, 2),
                    'unit': '%',
                    'description': 'Satisfaction client',
                    'target': 90,
                    'status': 'good' if customer_satisfaction >= 90 else 'warning' if customer_satisfaction >= 75 else 'critical'
                },
                'cart_recovery_roi': {
                    'value': round(cart_recovery_roi, 2),
                    'unit': '%',
                    'description': 'ROI récupération paniers',
                    'target': 15,
                    'status': 'good' if cart_recovery_roi >= 15 else 'warning' if cart_recovery_roi >= 10 else 'critical'
                },
                'fraud_prevention_rate': {
                    'value': round(fraud_prevention_rate, 2),
                    'unit': '%',
                    'description': 'Taux de prévention fraude',
                    'target': 5,
                    'status': 'good' if fraud_prevention_rate >= 3 else 'warning' if fraud_prevention_rate >= 1 else 'critical'
                },
                'inventory_health_score': {
                    'value': round(inventory_health_score, 2),
                    'unit': '%',
                    'description': 'Score santé inventaire',
                    'target': 80,
                    'status': 'good' if inventory_health_score >= 80 else 'warning' if inventory_health_score >= 60 else 'critical'
                }
            }
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

