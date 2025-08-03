from src.models.base import db
from datetime import datetime
from enum import Enum



class CartStatus(Enum):
    ACTIVE = "active"
    ABANDONED = "abandoned"
    RECOVERED = "recovered"
    CONVERTED = "converted"

class OrderStatus(Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"
    RETURNED = "returned"

class CODRiskLevel(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERY_HIGH = "very_high"

class NotificationStatus(Enum):
    PENDING = "pending"
    SENT = "sent"
    DELIVERED = "delivered"
    FAILED = "failed"

class AbandonedCart(db.Model):
    __tablename__ = 'abandoned_carts'
    
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.String(255), nullable=False)
    user_id = db.Column(db.String(255), nullable=True)
    email = db.Column(db.String(255), nullable=True)
    phone = db.Column(db.String(20), nullable=True)
    cart_value = db.Column(db.Float, nullable=False, default=0.0)
    currency = db.Column(db.String(3), nullable=False, default='DZD')
    items_count = db.Column(db.Integer, nullable=False, default=0)
    status = db.Column(db.Enum(CartStatus), nullable=False, default=CartStatus.ABANDONED)
    abandoned_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    last_activity = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    recovery_attempts = db.Column(db.Integer, nullable=False, default=0)
    recovered_at = db.Column(db.DateTime, nullable=True)
    conversion_value = db.Column(db.Float, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relations
    items = db.relationship('AbandonedCartItem', backref='cart', lazy=True, cascade='all, delete-orphan')
    notifications = db.relationship('CartRecoveryNotification', backref='cart', lazy=True, cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'id': self.id,
            'session_id': self.session_id,
            'user_id': self.user_id,
            'email': self.email,
            'phone': self.phone,
            'cart_value': self.cart_value,
            'currency': self.currency,
            'items_count': self.items_count,
            'status': self.status.value,
            'abandoned_at': self.abandoned_at.isoformat(),
            'last_activity': self.last_activity.isoformat(),
            'recovery_attempts': self.recovery_attempts,
            'recovered_at': self.recovered_at.isoformat() if self.recovered_at else None,
            'conversion_value': self.conversion_value,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'items': [item.to_dict() for item in self.items]
        }

class AbandonedCartItem(db.Model):
    __tablename__ = 'abandoned_cart_items'
    
    id = db.Column(db.Integer, primary_key=True)
    cart_id = db.Column(db.Integer, db.ForeignKey('abandoned_carts.id'), nullable=False)
    product_id = db.Column(db.String(255), nullable=False)
    product_name = db.Column(db.String(255), nullable=False)
    product_price = db.Column(db.Float, nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=1)
    variant_id = db.Column(db.String(255), nullable=True)
    variant_name = db.Column(db.String(255), nullable=True)
    image_url = db.Column(db.String(500), nullable=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'cart_id': self.cart_id,
            'product_id': self.product_id,
            'product_name': self.product_name,
            'product_price': self.product_price,
            'quantity': self.quantity,
            'variant_id': self.variant_id,
            'variant_name': self.variant_name,
            'image_url': self.image_url
        }

class CartRecoveryNotification(db.Model):
    __tablename__ = 'cart_recovery_notifications'
    
    id = db.Column(db.Integer, primary_key=True)
    cart_id = db.Column(db.Integer, db.ForeignKey('abandoned_carts.id'), nullable=False)
    channel = db.Column(db.String(50), nullable=False)  # 'email', 'sms', 'whatsapp'
    recipient = db.Column(db.String(255), nullable=False)
    subject = db.Column(db.String(255), nullable=True)
    message = db.Column(db.Text, nullable=False)
    status = db.Column(db.Enum(NotificationStatus), nullable=False, default=NotificationStatus.PENDING)
    sent_at = db.Column(db.DateTime, nullable=True)
    delivered_at = db.Column(db.DateTime, nullable=True)
    clicked_at = db.Column(db.DateTime, nullable=True)
    error_message = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'cart_id': self.cart_id,
            'channel': self.channel,
            'recipient': self.recipient,
            'subject': self.subject,
            'message': self.message,
            'status': self.status.value,
            'sent_at': self.sent_at.isoformat() if self.sent_at else None,
            'delivered_at': self.delivered_at.isoformat() if self.delivered_at else None,
            'clicked_at': self.clicked_at.isoformat() if self.clicked_at else None,
            'error_message': self.error_message,
            'created_at': self.created_at.isoformat()
        }

class CODOrder(db.Model):
    __tablename__ = 'cod_orders'
    
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.String(255), nullable=False, unique=True)
    customer_name = db.Column(db.String(255), nullable=False)
    customer_phone = db.Column(db.String(20), nullable=False)
    customer_email = db.Column(db.String(255), nullable=True)
    delivery_address = db.Column(db.Text, nullable=False)
    city = db.Column(db.String(100), nullable=False)
    postal_code = db.Column(db.String(20), nullable=True)
    order_value = db.Column(db.Float, nullable=False)
    currency = db.Column(db.String(3), nullable=False, default='DZD')
    risk_score = db.Column(db.Float, nullable=False, default=0.0)
    risk_level = db.Column(db.Enum(CODRiskLevel), nullable=False, default=CODRiskLevel.LOW)
    risk_factors = db.Column(db.JSON, nullable=True)
    verification_required = db.Column(db.Boolean, nullable=False, default=False)
    verification_status = db.Column(db.String(50), nullable=False, default='pending')
    verification_attempts = db.Column(db.Integer, nullable=False, default=0)
    verified_at = db.Column(db.DateTime, nullable=True)
    status = db.Column(db.Enum(OrderStatus), nullable=False, default=OrderStatus.PENDING)
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'order_id': self.order_id,
            'customer_name': self.customer_name,
            'customer_phone': self.customer_phone,
            'customer_email': self.customer_email,
            'delivery_address': self.delivery_address,
            'city': self.city,
            'postal_code': self.postal_code,
            'order_value': self.order_value,
            'currency': self.currency,
            'risk_score': self.risk_score,
            'risk_level': self.risk_level.value,
            'risk_factors': self.risk_factors,
            'verification_required': self.verification_required,
            'verification_status': self.verification_status,
            'verification_attempts': self.verification_attempts,
            'verified_at': self.verified_at.isoformat() if self.verified_at else None,
            'status': self.status.value,
            'notes': self.notes,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }

