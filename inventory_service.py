from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from src.models.management import InventoryItem, InventoryAlert, InventoryMovement, db
from src.services.notification_service import NotificationService

class InventoryService:
    """
    Service de gestion d'inventaire avec alertes automatiques
    """
    
    def __init__(self):
        self.notification_service = NotificationService()
        
        # Configuration des destinataires d'alertes (à configurer par l'utilisateur)
        self.alert_recipients = {
            'email': ['manager@retailbot.com', 'inventory@retailbot.com'],
            'sms': ['+213555123456']  # Numéros de téléphone pour SMS
        }
        
        # Configuration des seuils d'alerte
        self.alert_thresholds = {
            'critical_stock_days': 3,  # Jours de stock restant pour alerte critique
            'low_stock_multiplier': 1.5,  # Multiplicateur du seuil minimum pour alerte
            'overstock_multiplier': 0.9  # Multiplicateur du seuil maximum pour alerte
        }
    
    def check_and_create_alerts(self, item_id: int) -> List[Dict[str, Any]]:
        """
        Vérifier et créer des alertes pour un article d'inventaire
        """
        item = InventoryItem.query.get(item_id)
        if not item or not item.is_active:
            return []
        
        alerts_created = []
        
        # 1. Vérifier le stock faible
        if item.current_stock <= item.min_stock_threshold:
            alert = self._create_alert(
                item=item,
                alert_type='low_stock' if item.current_stock > 0 else 'out_of_stock',
                severity='critical' if item.current_stock == 0 else 'high',
                message=self._generate_alert_message(item, 'low_stock')
            )
            if alert:
                alerts_created.append(alert)
        
        # 2. Vérifier le surstock
        elif item.current_stock >= item.max_stock_threshold:
            alert = self._create_alert(
                item=item,
                alert_type='overstock',
                severity='medium',
                message=self._generate_alert_message(item, 'overstock')
            )
            if alert:
                alerts_created.append(alert)
        
        # 3. Vérifier le point de réapprovisionnement
        elif item.current_stock <= item.reorder_point:
            alert = self._create_alert(
                item=item,
                alert_type='reorder_needed',
                severity='medium',
                message=self._generate_alert_message(item, 'reorder')
            )
            if alert:
                alerts_created.append(alert)
        
        # Envoyer les notifications pour les alertes critiques
        for alert in alerts_created:
            if alert['severity'] in ['critical', 'high']:
                self._send_alert_notification(alert, item)
        
        return alerts_created
    
    def _create_alert(self, item: InventoryItem, alert_type: str, severity: str, message: str) -> Optional[Dict[str, Any]]:
        """
        Créer une alerte d'inventaire si elle n'existe pas déjà
        """
        # Vérifier si une alerte similaire existe déjà (non résolue)
        existing_alert = InventoryAlert.query.filter_by(
            item_id=item.id,
            alert_type=alert_type,
            is_resolved=False
        ).first()
        
        if existing_alert:
            return None  # Alerte déjà existante
        
        # Créer la nouvelle alerte
        alert = InventoryAlert(
            item_id=item.id,
            alert_type=alert_type,
            message=message,
            severity=severity
        )
        
        db.session.add(alert)
        db.session.commit()
        
        return alert.to_dict()
    
    def _generate_alert_message(self, item: InventoryItem, alert_type: str) -> str:
        """
        Générer le message d'alerte approprié
        """
        messages = {
            'low_stock': f"Stock faible pour {item.product_name} (SKU: {item.sku}). "
                        f"Stock actuel: {item.current_stock}, Seuil minimum: {item.min_stock_threshold}",
            
            'out_of_stock': f"RUPTURE DE STOCK pour {item.product_name} (SKU: {item.sku}). "
                           f"Réapprovisionnement urgent requis.",
            
            'overstock': f"Surstock détecté pour {item.product_name} (SKU: {item.sku}). "
                        f"Stock actuel: {item.current_stock}, Seuil maximum: {item.max_stock_threshold}",
            
            'reorder': f"Point de réapprovisionnement atteint pour {item.product_name} (SKU: {item.sku}). "
                      f"Stock actuel: {item.current_stock}, Point de commande: {item.reorder_point}"
        }
        
        return messages.get(alert_type, f"Alerte inventaire pour {item.product_name}")
    
    def _send_alert_notification(self, alert: Dict[str, Any], item: InventoryItem):
        """
        Envoyer une notification d'alerte
        """
        try:
            # Envoyer par email
            for email in self.alert_recipients['email']:
                self.notification_service.send_inventory_alert(
                    recipients=[email],
                    alert_type=alert['alert_type'],
                    item_name=item.product_name,
                    current_stock=item.current_stock,
                    threshold=item.min_stock_threshold if alert['alert_type'] in ['low_stock', 'out_of_stock'] else item.max_stock_threshold
                )
            
            # Envoyer par SMS pour les alertes critiques
            if alert['severity'] == 'critical':
                for phone in self.alert_recipients['sms']:
                    self.notification_service.send_inventory_alert(
                        recipients=[phone],
                        alert_type=alert['alert_type'],
                        item_name=item.product_name,
                        current_stock=item.current_stock,
                        threshold=item.min_stock_threshold
                    )
            
            # Marquer l'alerte comme notifiée
            alert_obj = InventoryAlert.query.get(alert['id'])
            if alert_obj:
                alert_obj.notified_at = datetime.utcnow()
                db.session.commit()
                
        except Exception as e:
            print(f"Erreur envoi notification alerte: {e}")
    
    def bulk_stock_update(self, updates: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Mise à jour en lot des stocks
        """
        results = {
            'updated': 0,
            'errors': [],
            'alerts_created': []
        }
        
        for update in updates:
            try:
                product_id = update.get('product_id')
                new_stock = update.get('stock')
                movement_type = update.get('movement_type', 'adjustment')
                
                if not product_id or new_stock is None:
                    results['errors'].append(f"Données manquantes pour {product_id}")
                    continue
                
                item = InventoryItem.query.filter_by(product_id=product_id).first()
                if not item:
                    results['errors'].append(f"Article non trouvé: {product_id}")
                    continue
                
                # Calculer la différence
                difference = new_stock - item.current_stock
                
                # Créer le mouvement d'inventaire
                movement = InventoryMovement(
                    item_id=item.id,
                    movement_type=movement_type,
                    quantity=difference,
                    reason=update.get('reason', 'Mise à jour en lot'),
                    performed_by=update.get('performed_by', 'System')
                )
                
                # Mettre à jour le stock
                item.current_stock = new_stock
                item.available_stock = new_stock - item.reserved_stock
                item.updated_at = datetime.utcnow()
                
                db.session.add(movement)
                results['updated'] += 1
                
                # Vérifier les alertes
                alerts = self.check_and_create_alerts(item.id)
                results['alerts_created'].extend(alerts)
                
            except Exception as e:
                results['errors'].append(f"Erreur pour {product_id}: {str(e)}")
        
        db.session.commit()
        return results
    
    def calculate_stock_velocity(self, item_id: int, days: int = 30) -> Dict[str, Any]:
        """
        Calculer la vélocité de stock (vitesse de rotation)
        """
        item = InventoryItem.query.get(item_id)
        if not item:
            return {'error': 'Article non trouvé'}
        
        # Période d'analyse
        start_date = datetime.utcnow() - timedelta(days=days)
        
        # Récupérer les mouvements de sortie
        outbound_movements = InventoryMovement.query.filter(
            InventoryMovement.item_id == item_id,
            InventoryMovement.movement_type == 'out',
            InventoryMovement.created_at >= start_date
        ).all()
        
        # Calculer la quantité totale vendue
        total_sold = sum(movement.quantity for movement in outbound_movements)
        
        # Calculer la vélocité (unités par jour)
        velocity = total_sold / days if days > 0 else 0
        
        # Estimer les jours de stock restant
        days_of_stock = item.current_stock / velocity if velocity > 0 else float('inf')
        
        # Recommandations
        recommendations = []
        
        if days_of_stock < 7:
            recommendations.append("Réapprovisionnement urgent recommandé")
        elif days_of_stock < 14:
            recommendations.append("Planifier le réapprovisionnement")
        elif days_of_stock > 90:
            recommendations.append("Stock élevé, considérer une promotion")
        
        return {
            'item_id': item_id,
            'product_name': item.product_name,
            'analysis_period_days': days,
            'total_sold': total_sold,
            'velocity_per_day': round(velocity, 2),
            'current_stock': item.current_stock,
            'estimated_days_of_stock': round(days_of_stock, 1) if days_of_stock != float('inf') else 'Illimité',
            'recommendations': recommendations
        }
    
    def generate_reorder_suggestions(self) -> List[Dict[str, Any]]:
        """
        Générer des suggestions de réapprovisionnement
        """
        # Articles nécessitant un réapprovisionnement
        items_to_reorder = InventoryItem.query.filter(
            InventoryItem.is_active == True,
            InventoryItem.current_stock <= InventoryItem.reorder_point
        ).all()
        
        suggestions = []
        
        for item in items_to_reorder:
            # Calculer la vélocité pour une meilleure estimation
            velocity_data = self.calculate_stock_velocity(item.id, 30)
            
            # Quantité suggérée basée sur la vélocité et la quantité de réapprovisionnement
            if velocity_data.get('velocity_per_day', 0) > 0:
                # Calculer pour 30 jours de stock
                suggested_quantity = max(
                    item.reorder_quantity,
                    int(velocity_data['velocity_per_day'] * 30)
                )
            else:
                suggested_quantity = item.reorder_quantity
            
            # Priorité basée sur le niveau de stock et la vélocité
            if item.current_stock == 0:
                priority = 'critical'
            elif item.current_stock <= item.min_stock_threshold:
                priority = 'high'
            else:
                priority = 'medium'
            
            suggestions.append({
                'item_id': item.id,
                'product_id': item.product_id,
                'product_name': item.product_name,
                'sku': item.sku,
                'current_stock': item.current_stock,
                'reorder_point': item.reorder_point,
                'suggested_quantity': suggested_quantity,
                'supplier_name': item.supplier_name,
                'cost_price': item.cost_price,
                'estimated_cost': item.cost_price * suggested_quantity if item.cost_price else None,
                'priority': priority,
                'velocity_data': velocity_data
            })
        
        # Trier par priorité puis par coût estimé
        priority_order = {'critical': 0, 'high': 1, 'medium': 2}
        suggestions.sort(key=lambda x: (priority_order[x['priority']], x['estimated_cost'] or 0))
        
        return suggestions
    
    def get_inventory_health_score(self) -> Dict[str, Any]:
        """
        Calculer un score de santé de l'inventaire
        """
        total_items = InventoryItem.query.filter(InventoryItem.is_active == True).count()
        
        if total_items == 0:
            return {'score': 0, 'status': 'No inventory'}
        
        # Compter les différents types de problèmes
        out_of_stock = InventoryItem.query.filter(
            InventoryItem.is_active == True,
            InventoryItem.current_stock == 0
        ).count()
        
        low_stock = InventoryItem.query.filter(
            InventoryItem.is_active == True,
            InventoryItem.current_stock <= InventoryItem.min_stock_threshold,
            InventoryItem.current_stock > 0
        ).count()
        
        overstock = InventoryItem.query.filter(
            InventoryItem.is_active == True,
            InventoryItem.current_stock >= InventoryItem.max_stock_threshold
        ).count()
        
        # Calculer le score (0-100)
        problems = out_of_stock * 3 + low_stock * 2 + overstock * 1  # Pondération des problèmes
        max_problems = total_items * 3  # Score maximum de problèmes
        
        score = max(0, 100 - (problems / max_problems * 100)) if max_problems > 0 else 100
        
        # Déterminer le statut
        if score >= 90:
            status = 'Excellent'
        elif score >= 75:
            status = 'Bon'
        elif score >= 60:
            status = 'Moyen'
        elif score >= 40:
            status = 'Préoccupant'
        else:
            status = 'Critique'
        
        return {
            'score': round(score, 1),
            'status': status,
            'total_items': total_items,
            'out_of_stock': out_of_stock,
            'low_stock': low_stock,
            'overstock': overstock,
            'healthy_items': total_items - out_of_stock - low_stock - overstock
        }
    
    def configure_alert_recipients(self, email_recipients: List[str], sms_recipients: List[str]):
        """
        Configurer les destinataires des alertes
        """
        self.alert_recipients['email'] = email_recipients
        self.alert_recipients['sms'] = sms_recipients
        
        return {
            'message': 'Destinataires d\'alertes mis à jour',
            'email_recipients': email_recipients,
            'sms_recipients': sms_recipients
        }

