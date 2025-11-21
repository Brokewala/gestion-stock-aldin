from __future__ import annotations

import pytest
from channels.testing import WebsocketCommunicator

from dynamic_shop.dynamic_shop.asgi import application
from dynamic_shop.inventory.models import Product
from dynamic_shop.inventory.services import PurchaseItem, receive_purchase
from dynamic_shop.sales.models import Customer, Order


@pytest.mark.asyncio
@pytest.mark.django_db(transaction=True)
async def test_chatbot_stock_lookup(product: Product, warehouse):
    receive_purchase("Test", [PurchaseItem(product=product, quantity=30, batch_code="BOT1")], warehouse)
    communicator = WebsocketCommunicator(application, "/ws/chat/")
    connected, _ = await communicator.connect()
    assert connected
    await communicator.receive_json_from()
    await communicator.send_json_to({"message": f"stock {product.sku}"})
    response = await communicator.receive_json_from()
    assert "30" in response["message"]
    await communicator.disconnect()


@pytest.mark.asyncio
@pytest.mark.django_db(transaction=True)
async def test_chatbot_order_status(product: Product, warehouse):
    customer = Customer.objects.create(name="Client Chat")
    order = Order.objects.create(code="ORD-TEST-0001", customer=customer, warehouse=warehouse)
    communicator = WebsocketCommunicator(application, "/ws/chat/")
    await communicator.connect()
    await communicator.receive_json_from()
    await communicator.send_json_to({"message": "suivi commande ORD-TEST-0001"})
    response = await communicator.receive_json_from()
    assert "ORD-TEST-0001" in response["message"]
    await communicator.disconnect()


@pytest.mark.asyncio
@pytest.mark.django_db(transaction=True)
async def test_chatbot_stock_lookup_by_name(product: Product, warehouse):
    receive_purchase("Test", [PurchaseItem(product=product, quantity=12, batch_code="BOT2")], warehouse)
    communicator = WebsocketCommunicator(application, "/ws/chat/")
    await communicator.connect()
    await communicator.receive_json_from()
    await communicator.send_json_to({"message": "Quel est le stock produit test ?"})
    response = await communicator.receive_json_from()
    assert "Produit Test" in response["message"]
    assert "12" in response["message"]
    await communicator.disconnect()


@pytest.mark.asyncio
@pytest.mark.django_db(transaction=True)
async def test_chatbot_help_message(product: Product, warehouse):
    communicator = WebsocketCommunicator(application, "/ws/chat/")
    await communicator.connect()
    await communicator.receive_json_from()
    await communicator.send_json_to({"message": "??"})
    response = await communicator.receive_json_from()
    assert "stock <SKU>" in response["message"]
    await communicator.disconnect()
