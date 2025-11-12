"""Consumer WebSocket pour le chatbot DYNAMIC."""
from __future__ import annotations

import re
from typing import Any, Dict

from asgiref.sync import sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer

from dynamic_shop.inventory.models import Product
from dynamic_shop.sales.models import Order


class ChatConsumer(AsyncWebsocketConsumer):
    """Chatbot simple basé sur des règles."""

    async def connect(self) -> None:
        await self.accept()
        await self.send_json({"sender": "bot", "message": "Bonjour ! Posez-moi une question sur DYNAMIC."})

    async def receive_json(self, content: Dict[str, Any], **kwargs: Any) -> None:  # type: ignore[override]
        message = content.get("message", "").lower()
        response = await self.handle_message(message)
        await self.send_json({"sender": "bot", "message": response})

    async def handle_message(self, message: str) -> str:
        """Route la question vers la réponse appropriée."""

        if not message:
            return "Je n'ai rien reçu, pouvez-vous reformuler ?"
        if any(greeting in message for greeting in ["bonjour", "salut", "hello"]):
            return "Salut ! Je suis le chatbot DYNAMIC. Demandez-moi un stock ou le statut d'une commande."
        if "horaires" in message:
            return "Nos équipes répondent de 8h à 18h, du lundi au samedi."
        if "livraison" in message:
            return "Livraison express sur Antananarivo en 24h et 72h maximum pour les autres régions."
        if "prix" in message:
            return "Consultez nos tarifs sur le portail partenaires ou contactez sales@dynamic.bo."

        stock_match = re.search(r"stock\s+(?P<sku>[A-Za-z0-9_-]+)", message)
        if stock_match:
            sku = stock_match.group("sku").upper()
            product = await sync_to_async(self.get_product_by_sku)(sku)
            if product:
                return f"Le produit {product.name} dispose de {product.remaining_stock} unités en stock."
            return "Je n'ai pas trouvé ce SKU, vérifiez qu'il est correct."

        order_match = re.search(r"suivi\s+commande\s+(?P<code>[A-Za-z0-9_-]+)", message)
        if order_match:
            code = order_match.group("code").upper()
            status = await sync_to_async(self.get_order_status)(code)
            if status:
                return f"La commande {code} est actuellement '{status}'."
            return "Je n'ai pas trouvé cette commande."

        return "Je n'ai pas compris. Essayez 'stock <SKU>' ou 'suivi commande <CODE>'."

    def get_product_by_sku(self, sku: str) -> Product | None:
        try:
            return Product.objects.get(sku=sku)
        except Product.DoesNotExist:
            return None

    def get_order_status(self, code: str) -> str | None:
        try:
            order = Order.objects.get(code=code)
            return order.get_status_display()
        except Order.DoesNotExist:
            return None
