from src.models.base import db
from src.models.conversation import Conversation, Message
from src.models.management import AbandonedCart, AbandonedCartItem, CODOrder, InventoryItem, InventoryAlert
from datetime import datetime, timedelta
import random

def create_sample_data():
    """
    Créer des données d'exemple pour tester le tableau de bord
    """
    try:
        # Supprimer les données existantes
        db.session.query(Message).delete()
        db.session.query(Conversation).delete()
        db.session.query(AbandonedCartItem).delete()
        db.session.query(AbandonedCart).delete()
        db.session.query(CODOrder).delete()
        db.session.query(InventoryAlert).delete()
        db.session.query(InventoryItem).delete()
        
        # Créer des conversations d'exemple
        for i in range(50):
            conversation = Conversation(
                session_id=f"session_{i}",
                user_id=f"user_{i % 20}",
                platform="website",
                status=random.choice(["active", "resolved", "closed"]),
                created_at=datetime.utcnow() - timedelta(days=random.randint(0, 30))
            )
            db.session.add(conversation)
            db.session.flush()
            
            # Ajouter des messages pour chaque conversation
            for j in range(random.randint(2, 8)):
                message = Message(
                    conversation_id=conversation.id,
                    sender_type=random.choice(["user", "bot"]),
                    content=f"Message {j} de la conversation {i}",
                    intent=random.choice(["greeting", "product_search", "order_status", "support", "goodbye"]),
                    timestamp=conversation.created_at + timedelta(minutes=j)
                )
                db.session.add(message)
        
        # Créer des paniers abandonnés d'exemple
        for i in range(30):
            cart = AbandonedCart(
                session_id=f"cart_session_{i}",
                user_id=f"user_{i % 15}" if i % 3 == 0 else None,
                email=f"user{i}@example.com" if i % 2 == 0 else None,
                phone=f"+21355512{i:04d}" if i % 3 == 0 else None,
                cart_value=random.uniform(500, 5000),
                currency="DZD",
                items_count=random.randint(1, 5),
                status=random.choice(["abandoned", "converted", "recovered"]),
                abandoned_at=datetime.utcnow() - timedelta(days=random.randint(0, 30)),
                recovery_attempts=random.randint(0, 3)
            )
            
            if cart.status == "converted":
                cart.recovered_at = cart.abandoned_at + timedelta(hours=random.randint(1, 48))
                cart.conversion_value = cart.cart_value * random.uniform(0.8, 1.0)
            
            db.session.add(cart)
            db.session.flush()
            
            # Ajouter des articles au panier
            for j in range(cart.items_count):
                item = AbandonedCartItem(
                    cart_id=cart.id,
                    product_id=f"product_{random.randint(1, 100)}",
                    product_name=f"Produit {random.randint(1, 100)}",
                    product_price=random.uniform(50, 1000),
                    quantity=random.randint(1, 3)
                )
                db.session.add(item)
        
        # Créer des commandes COD d'exemple
        cities = ["Alger", "Oran", "Constantine", "Annaba", "Blida", "Batna", "Djelfa", "Sétif", "Sidi Bel Abbès", "Biskra"]
        
        for i in range(40):
            order = CODOrder(
                order_id=f"COD_{i:06d}",
                customer_name=f"Client {i}",
                customer_phone=f"+21355512{i:04d}",
                customer_email=f"client{i}@example.com" if i % 3 == 0 else None,
                delivery_address=f"Adresse {i}, Rue {i}",
                city=random.choice(cities),
                postal_code=f"{random.randint(10000, 99999)}",
                order_value=random.uniform(1000, 10000),
                currency="DZD",
                risk_score=random.uniform(0, 100),
                risk_level=random.choice(["low", "medium", "high", "very_high"]),
                verification_required=random.choice([True, False]),
                verification_status=random.choice(["pending", "verified", "failed"]),
                status=random.choice(["pending", "confirmed", "shipped", "delivered", "cancelled"]),
                created_at=datetime.utcnow() - timedelta(days=random.randint(0, 30))
            )
            db.session.add(order)
        
        # Créer des articles d'inventaire d'exemple
        categories = ["Électronique", "Vêtements", "Maison", "Sport", "Beauté", "Livres", "Jouets"]
        
        for i in range(100):
            item = InventoryItem(
                product_id=f"PROD_{i:06d}",
                product_name=f"Produit {i}",
                sku=f"SKU{i:06d}",
                category=random.choice(categories),
                brand=f"Marque {random.randint(1, 20)}",
                current_stock=random.randint(0, 500),
                reserved_stock=random.randint(0, 50),
                min_stock_threshold=random.randint(10, 50),
                max_stock_threshold=random.randint(200, 1000),
                reorder_point=random.randint(20, 100),
                reorder_quantity=random.randint(50, 200),
                cost_price=random.uniform(10, 500),
                selling_price=random.uniform(20, 1000),
                supplier_name=f"Fournisseur {random.randint(1, 10)}",
                last_restocked=datetime.utcnow() - timedelta(days=random.randint(1, 90)) if random.choice([True, False]) else None,
                last_sold=datetime.utcnow() - timedelta(days=random.randint(1, 30)) if random.choice([True, False]) else None
            )
            
            item.available_stock = max(0, item.current_stock - item.reserved_stock)
            db.session.add(item)
            db.session.flush()
            
            # Créer des alertes pour les articles à faible stock
            if item.current_stock <= item.min_stock_threshold:
                alert = InventoryAlert(
                    item_id=item.id,
                    alert_type="low_stock" if item.current_stock > 0 else "out_of_stock",
                    message=f"Stock faible pour {item.product_name}",
                    severity="critical" if item.current_stock == 0 else "high",
                    is_resolved=False
                )
                db.session.add(alert)
        
        db.session.commit()
        print("Données d'exemple créées avec succès!")
        
    except Exception as e:
        db.session.rollback()
        print(f"Erreur lors de la création des données d'exemple: {e}")
        raise e

if __name__ == "__main__":
    from src.main import app
    with app.app_context():
        create_sample_data()

