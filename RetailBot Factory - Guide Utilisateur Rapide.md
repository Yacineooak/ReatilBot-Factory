# RetailBot Factory - Guide Utilisateur Rapide

## Démarrage Rapide

### 1. Accès à l'Interface
- Ouvrez votre navigateur et accédez à l'interface no-code : `http://localhost:5174`
- L'interface s'ouvre directement sans authentification pour cette version de démonstration

### 2. Configuration de Base
1. **Onglet Général** :
   - Nom du bot : Choisissez un nom représentatif de votre marque
   - Langue : Sélectionnez français, arabe ou anglais
   - Plateforme : Website, WhatsApp, Messenger ou Telegram

2. **Onglet Apparence** :
   - Choisissez un thème (Moderne, Minimal, Coloré)
   - Personnalisez les couleurs selon votre charte graphique
   - Définissez la position du widget de chat

3. **Onglet Comportement** :
   - Message d'accueil : Première impression de votre bot
   - Message de fallback : Réponse quand le bot ne comprend pas
   - Paramètres avancés : Délais, nombre de messages max

### 3. Activation des Fonctionnalités
- **Paniers Abandonnés** : Récupération automatique des ventes perdues
- **Gestion COD** : Vérification des commandes à la livraison
- **Alertes Inventaire** : Notifications de stock en temps réel
- **Analytics** : Tableaux de bord et rapports détaillés

### 4. Configuration des Intégrations
- **Shopify** : Domaine + Token d'accès
- **WhatsApp Business** : Phone Number ID + Access Token
- **WooCommerce** : URL du site + Clés API
- **Messenger** : Page ID + Access Token

### 5. Test et Déploiement
1. Utilisez l'aperçu en temps réel pour tester votre bot
2. Sauvegardez votre configuration
3. Cliquez sur "Déployer" pour mettre en ligne
4. Récupérez l'URL de votre bot déployé

## Accès aux Modules

### Interface No-Code
- **URL** : http://localhost:5174
- **Fonctionnalité** : Configuration complète sans code

### Tableau de Bord Analytics
- **URL** : http://localhost:5173
- **Fonctionnalité** : Métriques et visualisations en temps réel

### API Backend
- **URL** : http://localhost:5001
- **Endpoints principaux** :
  - `/api/health` - Statut du système
  - `/api/chat` - Interface de conversation
  - `/api/analytics/dashboard` - Données analytiques
  - `/api/integrations/available` - Intégrations disponibles

## Fonctionnalités Clés

### 🤖 IA Conversationnelle
- Compréhension du langage naturel
- Détection d'intentions avancée
- Support multilingue (FR, AR, EN)
- Recommandations de produits intelligentes

### 🛒 Récupération de Paniers
- Détection automatique d'abandon
- Campagnes multi-canal personnalisées
- Codes de réduction dynamiques
- Analytics de performance

### 💰 Gestion COD
- Scoring de risque automatique
- Vérification intelligente des commandes
- Réduction des refus de livraison
- Optimisation des coûts opérationnels

### 📊 Analytics Avancés
- KPIs en temps réel
- Visualisations interactives
- Rapports de performance
- Insights comportementaux

### 🔗 Intégrations Natives
- Shopify, WooCommerce
- WhatsApp Business, Messenger
- APIs REST complètes
- Webhooks bidirectionnels

## Support et Ressources

### Documentation Complète
- Fichier : `retailbot-factory-documentation.md`
- Contenu : Architecture, APIs, déploiement, maintenance

### Fichiers de Configuration
- Sauvegarde automatique des configurations
- Export/Import JSON
- Templates prédéfinis
- Historique des versions

### Logs et Debugging
- Logs serveur : `retailbot-ai-core/server.log`
- Console navigateur pour les erreurs frontend
- Endpoints de test pour validation

---

**Besoin d'aide ?** Consultez la documentation complète ou contactez le support technique.