class InventoryItem(db.Model):
    __tablename__ = 'inventory_items'
    
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.String(255), nullable=False, unique=True)
    product_name = db.Column(db.String(255), nullable=False)
    sku = db.Column(db.String(100), nullable=True)
    category = db.Column(db.String(100), nullable=True)
    brand = db.Column(db.String(100), nullable=True)
    current_stock = db.Column(db.Integer, nullable=False, default=0)
    reserved_stock = db.Column(db.Integer, nullable=False, default=0)
    available_stock = db.Column(db.Integer, nullable=False, default=0)
    min_stock_threshold = db.Column(db.Integer, nullable=False, default=10)
    max_stock_threshold = db.Column(db.Integer, nullable=False, default=1000)
    reorder_point = db.Column(db.Integer, nullable=False, default=20)
    reorder_quantity = db.Column(db.Integer, nullable=False, default=100)
    cost_price = db.Column(db.Float, nullable=True)
    selling_price = db.Column(db.Float, nullable=True)
    supplier_id = db.Column(db.String(255), nullable=True)
    supplier_name = db.Column(db.String(255), nullable=True)
    last_restocked = db.Column(db.DateTime, nullable=True)
    last_sold = db.Column(db.DateTime, nullable=True)
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relations
    alerts = db.relationship('InventoryAlert', backref='item', lazy=True, cascade='all, delete-orphan')
    movements = db.relationship('InventoryMovement', backref='item', lazy=True, cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'id': self.id,
            'product_id': self.product_id,
            'product_name': self.product_name,
            'sku': self.sku,
            'category': self.category,
            'brand': self.brand,
            'current_stock': self.current_stock,
            'reserved_stock': self.reserved_stock,
            'available_stock': self.available_stock,
            'min_stock_threshold': self.min_stock_threshold,
            'max_stock_threshold': self.max_stock_threshold,
            'reorder_point': self.reorder_point,
            'reorder_quantity': self.reorder_quantity,
            'cost_price': self.cost_price,
            'selling_price': self.selling_price,
            'supplier_id': self.supplier_id,
            'supplier_name': self.supplier_name,
            'last_restocked': self.last_restocked.isoformat() if self.last_restocked else None,
            'last_sold': self.last_sold.isoformat() if self.last_sold else None,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }

class InventoryAlert(db.Model):
    __tablename__ = 'inventory_alerts'
    
    id = db.Column(db.Integer, primary_key=True)
    item_id = db.Column(db.Integer, db.ForeignKey('inventory_items.id'), nullable=False)
    alert_type = db.Column(db.String(50), nullable=False)  # 'low_stock', 'out_of_stock', 'overstock'
    message = db.Column(db.Text, nullable=False)
    severity = db.Column(db.String(20), nullable=False, default='medium')  # 'low', 'medium', 'high', 'critical'
    is_resolved = db.Column(db.Boolean, nullable=False, default=False)
    resolved_at = db.Column(db.DateTime, nullable=True)
    notified_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'item_id': self.item_id,
            'alert_type': self.alert_type,
            'message': self.message,
            'severity': self.severity,
            'is_resolved': self.is_resolved,
            'resolved_at': self.resolved_at.isoformat() if self.resolved_at else None,
            'notified_at': self.notified_at.isoformat() if self.notified_at else None,
            'created_at': self.created_at.isoformat()
        }

class InventoryMovement(db.Model):
    __tablename__ = 'inventory_movements'
    
    id = db.Column(db.Integer, primary_key=True)
    item_id = db.Column(db.Integer, db.ForeignKey('inventory_items.id'), nullable=False)
    movement_type = db.Column(db.String(50), nullable=False)  # 'in', 'out', 'adjustment', 'transfer'
    quantity = db.Column(db.Integer, nullable=False)
    reference_id = db.Column(db.String(255), nullable=True)  # Order ID, Transfer ID, etc.
    reference_type = db.Column(db.String(50), nullable=True)  # 'order', 'transfer', 'adjustment'
    reason = db.Column(db.String(255), nullable=True)
    notes = db.Column(db.Text, nullable=True)
    performed_by = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'item_id': self.item_id,
            'movement_type': self.movement_type,
            'quantity': self.quantity,
            'reference_id': self.reference_id,
            'reference_type': self.reference_type,
            'reason': self.reason,
            'notes': self.notes,
            'performed_by': self.performed_by,
            'created_at': self.created_at.isoformat()
        }

