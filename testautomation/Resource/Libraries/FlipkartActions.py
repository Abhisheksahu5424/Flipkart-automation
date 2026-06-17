"""
FlipkartActions - Robot library entry point.

Implementation is split by screen under Resource/Libraries/flipkart/:
  - base.py     shared browser helpers and session state
  - home.py     HomePage actions (login popup)
  - search.py   SearchPage actions (cards, compare, open product)
  - pricing.py  price parsing and cart/listing price keywords
  - product.py  ProductPage actions (add to cart, PDP navigation)
  - cart.py     CartPage actions (qty, remove, empty cart)
"""

from flipkart.actions import FlipkartActions

__all__ = ["FlipkartActions"]
