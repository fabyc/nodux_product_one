import datetime

from trytond.pool import Pool, PoolMeta
from trytond.transaction import Transaction
from trytond.pyson import Eval, Or
from trytond import backend
from decimal import Decimal
from trytond.config import config
from trytond.model import ModelView, ModelSQL, fields, Unique

__all__ = ['Product', 'Category', 'Template']
__metaclass__ = PoolMeta

STATES = {
    'readonly': ~Eval('active', True),
    }
DEPENDS = ['active']

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

    category = fields.Many2One('product.category', 'Category',
        states=STATES, depends=DEPENDS)

    taxes_category = fields.Boolean('Use Category\'s Taxes',
        help='Use the taxes defined on the category')

    taxes = fields.Selection([
        ('', ''),
        ('iva0','IVA 0%'),
        ('no_iva', 'No aplica impuesto'),
        ('iva12', 'IVA 12%'),
        ('iva14', 'IVA 14%.'),
    ], 'Tax', states={
        'invisible': Eval('taxes_category', True)
        })

    list_price_with_tax = fields.Property(fields.Numeric('List Price With Tax',
            states=STATES, digits=(16, 4), depends=DEPENDS)
            )
    cost_price_with_tax = fields.Property(fields.Numeric('Cost Price With Tax',
            states=STATES, digits=(16, 4), depends=DEPENDS)
            )
    total = fields.Property(fields.Numeric('Total Products', digits=(16, 8)))

    code1 = fields.Char('Code')

    code2 = fields.Char('Code')

    @classmethod
    def __setup__(cls):
        super(Template, cls).__setup__()
        t = cls.__table__()
        cls._sql_constraints = [
            ('NAME', Unique(t, t.name),
             'Product already exists.')
        ]
        cls.category.states['required'] = Or(
            cls.category.states.get('required', False),
            Eval('taxes_category', False))
        cls.name.size = 100

    @classmethod
    def delete(cls, templates):
        pool = Pool()
        SaleLine = pool.get('sale.line')
        PurchaseLine = pool.get('purchase.line')
        lines = None
        purchase_lines = None
        for template in templates:
            for product in template.products:
                lines = SaleLine.search([('product', '=', product)])
                purchase_lines = PurchaseLine.search([('product', '=', product)])
                if lines:
                    cls.raise_user_error('No puede eliminar el producto\n%s\nporque tiene asociada una venta' , (template.name))
                if purchase_lines:
                    cls.raise_user_error('No puede eliminar el producto\n%s\nporque tiene asociada una compra', (template.name))
        super(Template, cls).delete(templates)

    @fields.depends('name')
    def on_change_name(self):
        cont = 0
        if self.name:
            name = self.name.strip()
            name = name.replace("\n","")
            self.name = name

    @classmethod
    def search_rec_name(cls, name, clause):
        products = cls.search([
                ('code1',) + tuple(clause[1:]),
                ], limit=1)
        if products:
            return [('code1',) + tuple(clause[1:])]

        products2 = cls.search([
                ('code2',) + tuple(clause[1:]),
                ], limit=1)
        if products2:
            return [('code2',) + tuple(clause[1:])]

        return [('name',) + tuple(clause[1:])]

    @staticmethod
    def default_products():
        return []

    @fields.depends('products')
    def on_change_products(self):
        cont = 0
        for product in self.products:
            cont += 1
            print "Ingresa ", cont
            if cont == 1:
                self.code1 = product.code
            if cont == 2:
                self.code2 = product.code


    @staticmethod
    def default_total():
        return 0

    @staticmethod
    def default_default_uom():
        Uom = Pool().get('product.uom')
        uoms = Uom.search([('symbol', '=', 'u'), ('name', '=', 'Unidad')])
        if len(uoms) >= 1:
            for uom in uoms:
                return uom.id

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
        'taxes', 'list_price_with_tax')
    def on_change_list_price(self):
        try:
            super(Template, self).on_change_list_price()
        except AttributeError:
            pass
        if self.list_price:
            self.list_price_with_tax = self.get_list_price_with_tax()

    def get_list_price(self):
        impuesto = 'iva0'
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
        return tax_amount.quantize(Decimal(str(10.0 ** -4)))

    @fields.depends('taxes_category', 'category', 'list_price_with_tax',
        'taxes', 'list_price')
    def on_change_list_price_with_tax(self):
        if self.list_price_with_tax:
            self.list_price = self.get_list_price()

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
        'taxes', 'cost_price_with_tax')
    def on_change_cost_price(self):
        try:
            super(Template, self).on_change_cost_price()
        except AttributeError:
            pass
        if self.cost_price:
            self.cost_price_with_tax = self.get_cost_price_with_tax()

    def get_cost_price(self):
        impuesto = 'iva0'
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
        return tax_amount.quantize(Decimal(str(10.0 ** -4)))

    @fields.depends('taxes_category', 'category', 'cost_price_with_tax',
        'taxes', 'cost_price')
    def on_change_cost_price_with_tax(self):
        if self.cost_price_with_tax:
            self.cost_price = self.get_cost_price()

    @fields.depends('taxes_category', 'category', 'list_price', 'cost_price',
        'taxes', 'list_price_with_tax', 'cost_price_with_tax')
    def on_change_taxes_category(self):
        try:
            super(Template, self).on_change_taxes_category()
        except AttributeError:
            pass
        if self.list_price:
            self.list_price_with_tax = self.get_list_price_with_tax()
        if self.cost_price:
            self.cost_price_with_tax = self.get_cost_price_with_tax()

    @fields.depends('taxes_category', 'list_price', 'cost_price',
        'taxes', 'list_price_with_tax', 'cost_price_with_tax')
    def on_change_taxes(self):
        try:
            super(Template, self).on_change_taxes_category()
        except AttributeError:
            pass
        if self.list_price:
            self.list_price_with_tax = self.get_list_price_with_tax()
        if self.cost_price:
            self.cost_price_with_tax = self.get_cost_price_with_tax()

    @fields.depends('taxes_category', 'category', 'list_price', 'cost_price',
        'taxes', 'list_price_with_tax', 'cost_price_with_tax','taxes_category')
    def on_change_category(self):
        try:
            super(Template, self).on_change_category()
        except AttributeError:
            pass

        if self.category:
            self.taxes_category = True

        if self.taxes_category:
            self.list_price_with_tax = None
            self.cost_price_with_tax = None
            if self.category:
                self.list_price_with_tax = self.get_list_price_with_tax()
                self.cost_price_with_tax = self.get_cost_price_with_tax()


class Product:
    __name__ = 'product.product'

    @classmethod
    def __setup__(cls):
        super(Product, cls).__setup__()
        cls.code.size = 50

    @fields.depends('code')
    def on_change_code(self):
        cont = 0
        if self.code:
            if self.code != "":
                code = self.code.strip()
                code = code.replace("\n","")
                self.code = code

    @fields.depends('description')
    def on_change_description(self):
        cont = 0
        if self.description:
            description = self.description.strip()
            self.description = description

    @staticmethod
    def get_sale_price(products, quantity=0):
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
            if product:
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

    @staticmethod
    def get_purchase_price(products, quantity=0):
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
            prices[product.id] = product.cost_price
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
