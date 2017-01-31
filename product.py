#This file is part of Tryton.  The COPYRIGHT file at the top level of
#this repository contains the full copyright notices and license terms.
import datetime

from trytond.pool import Pool, PoolMeta
from trytond.transaction import Transaction
from trytond.model import ModelSQL, fields
from trytond.pyson import Eval, Or
from trytond import backend
from decimal import Decimal
from trytond.config import config

__all__ = ['Product', 'Category', 'Template']
__metaclass__ = PoolMeta

STATES = {
    'readonly': ~Eval('active', True),
    }
DEPENDS = ['active']
DIGITS = int(config.get('digits', 'unit_price_digits', 4))

class Category:
    __name__ = 'product.category'

    taxes_parent = fields.Boolean('Use the Parent\'s Taxes',
        help='Use the taxes defined on the parent category')

    taxes = fields.Selection([
        ('', ''),
        ('iva0','IVA 0%'),
        ('no_iva', 'No aplica impuesto'),
        ('iva12', 'IVA 12%'),
        ('iva14', 'IVA 14%.'),
    ], 'Tax', states={
        'invisible': Eval('taxes_parent', True)
        })

    @classmethod
    def __setup__(cls):
        super(Category, cls).__setup__()
        cls.parent.states['required'] = Or(
            cls.parent.states.get('required', False),
            Eval('taxes_parent', False))
        cls.parent.depends.extend(['taxes_parent'])


