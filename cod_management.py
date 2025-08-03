from flask import Blueprint, jsonify, request
from src.models.management import CODOrder, CODRiskLevel, OrderStatus, db
from src.services.fraud_detection_service import FraudDetectionService
from src.services.verification_service import VerificationService
from datetime import datetime, timedelta

cod_management_bp = Blueprint('cod_management', __name__)

# Initialisation des services
fraud_detection_service = FraudDetectionService()
verification_service = VerificationService()

@cod_management_bp.route('/cod-orders', methods=['GET'])
def get_cod_orders():
    """
    Récupérer la liste des commandes COD
    """
    try:
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 20))
        risk_level = request.args.get('risk_level')
        status = request.args.get('status')
        verification_required = request.args.get('verification_required')
        
        query = CODOrder.query
        
        if risk_level:
            query = query.filter(CODOrder.risk_level == CODRiskLevel(risk_level))
        
        if status:
            query = query.filter(CODOrder.status == OrderStatus(status))
        
        if verification_required is not None:
            query = query.filter(CODOrder.verification_required == (verification_required.lower() == 'true'))
        
        # Trier par score de risque (plus élevé en premier) puis par date
        query = query.order_by(CODOrder.risk_score.desc(), CODOrder.created_at.desc())
        
        orders = query.paginate(
            page=page, 
            per_page=per_page, 
            error_out=False
        )
        
        return jsonify({
            'orders': [order.to_dict() for order in orders.items],
            'total': orders.total,
            'pages': orders.pages,
            'current_page': page,
            'per_page': per_page
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@cod_management_bp.route('/cod-orders', methods=['POST'])
def create_cod_order():
    """
    Créer une nouvelle commande COD avec analyse de risque
    """
    try:
        data = request.json
        
        # Validation des données requises
        required_fields = ['order_id', 'customer_name', 'customer_phone', 'delivery_address', 'city', 'order_value']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Champ requis manquant: {field}'}), 400
        
        # Vérifier si la commande existe déjà
        existing_order = CODOrder.query.filter_by(order_id=data['order_id']).first()
        if existing_order:
            return jsonify({'error': 'Commande déjà enregistrée'}), 409
        
        # Créer la commande COD
        order = CODOrder(
            order_id=data['order_id'],
            customer_name=data['customer_name'],
            customer_phone=data['customer_phone'],
            customer_email=data.get('customer_email'),
            delivery_address=data['delivery_address'],
            city=data['city'],
            postal_code=data.get('postal_code'),
            order_value=data['order_value'],
            currency=data.get('currency', 'DZD'),
            notes=data.get('notes')
        )
        
        # Analyser le risque de fraude
        risk_analysis = fraud_detection_service.analyze_order(order)
        order.risk_score = risk_analysis['score']
        order.risk_level = CODRiskLevel(risk_analysis['level'])
        order.risk_factors = risk_analysis['factors']
        order.verification_required = risk_analysis['verification_required']
        
        db.session.add(order)
        db.session.commit()
        
        # Si vérification requise, déclencher le processus
        if order.verification_required:
            verification_service.initiate_verification(order.id)
        
        return jsonify(order.to_dict()), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@cod_management_bp.route('/cod-orders/<int:order_id>/verify', methods=['POST'])
def verify_order(order_id):
    """
    Déclencher la vérification d'une commande COD
    """
    try:
        order = CODOrder.query.get_or_404(order_id)
        data = request.json
        
        verification_method = data.get('method', 'phone_call')  # 'phone_call', 'sms', 'whatsapp'
        
        # Déclencher la vérification
        result = verification_service.verify_order(order.id, verification_method)
        
        # Mettre à jour le statut de vérification
        order.verification_attempts += 1
        order.updated_at = datetime.utcnow()
        
        if result['success']:
            order.verification_status = 'verified'
            order.verified_at = datetime.utcnow()
            order.status = OrderStatus.CONFIRMED
        else:
            order.verification_status = 'failed'
        
        db.session.commit()
        
        return jsonify({
            'message': 'Vérification initiée',
            'result': result,
            'order': order.to_dict()
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@cod_management_bp.route('/cod-orders/<int:order_id>/status', methods=['PUT'])
def update_order_status(order_id):
    """
    Mettre à jour le statut d'une commande COD
    """
    try:
        order = CODOrder.query.get_or_404(order_id)
        data = request.json
        
        new_status = data.get('status')
        notes = data.get('notes')
        
        if new_status:
            order.status = OrderStatus(new_status)
        
        if notes:
            order.notes = notes
        
        order.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'message': 'Statut mis à jour',
            'order': order.to_dict()
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@cod_management_bp.route('/cod-orders/risk-analysis', methods=['GET'])
def get_risk_analysis():
    """
    Obtenir l'analyse des risques COD
    """
    try:
        # Période d'analyse (par défaut 30 derniers jours)
        days = int(request.args.get('days', 30))
        start_date = datetime.utcnow() - timedelta(days=days)
        
        # Statistiques par niveau de risque
        risk_stats = {}
        for risk_level in CODRiskLevel:
            count = CODOrder.query.filter(
                CODOrder.created_at >= start_date,
                CODOrder.risk_level == risk_level
            ).count()
            
            # Taux de fraude confirmée pour ce niveau
            fraud_count = CODOrder.query.filter(
                CODOrder.created_at >= start_date,
                CODOrder.risk_level == risk_level,
                CODOrder.status == OrderStatus.CANCELLED,
                CODOrder.notes.contains('fraude')
            ).count()
            
            fraud_rate = (fraud_count / count * 100) if count > 0 else 0
            
            risk_stats[risk_level.value] = {
                'count': count,
                'fraud_count': fraud_count,
                'fraud_rate': round(fraud_rate, 2)
            }
        
        # Statistiques de vérification
        total_orders = CODOrder.query.filter(CODOrder.created_at >= start_date).count()
        verification_required = CODOrder.query.filter(
            CODOrder.created_at >= start_date,
            CODOrder.verification_required == True
        ).count()
        
        verified_orders = CODOrder.query.filter(
            CODOrder.created_at >= start_date,
            CODOrder.verification_status == 'verified'
        ).count()
        
        failed_verifications = CODOrder.query.filter(
            CODOrder.created_at >= start_date,
            CODOrder.verification_status == 'failed'
        ).count()
        
        # Top facteurs de risque
        risk_factors_analysis = fraud_detection_service.get_risk_factors_analysis(start_date)
        
        return jsonify({
            'period_days': days,
            'total_orders': total_orders,
            'risk_distribution': risk_stats,
            'verification_stats': {
                'verification_required': verification_required,
                'verification_rate': round((verification_required / total_orders * 100) if total_orders > 0 else 0, 2),
                'verified_orders': verified_orders,
                'failed_verifications': failed_verifications,
                'verification_success_rate': round((verified_orders / verification_required * 100) if verification_required > 0 else 0, 2)
            },
            'top_risk_factors': risk_factors_analysis
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@cod_management_bp.route('/cod-orders/fraud-report', methods=['POST'])
def report_fraud():
    """
    Signaler une commande comme frauduleuse
    """
    try:
        data = request.json
        order_id = data.get('order_id')
        fraud_type = data.get('fraud_type', 'confirmed')
        details = data.get('details', '')
        
        order = CODOrder.query.filter_by(order_id=order_id).first()
        if not order:
            return jsonify({'error': 'Commande non trouvée'}), 404
        
        # Mettre à jour le statut et les notes
        order.status = OrderStatus.CANCELLED
        order.notes = f"FRAUDE CONFIRMÉE - Type: {fraud_type} - Détails: {details}"
        order.updated_at = datetime.utcnow()
        
        # Mettre à jour le modèle de détection de fraude
        fraud_detection_service.update_fraud_model(order, fraud_type, details)
        
        db.session.commit()
        
        return jsonify({
            'message': 'Fraude signalée et modèle mis à jour',
            'order': order.to_dict()
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@cod_management_bp.route('/cod-orders/cities-analysis', methods=['GET'])
def get_cities_analysis():
    """
    Analyse des risques par ville
    """
    try:
        days = int(request.args.get('days', 30))
        start_date = datetime.utcnow() - timedelta(days=days)
        
        # Requête pour obtenir les statistiques par ville
        cities_stats = db.session.query(
            CODOrder.city,
            db.func.count(CODOrder.id).label('total_orders'),
            db.func.avg(CODOrder.risk_score).label('avg_risk_score'),
            db.func.count(db.case([(CODOrder.status == OrderStatus.CANCELLED, 1)])).label('cancelled_orders'),
            db.func.count(db.case([(CODOrder.verification_required == True, 1)])).label('verification_required')
        ).filter(
            CODOrder.created_at >= start_date
        ).group_by(CODOrder.city).all()
        
        cities_analysis = []
        for city_stat in cities_stats:
            cancellation_rate = (city_stat.cancelled_orders / city_stat.total_orders * 100) if city_stat.total_orders > 0 else 0
            verification_rate = (city_stat.verification_required / city_stat.total_orders * 100) if city_stat.total_orders > 0 else 0
            
            cities_analysis.append({
                'city': city_stat.city,
                'total_orders': city_stat.total_orders,
                'avg_risk_score': round(city_stat.avg_risk_score or 0, 2),
                'cancelled_orders': city_stat.cancelled_orders,
                'cancellation_rate': round(cancellation_rate, 2),
                'verification_required': city_stat.verification_required,
                'verification_rate': round(verification_rate, 2)
            })
        
        # Trier par score de risque moyen
        cities_analysis.sort(key=lambda x: x['avg_risk_score'], reverse=True)
        
        return jsonify({
            'period_days': days,
            'cities_analysis': cities_analysis
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

