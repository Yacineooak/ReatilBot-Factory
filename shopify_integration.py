import requests
import json
from datetime import datetime
from typing import Dict, List, Optional

class ShopifyIntegration:
    """
    Intégration avec l'API Shopify pour RetailBot Factory
    """
    
    def __init__(self, shop_domain: str, access_token: str):
        self.shop_domain = shop_domain
        self.access_token = access_token
        self.base_url = f"https://{shop_domain}.myshopify.com/admin/api/2023-10"
        self.headers = {
            'X-Shopify-Access-Token': access_token,
            'Content-Type': 'application/json'
        }
    
    def test_connection(self) -> Dict:
        """
        Tester la connexion à l'API Shopify
        """
        try:
            response = requests.get(f"{self.base_url}/shop.json", headers=self.headers)
            if response.status_code == 200:
                shop_data = response.json()['shop']
                return {
                    'success': True,
                    'shop_name': shop_data['name'],
                    'domain': shop_data['domain'],
                    'currency': shop_data['currency']
                }
            else:
                return {
                    'success': False,
                    'error': f"Erreur API: {response.status_code}"
                }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_products(self, limit: int = 50) -> List[Dict]:
        """
        Récupérer la liste des produits
        """
        try:
            response = requests.get(
                f"{self.base_url}/products.json",
                headers=self.headers,
                params={'limit': limit}
            )
            
            if response.status_code == 200:
                products = response.json()['products']
                return [
                    {
                        'id': product['id'],
                        'title': product['title'],
                        'handle': product['handle'],
                        'price': product['variants'][0]['price'] if product['variants'] else '0.00',
                        'inventory_quantity': product['variants'][0]['inventory_quantity'] if product['variants'] else 0,
                        'status': product['status'],
                        'created_at': product['created_at']
                    }
                    for product in products
                ]
            else:
                return []
        except Exception as e:
            print(f"Erreur lors de la récupération des produits: {e}")
            return []
    
    def search_products(self, query: str) -> List[Dict]:
        """
        Rechercher des produits par nom
        """
        try:
            response = requests.get(
                f"{self.base_url}/products.json",
                headers=self.headers,
                params={'title': query}
            )
            
            if response.status_code == 200:
                products = response.json()['products']
                return [
                    {
                        'id': product['id'],
                        'title': product['title'],
                        'handle': product['handle'],
                        'price': product['variants'][0]['price'] if product['variants'] else '0.00',
                        'image': product['images'][0]['src'] if product['images'] else None,
                        'url': f"https://{self.shop_domain}.myshopify.com/products/{product['handle']}"
                    }
                    for product in products
                ]
            else:
                return []
        except Exception as e:
            print(f"Erreur lors de la recherche de produits: {e}")
            return []
    
    def get_order(self, order_id: str) -> Optional[Dict]:
        """
        Récupérer les détails d'une commande
        """
        try:
            response = requests.get(
                f"{self.base_url}/orders/{order_id}.json",
                headers=self.headers
            )
            
            if response.status_code == 200:
                order = response.json()['order']
                return {
                    'id': order['id'],
                    'order_number': order['order_number'],
                    'total_price': order['total_price'],
                    'currency': order['currency'],
                    'financial_status': order['financial_status'],
                    'fulfillment_status': order['fulfillment_status'],
                    'created_at': order['created_at'],
                    'customer': {
                        'email': order['customer']['email'] if order['customer'] else None,
                        'first_name': order['customer']['first_name'] if order['customer'] else None,
                        'last_name': order['customer']['last_name'] if order['customer'] else None
                    },
                    'line_items': [
                        {
                            'title': item['title'],
                            'quantity': item['quantity'],
                            'price': item['price']
                        }
                        for item in order['line_items']
                    ]
                }
            else:
                return None
        except Exception as e:
            print(f"Erreur lors de la récupération de la commande: {e}")
            return None
    
    def get_abandoned_checkouts(self) -> List[Dict]:
        """
        Récupérer les paniers abandonnés
        """
        try:
            response = requests.get(
                f"{self.base_url}/checkouts.json",
                headers=self.headers,
                params={'status': 'open'}
            )
            
            if response.status_code == 200:
                checkouts = response.json()['checkouts']
                return [
                    {
                        'id': checkout['id'],
                        'token': checkout['token'],
                        'email': checkout['email'],
                        'total_price': checkout['total_price'],
                        'currency': checkout['currency'],
                        'created_at': checkout['created_at'],
                        'updated_at': checkout['updated_at'],
                        'line_items': [
                            {
                                'title': item['title'],
                                'quantity': item['quantity'],
                                'price': item['price']
                            }
                            for item in checkout['line_items']
                        ]
                    }
                    for checkout in checkouts
                ]
            else:
                return []
        except Exception as e:
            print(f"Erreur lors de la récupération des paniers abandonnés: {e}")
            return []
    
    def create_discount_code(self, code: str, percentage: float, usage_limit: int = 1) -> Dict:
        """
        Créer un code de réduction
        """
        try:
            discount_data = {
                "discount_code": {
                    "code": code,
                    "usage_limit": usage_limit,
                    "value_type": "percentage",
                    "value": f"-{percentage}"
                }
            }
            
            # Note: Cette API nécessite un price_rule_id existant
            # En production, il faudrait d'abord créer une price_rule
            
            return {
                'success': True,
                'code': code,
                'percentage': percentage,
                'message': 'Code de réduction créé (simulation)'
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def update_inventory(self, variant_id: str, quantity: int) -> Dict:
        """
        Mettre à jour l'inventaire d'un produit
        """
        try:
            # D'abord, récupérer l'inventory_item_id
            response = requests.get(
                f"{self.base_url}/variants/{variant_id}.json",
                headers=self.headers
            )
            
            if response.status_code == 200:
                variant = response.json()['variant']
                inventory_item_id = variant['inventory_item_id']
                
                # Mettre à jour l'inventaire
                inventory_data = {
                    "location_id": "primary",  # Utiliser la location principale
                    "inventory_item_id": inventory_item_id,
                    "available": quantity
                }
                
                return {
                    'success': True,
                    'variant_id': variant_id,
                    'new_quantity': quantity,
                    'message': 'Inventaire mis à jour (simulation)'
                }
            else:
                return {
                    'success': False,
                    'error': 'Variant non trouvé'
                }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_customer_by_email(self, email: str) -> Optional[Dict]:
        """
        Récupérer un client par email
        """
        try:
            response = requests.get(
                f"{self.base_url}/customers/search.json",
                headers=self.headers,
                params={'query': f'email:{email}'}
            )
            
            if response.status_code == 200:
                customers = response.json()['customers']
                if customers:
                    customer = customers[0]
                    return {
                        'id': customer['id'],
                        'email': customer['email'],
                        'first_name': customer['first_name'],
                        'last_name': customer['last_name'],
                        'orders_count': customer['orders_count'],
                        'total_spent': customer['total_spent'],
                        'created_at': customer['created_at']
                    }
            return None
        except Exception as e:
            print(f"Erreur lors de la recherche du client: {e}")
            return None

