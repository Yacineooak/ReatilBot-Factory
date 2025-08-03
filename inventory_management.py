from flask import Blueprint, jsonify, request
from src.models.management import InventoryItem, InventoryAlert, InventoryMovement, db
from src.services.inventory_service import InventoryService
from datetime import datetime, timedelta
import csv
import io

inventory_management_bp = Blueprint('inventory_management', __name__)

# Initialisation du service d'inventaire
inventory_service = InventoryService()

@inventory_management_bp.route('/inventory/items', methods=['GET'])
def get_inventory_items():
    """
    Récupérer la liste des articles d'inventaire
    """
    try:
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 20))
        category = request.args.get('category')
        low_stock = request.args.get('low_stock')
        search = request.args.get('search')
        
        query = InventoryItem.query.filter(InventoryItem.is_active == True)
        
        if category:
            query = query.filter(InventoryItem.category == category)
        
        if low_stock and low_stock.lower() == 'true':
            query = query.filter(InventoryItem.current_stock <= InventoryItem.min_stock_threshold)
        
        if search:
            query = query.filter(
                InventoryItem.product_name.contains(search) |
                InventoryItem.sku.contains(search)
            )
        
        # Trier par stock faible en premier, puis par nom
        query = query.order_by(
            (InventoryItem.current_stock <= InventoryItem.min_stock_threshold).desc(),
            InventoryItem.product_name
        )
        
        items = query.paginate(
            page=page, 
            per_page=per_page, 
            error_out=False
        )
        
        return jsonify({
            'items': [item.to_dict() for item in items.items],
            'total': items.total,
            'pages': items.pages,
            'current_page': page,
            'per_page': per_page
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@inventory_management_bp.route('/inventory/items', methods=['POST'])
def create_inventory_item():
    """
    Créer un nouvel article d'inventaire
    """
    try:
        data = request.json
        
        # Validation des données requises
        required_fields = ['product_id', 'product_name', 'current_stock']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Champ requis manquant: {field}'}), 400
        
        # Vérifier si l'article existe déjà
        existing_item = InventoryItem.query.filter_by(product_id=data['product_id']).first()
        if existing_item:
            return jsonify({'error': 'Article déjà existant'}), 409
        
        # Créer l'article d'inventaire
        item = InventoryItem(
            product_id=data['product_id'],
            product_name=data['product_name'],
            sku=data.get('sku'),
            category=data.get('category'),
            brand=data.get('brand'),
            current_stock=data['current_stock'],
            reserved_stock=data.get('reserved_stock', 0),
            min_stock_threshold=data.get('min_stock_threshold', 10),
            max_stock_threshold=data.get('max_stock_threshold', 1000),
            reorder_point=data.get('reorder_point', 20),
            reorder_quantity=data.get('reorder_quantity', 100),
            cost_price=data.get('cost_price'),
            selling_price=data.get('selling_price'),
            supplier_id=data.get('supplier_id'),
            supplier_name=data.get('supplier_name')
        )
        
        # Calculer le stock disponible
        item.available_stock = item.current_stock - item.reserved_stock
        
        db.session.add(item)
        db.session.commit()
        
        # Vérifier si des alertes doivent être créées
        inventory_service.check_and_create_alerts(item.id)
        
        return jsonify(item.to_dict()), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@inventory_management_bp.route('/inventory/items/<int:item_id>', methods=['PUT'])
def update_inventory_item(item_id):
    """
    Mettre à jour un article d'inventaire
    """
    try:
        item = InventoryItem.query.get_or_404(item_id)
        data = request.json
        
        # Mettre à jour les champs modifiables
        updatable_fields = [
            'product_name', 'sku', 'category', 'brand', 'min_stock_threshold',
            'max_stock_threshold', 'reorder_point', 'reorder_quantity',
            'cost_price', 'selling_price', 'supplier_id', 'supplier_name'
        ]
        
        for field in updatable_fields:
            if field in data:
                setattr(item, field, data[field])
        
        item.updated_at = datetime.utcnow()
        db.session.commit()
        
        # Vérifier si des alertes doivent être créées
        inventory_service.check_and_create_alerts(item.id)
        
        return jsonify(item.to_dict())
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@inventory_management_bp.route('/inventory/items/<int:item_id>/movement', methods=['POST'])
def create_inventory_movement():
    """
    Créer un mouvement d'inventaire (entrée/sortie/ajustement)
    """
    try:
        item_id = request.view_args['item_id']
        item = InventoryItem.query.get_or_404(item_id)
        data = request.json
        
        # Validation des données requises
        required_fields = ['movement_type', 'quantity']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Champ requis manquant: {field}'}), 400
        
        movement_type = data['movement_type']
        quantity = int(data['quantity'])
        
        if movement_type not in ['in', 'out', 'adjustment', 'transfer']:
            return jsonify({'error': 'Type de mouvement invalide'}), 400
        
        # Créer le mouvement
        movement = InventoryMovement(
            item_id=item.id,
            movement_type=movement_type,
            quantity=quantity,
            reference_id=data.get('reference_id'),
            reference_type=data.get('reference_type'),
            reason=data.get('reason'),
            notes=data.get('notes'),
            performed_by=data.get('performed_by')
        )
        
        # Mettre à jour le stock
        if movement_type == 'in':
            item.current_stock += quantity
            if data.get('reference_type') == 'restock':
                item.last_restocked = datetime.utcnow()
        elif movement_type == 'out':
            if item.current_stock < quantity:
                return jsonify({'error': 'Stock insuffisant'}), 400
            item.current_stock -= quantity
            item.last_sold = datetime.utcnow()
        elif movement_type == 'adjustment':
            # Pour les ajustements, la quantité peut être positive ou négative
            item.current_stock += quantity
        
        # Recalculer le stock disponible
        item.available_stock = item.current_stock - item.reserved_stock
        item.updated_at = datetime.utcnow()
        
        db.session.add(movement)
        db.session.commit()
        
        # Vérifier si des alertes doivent être créées
        inventory_service.check_and_create_alerts(item.id)
        
        return jsonify({
            'message': 'Mouvement d\'inventaire créé',
            'movement': movement.to_dict(),
            'item': item.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@inventory_management_bp.route('/inventory/alerts', methods=['GET'])
def get_inventory_alerts():
    """
    Récupérer les alertes d'inventaire
    """
    try:
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 20))
        alert_type = request.args.get('alert_type')
        severity = request.args.get('severity')
        resolved = request.args.get('resolved')
        
        query = InventoryAlert.query
        
        if alert_type:
            query = query.filter(InventoryAlert.alert_type == alert_type)
        
        if severity:
            query = query.filter(InventoryAlert.severity == severity)
        
        if resolved is not None:
            query = query.filter(InventoryAlert.is_resolved == (resolved.lower() == 'true'))
        
        # Trier par sévérité puis par date de création
        severity_order = db.case(
            (InventoryAlert.severity == 'critical', 1),
            (InventoryAlert.severity == 'high', 2),
            (InventoryAlert.severity == 'medium', 3),
            (InventoryAlert.severity == 'low', 4),
            else_=5
        )
        
        query = query.order_by(severity_order, InventoryAlert.created_at.desc())
        
        alerts = query.paginate(
            page=page, 
            per_page=per_page, 
            error_out=False
        )
        
        return jsonify({
            'alerts': [alert.to_dict() for alert in alerts.items],
            'total': alerts.total,
            'pages': alerts.pages,
            'current_page': page,
            'per_page': per_page
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@inventory_management_bp.route('/inventory/alerts/<int:alert_id>/resolve', methods=['POST'])
def resolve_alert(alert_id):
    """
    Marquer une alerte comme résolue
    """
    try:
        alert = InventoryAlert.query.get_or_404(alert_id)
        
        alert.is_resolved = True
        alert.resolved_at = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify({
            'message': 'Alerte marquée comme résolue',
            'alert': alert.to_dict()
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@inventory_management_bp.route('/inventory/analytics', methods=['GET'])
def get_inventory_analytics():
    """
    Obtenir les analyses d'inventaire
    """
    try:
        # Statistiques générales
        total_items = InventoryItem.query.filter(InventoryItem.is_active == True).count()
        
        low_stock_items = InventoryItem.query.filter(
            InventoryItem.is_active == True,
            InventoryItem.current_stock <= InventoryItem.min_stock_threshold
        ).count()
        
        out_of_stock_items = InventoryItem.query.filter(
            InventoryItem.is_active == True,
            InventoryItem.current_stock == 0
        ).count()
        
        overstock_items = InventoryItem.query.filter(
            InventoryItem.is_active == True,
            InventoryItem.current_stock >= InventoryItem.max_stock_threshold
        ).count()
        
        # Valeur totale de l'inventaire
        total_inventory_value = db.session.query(
            db.func.sum(InventoryItem.current_stock * InventoryItem.cost_price)
        ).filter(
            InventoryItem.is_active == True,
            InventoryItem.cost_price.isnot(None)
        ).scalar() or 0
        
        # Alertes actives par type
        alert_stats = {}
        for alert_type in ['low_stock', 'out_of_stock', 'overstock']:
            count = InventoryAlert.query.filter(
                InventoryAlert.alert_type == alert_type,
                InventoryAlert.is_resolved == False
            ).count()
            alert_stats[alert_type] = count
        
        # Top 10 des articles à faible stock
        low_stock_top = InventoryItem.query.filter(
            InventoryItem.is_active == True,
            InventoryItem.current_stock <= InventoryItem.min_stock_threshold
        ).order_by(InventoryItem.current_stock).limit(10).all()
        
        # Mouvements récents (7 derniers jours)
        week_ago = datetime.utcnow() - timedelta(days=7)
        recent_movements = db.session.query(
            InventoryMovement.movement_type,
            db.func.count(InventoryMovement.id).label('count'),
            db.func.sum(InventoryMovement.quantity).label('total_quantity')
        ).filter(
            InventoryMovement.created_at >= week_ago
        ).group_by(InventoryMovement.movement_type).all()
        
        movements_stats = {}
        for movement in recent_movements:
            movements_stats[movement.movement_type] = {
                'count': movement.count,
                'total_quantity': movement.total_quantity
            }
        
        return jsonify({
            'summary': {
                'total_items': total_items,
                'low_stock_items': low_stock_items,
                'out_of_stock_items': out_of_stock_items,
                'overstock_items': overstock_items,
                'total_inventory_value': round(total_inventory_value, 2),
                'low_stock_percentage': round((low_stock_items / total_items * 100) if total_items > 0 else 0, 2)
            },
            'alerts': alert_stats,
            'low_stock_top': [item.to_dict() for item in low_stock_top],
            'recent_movements': movements_stats
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@inventory_management_bp.route('/inventory/import', methods=['POST'])
def import_inventory():
    """
    Importer des données d'inventaire depuis un fichier CSV
    """
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'Aucun fichier fourni'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'Aucun fichier sélectionné'}), 400
        
        if not file.filename.endswith('.csv'):
            return jsonify({'error': 'Format de fichier non supporté. Utilisez CSV.'}), 400
        
        # Lire le fichier CSV
        stream = io.StringIO(file.stream.read().decode("UTF8"), newline=None)
        csv_input = csv.DictReader(stream)
        
        imported_count = 0
        updated_count = 0
        errors = []
        
        for row_num, row in enumerate(csv_input, start=2):  # Start=2 car ligne 1 = headers
            try:
                product_id = row.get('product_id')
                if not product_id:
                    errors.append(f"Ligne {row_num}: product_id manquant")
                    continue
                
                # Vérifier si l'article existe
                existing_item = InventoryItem.query.filter_by(product_id=product_id).first()
                
                if existing_item:
                    # Mettre à jour l'article existant
                    existing_item.current_stock = int(row.get('current_stock', existing_item.current_stock))
                    existing_item.min_stock_threshold = int(row.get('min_stock_threshold', existing_item.min_stock_threshold))
                    existing_item.max_stock_threshold = int(row.get('max_stock_threshold', existing_item.max_stock_threshold))
                    existing_item.updated_at = datetime.utcnow()
                    updated_count += 1
                else:
                    # Créer un nouvel article
                    new_item = InventoryItem(
                        product_id=product_id,
                        product_name=row.get('product_name', ''),
                        sku=row.get('sku'),
                        category=row.get('category'),
                        brand=row.get('brand'),
                        current_stock=int(row.get('current_stock', 0)),
                        min_stock_threshold=int(row.get('min_stock_threshold', 10)),
                        max_stock_threshold=int(row.get('max_stock_threshold', 1000)),
                        cost_price=float(row.get('cost_price')) if row.get('cost_price') else None,
                        selling_price=float(row.get('selling_price')) if row.get('selling_price') else None
                    )
                    new_item.available_stock = new_item.current_stock
                    db.session.add(new_item)
                    imported_count += 1
                    
            except Exception as e:
                errors.append(f"Ligne {row_num}: {str(e)}")
        
        db.session.commit()
        
        return jsonify({
            'message': 'Import terminé',
            'imported_count': imported_count,
            'updated_count': updated_count,
            'errors': errors
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@inventory_management_bp.route('/inventory/export', methods=['GET'])
def export_inventory():
    """
    Exporter les données d'inventaire en CSV
    """
    try:
        items = InventoryItem.query.filter(InventoryItem.is_active == True).all()
        
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Headers
        writer.writerow([
            'product_id', 'product_name', 'sku', 'category', 'brand',
            'current_stock', 'reserved_stock', 'available_stock',
            'min_stock_threshold', 'max_stock_threshold', 'reorder_point',
            'reorder_quantity', 'cost_price', 'selling_price',
            'supplier_name', 'last_restocked', 'last_sold'
        ])
        
        # Data
        for item in items:
            writer.writerow([
                item.product_id, item.product_name, item.sku, item.category, item.brand,
                item.current_stock, item.reserved_stock, item.available_stock,
                item.min_stock_threshold, item.max_stock_threshold, item.reorder_point,
                item.reorder_quantity, item.cost_price, item.selling_price,
                item.supplier_name,
                item.last_restocked.isoformat() if item.last_restocked else '',
                item.last_sold.isoformat() if item.last_sold else ''
            ])
        
        output.seek(0)
        
        return jsonify({
            'csv_data': output.getvalue(),
            'filename': f'inventory_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

