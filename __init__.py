# The COPYRIGHT file at the top level of this repository contains
# the full copyright notices and license terms.

from trytond.pool import Pool
from .product import *

def register():
    Pool.register(
        Product,
        Category,
        Template,
        module='nodux_product_one', type_='model')
