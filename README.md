# DYNAMIC Shop

Plateforme de gestion pour la boisson énergisante **DYNAMIC** : inventaire, ventes, chatbot et API REST.

## 🚀 Démarrage rapide (local)

1. **Créer un environnement virtuel**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # Windows PowerShell : .venv\Scripts\Activate.ps1
   ```
2. **Installer les dépendances**
   ```bash
   pip install -r requirements.txt
   ```
3. **Configurer les variables d'environnement**
   ```bash
   cp .env.example .env
   ```
   Ajustez `DATABASE_URL` pour PostgreSQL si besoin. Par défaut SQLite est utilisé.
4. **Appliquer les migrations**
   ```bash
   python manage.py migrate
   ```
5. **Créer un compte administrateur**
   ```bash
   python manage.py createsuperuser
   ```
6. **Peupler des données de démonstration**
   ```bash
   python manage.py seed_dynamic
   ```
7. **Lancer le serveur**
   ```bash
   python manage.py runserver
   ```

- Admin : http://127.0.0.1:8000/admin/
- Dashboard : http://127.0.0.1:8000/dashboard/
- Swagger : http://127.0.0.1:8000/api/docs/
- Chatbot : http://127.0.0.1:8000/

## 🧪 Tests

```bash
pytest
```

Les tests couvrent les services d'inventaire, la logique de commandes, les endpoints d'API et le consumer Channels.

## 🐳 Docker

```bash
docker-compose up --build
```

Services :
- `web` : Django + Daphne
- `db` : PostgreSQL 15
- `redis` : Broker pour Channels

## 📦 Commandes Makefile

| Commande | Description |
| --- | --- |
| `make install` | Crée l'environnement virtuel et installe les dépendances |
| `make migrate` | Exécute les migrations |
| `make seed` | Lance le script `seed_dynamic` |
| `make runserver` | Démarre le serveur de développement |
| `make test` | Lance la suite de tests |

## 📁 Structure

```
dynamic_shop/
  dynamic_shop/        # Paramètres, ASGI/WSGI, URLs
  core/                # Landing page, dashboard, rapports
  inventory/           # Modèles et services de stock
  sales/               # Clients, commandes, paiements
  chatbot/             # Consumer Channels + widget
  api/                 # Serializers, viewsets, routes DRF
  templates/           # Base HTML partagée
  static/              # Assets partagés (.gitkeep)
  management/commands/ # seed_dynamic
scripts/fetch_assets.sh
```

## 📚 API REST

- Authentification via Session ou Token (`/api/auth/token/`).
- Produits publics en lecture, CRUD restreint aux utilisateurs staff.
- Endpoints métier :
  - `POST /api/orders/{id}/confirm/`
  - `POST /api/orders/{id}/ship/`
  - `POST /api/orders/{id}/cancel/`
  - `POST /api/inventory/receive/`
  - `POST /api/inventory/transfer/`
  - `POST /api/inventory/adjust/`

Consultez `/api/docs/` pour la documentation Swagger et `/api/redoc/` pour Redoc.

## 🎨 Assets

Aucun fichier binaire n'est versionné. Pour illustrer la landing page, exécutez :

```bash
./scripts/fetch_assets.sh
```

Les images seront téléchargées dans `dynamic_shop/static/img/`.

## 🧠 Chatbot

Le chatbot Channels répond aux requêtes :
- salutations (`bonjour`, `salut` …)
- questions sur les horaires, prix, livraison
- `stock <SKU>`
- `suivi commande <CODE>`

Une variable `CHATBOT_PROVIDER` (future) peut être utilisée pour intégrer un moteur externe.

## 🔒 Configuration

- `Jazzmin` personnalise l'admin avec des liens rapides.
- WhiteNoise gère les fichiers statiques en production.
- DRF applique un throttling simple (`1000/day` user, `200/day` anonyme).
- Channels bascule sur Redis si `REDIS_URL` est défini.

## 📝 Notes supplémentaires

- Les imports d'assets se font via `django-import-export` dans l'administration (Produits, Lots, Clients).
- Des échantillons de CSV sont à ajouter manuellement dans `dynamic_shop/core/static/samples/` selon vos besoins.
