"""Composite Flipkart Robot library — combines all screen action mixins."""

from flipkart.base import FlipkartBase
from flipkart.cart import FlipkartCartActions
from flipkart.home import FlipkartHomeActions
from flipkart.pricing import FlipkartPricingActions
from flipkart.product import FlipkartProductActions
from flipkart.search import FlipkartSearchActions


class FlipkartActions(
    FlipkartBase,
    FlipkartHomeActions,
    FlipkartSearchActions,
    FlipkartPricingActions,
    FlipkartProductActions,
    FlipkartCartActions,
):
    """Single Robot library entry point used by Screen page objects."""

    ROBOT_LIBRARY_SCOPE = "GLOBAL"
