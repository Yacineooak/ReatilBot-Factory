# RetailBot Factory - Installation Guide

## Structure du Projet

```
retailbot_factory/
├── retailbot-ai-core/src/          # Backend Flask (API)
├── retailbot-dashboard/src/        # Interface Analytics (React)
├── retailbot-builder/src/          # Interface No-Code (React)
├── retailbot-factory-documentation.md
└── retailbot-factory-guide-utilisateur.md
```

## Installation Rapide

### 1. Backend (API Flask)
```bash
cd retailbot-ai-core
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# ou venv\Scripts\activate  # Windows
pip install flask flask-cors sqlalchemy requests
python src/main.py
```
**URL**: http://localhost:5001

### 2. Interface Analytics (React)
```bash
cd retailbot-dashboard
npm install
npm run dev
```
**URL**: http://localhost:5173

### 3. Interface No-Code (React)
```bash
cd retailbot-builder
npm install
npm run dev
```
**URL**: http://localhost:5174

## Fonctionnalités Principales

- 🤖 **IA Conversationnelle** - Chatbot intelligent multilingue
- 🛒 **Récupération Paniers** - Campagnes automatisées
- 💰 **Gestion COD** - Scoring de risque et vérification
- 📊 **Analytics** - Tableaux de bord en temps réel
- 🎨 **Interface No-Code** - Configuration sans programmation
- 🔗 **Intégrations** - Shopify, WhatsApp, WooCommerce

## APIs Principales

- `/api/health` - Statut du système
- `/api/chat` - Interface de conversation
- `/api/analytics/dashboard` - Données analytiques
- `/api/integrations/available` - Intégrations disponibles

## Support

Consultez la documentation complète dans `retailbot-factory-documentation.md`

---
**RetailBot Factory** - Plateforme de chatbots conversationnels pour le e-commerce