class Template:
    __name__ = 'product.template'

    taxes_category = fields.Boolean('Use Category\'s Taxes',
        help='Use the taxes defined on the category')

    taxes = fields.Selection([
        ('iva0','IVA 0%'),
        ('no_iva', 'No aplica impuesto'),
        ('iva12', 'IVA 12%'),
        ('iva14', 'IVA 14%.'),
    ], 'Tax', states={
        'invisible': Eval('taxes_category', True)
        })

    list_price_with_tax = fields.Property(fields.Numeric('List Price With Tax',
            states=STATES, digits=(16, DIGITS), depends=DEPENDS)
            )
    cost_price_with_tax = fields.Property(fields.Numeric('Cost Price With Tax',
            states=STATES, digits=(16, DIGITS), depends=DEPENDS)
            )
    total = fields.Integer('Total Products')

    @classmethod
    def __setup__(cls):
        super(Template, cls).__setup__()
        cls.category.states['required'] = Or(
            cls.category.states.get('required', False),
            Eval('taxes_category', False))
        cls.category.depends.extend(['taxes_category'])

    def get_list_price_with_tax(self):
        if self.list_price:
            impuesto = 'iva0'
            if self.taxes_category and not self.category:
                return None
            if self.taxes_category and self.category:
                impuesto = self.category.taxes
            if self.taxes:
                impuesto = self.taxes
            if impuesto == 'iva0':
                value = Decimal(0.0)
            elif impuesto == 'no_iva':
                value = Decimal(0.0)
            elif impuesto == 'iva12':
                value = Decimal(0.12)
            elif impuesto == 'iva14':
                value = Decimal(0.14)
            else:
                value = Decimal(0.0)
            tax_amount = self.list_price * value
            return self.list_price + tax_amount

    @fields.depends('taxes_category', 'category', 'list_price',
        'taxes')
    def on_change_list_price(self):
        try:
            changes = super(Template, self).on_change_list_price()
        except AttributeError:
            changes = {}
        if self.list_price:
            changes['list_price_with_tax'] = self.get_list_price_with_tax()
        return changes

    def get_list_price(self):
        if self.taxes_category and not self.category:
            return None
        if self.taxes_category and self.category:
            impuesto = self.category.taxes
        if self.taxes:
            impuesto = self.taxes
        if impuesto == 'iva0':
            value = Decimal(1.0)+Decimal(0.0)
        elif impuesto == 'no_iva':
            value = Decimal(1.0)+Decimal(0.0)
        elif impuesto == 'iva12':
            value = Decimal(1.0)+Decimal(0.12)
        elif impuesto == 'iva14':
            value = Decimal(1.0)+Decimal(0.14)
        else:
            value = Decimal(1.0)+Decimal(0.0)
        tax_amount = self.list_price_with_tax / value
        return tax_amount.quantize(Decimal(str(10.0 ** -DIGITS)))

    @fields.depends('taxes_category', 'category', 'list_price_with_tax',
        'taxes')
    def on_change_list_price_with_tax(self):
        changes = {}
        if self.list_price_with_tax:
            changes['list_price'] = self.get_list_price()
        return changes

    def get_cost_price_with_tax(self):
        if self.cost_price:
            impuesto = 'iva0'
            if self.taxes_category and not self.category:
                return None
            if self.taxes_category and self.category:
                impuesto = self.category.taxes
            if self.taxes:
                impuesto = self.taxes
            if impuesto == 'iva0':
                value = Decimal(0.0)
            elif impuesto == 'no_iva':
                value = Decimal(0.0)
            elif impuesto == 'iva12':
                value = Decimal(0.12)
            elif impuesto == 'iva14':
                value = Decimal(0.14)
            else:
                value = Decimal(0.0)
            tax_amount = self.cost_price * value
            return self.cost_price + tax_amount

    @fields.depends('taxes_category', 'category', 'cost_price',
        'taxes')
    def on_change_cost_price(self):
        try:
            changes = super(Template, self).on_change_cost_price()
        except AttributeError:
            changes = {}
        if self.cost_price:
            changes['cost_price_with_tax'] = self.get_cost_price_with_tax()
        return changes

    def get_cost_price(self):
        if self.taxes_category and not self.category:
            return None
        if self.taxes_category and self.category:
            impuesto = self.category.taxes
        if self.taxes:
            impuesto = self.taxes
        if impuesto == 'iva0':
            value = Decimal(1.0)+Decimal(0.0)
        elif impuesto == 'no_iva':
            value = Decimal(1.0)+Decimal(0.0)
        elif impuesto == 'iva12':
            value = Decimal(1.0)+Decimal(0.12)
        elif impuesto == 'iva14':
            value = Decimal(1.0)+Decimal(0.14)
        else:
            value = Decimal(1.0)+Decimal(0.0)
        tax_amount = self.cost_price_with_tax / value
        return tax_amount.quantize(Decimal(str(10.0 ** -DIGITS)))

    @fields.depends('taxes_category', 'category', 'cost_price_with_tax',
        'taxes')
    def on_change_cost_price_with_tax(self):
        changes = {}
        if self.cost_price_with_tax:
            changes['cost_price'] = self.get_cost_price()
        return changes

    @fields.depends('taxes_category', 'category', 'list_price', 'cost_price',
        'taxes')
    def on_change_taxes_category(self):
        try:
            changes = super(Template, self).on_change_taxes_category()
        except AttributeError:
            changes = {}
        if self.list_price:
            changes['list_price_with_tax'] = self.get_list_price_with_tax()
        if self.cost_price:
            changes['cost_price_with_tax'] = self.get_cost_price_with_tax()
        return changes

    @fields.depends('taxes_category', 'list_price', 'cost_price',
        'taxes')
    def on_change_taxes(self):
        try:
            changes = super(Template, self).on_change_taxes_category()
        except AttributeError:
            changes = {}
        if self.list_price:
            changes['list_price_with_tax'] = self.get_list_price_with_tax()
        if self.cost_price:
            changes['cost_price_with_tax'] = self.get_cost_price_with_tax()
        return changes

    @fields.depends('taxes_category', 'category', 'list_price', 'cost_price',
        'taxes')
    def on_change_category(self):
        try:
            changes = super(Template, self).on_change_category()
        except AttributeError:
            changes = {}
        if self.taxes_category:
            changes['list_price_with_tax'] = None
            changes['cost_price_with_tax'] = None
            if self.category:
                changes['list_price_with_tax'] = self.get_list_price_with_tax()
                changes['cost_price_with_tax'] = self.get_cost_price_with_tax()
        return changes

class Product:
    __name__ = 'product.product'

    @staticmethod
    def get_sale_price(products, quantity=0):
        '''
        Return the sale price for products and quantity.
        It uses if exists from the context:
            uom: the unit of measure
            currency: the currency id for the returned price
        '''
        pool = Pool()
        Uom = pool.get('product.uom')
        User = pool.get('res.user')
        Currency = pool.get('currency.currency')
        Date = pool.get('ir.date')

        today = Date.today()
        prices = {}

        uom = None
        if Transaction().context.get('uom'):
            uom = Uom(Transaction().context.get('uom'))

        currency = None
        if Transaction().context.get('currency'):
            currency = Currency(Transaction().context.get('currency'))

        user = User(Transaction().user)

        for product in products:
            prices[product.id] = product.list_price
            if uom:
                prices[product.id] = Uom.compute_price(
                    product.default_uom, prices[product.id], uom)
            if currency and user.company:
                if user.company.currency != currency:
                    date = Transaction().context.get('sale_date') or today
                    with Transaction().set_context(date=date):
                        prices[product.id] = Currency.compute(
                            user.company.currency, prices[product.id],
                            currency, round=False)
        return prices

    def compute_delivery_date(self, date=None):
        '''
        Compute the delivery date a the given date
        '''
        Date = Pool().get('ir.date')

        if not date:
            date = Date.today()
        return date + datetime.timedelta(self.delivery_time)
