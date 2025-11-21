"""Consumer WebSocket pour le chatbot DYNAMIC."""
from __future__ import annotations

import unicodedata
import re
from typing import Any, Dict, Tuple

from asgiref.sync import sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer

from dynamic_shop.inventory.models import Product
from dynamic_shop.sales.models import Order


class ChatConsumer(AsyncWebsocketConsumer):
    """Chatbot simple basé sur des règles."""

    FAQ_RESPONSES: Tuple[Tuple[Tuple[str, ...], str], ...] = (
        (
            (
                "horaire",
                "heure",
                "disponibilite",
                "ouverture",
                "ouvert",
                "ferme",
            ),
            "Nos équipes répondent du lundi au samedi de 8h à 18h (GMT+3).",
        ),
        (
            ("livraison", "delai", "delais", "expedition", "livrer"),
            "Livraison express sur Antananarivo en 24h et jusqu'à 72h pour les autres régions.",
        ),
        (
            ("prix", "tarif", "cout", "facture", "devis"),
            "Consultez nos tarifs sur le portail partenaires ou écrivez-nous sur sales@dynamic.bo pour un devis personnalisé.",
        ),
        (
            ("contact", "support", "assistance", "aide", "help"),
            "Vous pouvez nous joindre via support@dynamic.bo ou WhatsApp +261 34 00 00 000.",
        ),
    )

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

        normalized = self.normalize_message(message)

        if any(greeting in normalized for greeting in ["bonjour", "salut", "hello", "hey"]):
            return "Salut ! Je suis le chatbot DYNAMIC. Demandez-moi un stock ou le statut d'une commande."

        quick_help = self.match_quick_answers(normalized)
        if quick_help:
            return quick_help

        order_code = self.extract_order_code(normalized)
        if order_code:
            status = await sync_to_async(self.get_order_status)(order_code)
            if status:
                return f"La commande {order_code} est actuellement '{status}'."
            return "Je n'ai pas trouvé cette commande. Vérifiez le code ou contactez le support."

        stock_query = self.extract_stock_query(normalized)
        if stock_query:
            product = await sync_to_async(self.get_product_by_query)(stock_query)
            if product:
                return (
                    f"{product.name} (SKU {product.sku}) dispose de {product.remaining_stock} "
                    "unités en stock."
                )
            return "Je n'ai pas trouvé ce produit. Indiquez un SKU ou un nom plus précis."

        return self.help_message()

    @staticmethod
    def normalize_message(message: str) -> str:
        """Abaisse, supprime les accents et espaces superflus."""

        lowered = message.strip().lower()
        normalized = unicodedata.normalize("NFD", lowered)
        return "".join(char for char in normalized if unicodedata.category(char) != "Mn")

    def match_quick_answers(self, normalized: str) -> str | None:
        """Renvoie une réponse FAQ ou aide rapide si applicable."""

        for keywords, answer in self.FAQ_RESPONSES:
            if any(keyword in normalized for keyword in keywords):
                return answer
        if "aide" in normalized or normalized.endswith("?"):
            return self.help_message()
        return None

    @staticmethod
    def extract_stock_query(normalized: str) -> str | None:
        """Retourne le SKU ou un terme produit repéré dans le message."""

        stock_match = re.search(r"stock\s+(?P<query>[A-Za-z0-9_-]{3,})", normalized)
        if stock_match:
            return stock_match.group("query").upper()
        inline_match = re.search(r"(?P<query>[A-Za-z0-9_-]{3,})\s+en\s+stock", normalized)
        if inline_match:
            return inline_match.group("query").upper()
        return None

    @staticmethod
    def extract_order_code(normalized: str) -> str | None:
        """Identifie un code de commande dans les formulations courantes."""

        patterns = [
            r"suivi\s+commande\s+(?P<code>[A-Za-z0-9_-]+)",
            r"statut\s+commande\s+(?P<code>[A-Za-z0-9_-]+)",
            r"ou\s+en\s+est\s+ma\s+commande\s+(?P<code>[A-Za-z0-9_-]+)",
        ]
        for pattern in patterns:
            match = re.search(pattern, normalized)
            if match:
                return match.group("code").upper()
        return None

    @staticmethod
    def help_message() -> str:
        """Message d'aide générique avec les actions possibles."""

        return (
            "Je peux répondre sur le stock et le suivi client :\n"
            "- 'stock <SKU>' ou le nom produit pour vérifier la disponibilité\n"
            "- 'suivi commande <CODE>' pour connaître le statut\n"
            "- horaires, livraison, prix, contact"
        )

    def get_product_by_query(self, query: str) -> Product | None:
        """Recherche un produit par SKU exact ou par nom approximatif."""

        try:
            return Product.objects.get(sku__iexact=query)
        except Product.DoesNotExist:
            return Product.objects.filter(name__icontains=query).first()

    def get_order_status(self, code: str) -> str | None:
        try:
            order = Order.objects.get(code=code)
            return order.get_status_display()
        except Order.DoesNotExist:
            return None
