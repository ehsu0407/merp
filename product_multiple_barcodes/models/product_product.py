# Copyright 2019 VentorTech OU
# Part of Ventor modules. See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api, _
from odoo.osv import expression
from odoo.exceptions import UserError


class ProductProduct(models.Model):
    _inherit = 'product.product'

    barcode_ids = fields.One2many(
        'product.barcode.multi',
        'product_id',
        string='Additional Barcodes',
    )

    # THIS IS OVERRIDE SQL CONSTRAINTS.
    _sql_constraints = [
        ('barcode_uniq', 'check(1=1)', 'No error')
    ]

    @api.model
    def _name_search(self, name, args=None, operator='ilike', limit=100, name_get_uid=None):
        res = super(ProductProduct, self)._name_search(
            name, args=args, operator=operator, limit=limit, name_get_uid=name_get_uid
        )

        if not name:
            return res

        args = args or []
        domain = [('barcode_ids', '=', name)]
        product_id = self._search(domain + args, limit=limit, access_rights_uid=name_get_uid)
        new_res = models.lazy_name_get(self.browse(product_id).with_user(name_get_uid))
        res.extend(new_res)

        return res

    @api.constrains('barcode', 'barcode_ids', 'active')
    def _check_unique_barcode(self):
        for product in self:
            barcode_names = []
            if product.barcode_ids:
                barcode_names = product.mapped('barcode_ids.name')
            if product.barcode:
                barcode_names.append(product.barcode)
            if not barcode_names:
                continue
            products = self.env['product.product'].search([
                ('barcode', 'in', barcode_names), ('id', '!=', product.id)
            ], limit=1)
            barcode_ids = self.env['product.barcode.multi'].search([
                ('name', 'in', barcode_names), ('product_id', '!=', product.id)
            ], limit=1)
            if products or barcode_ids or len(barcode_names) != len(set(barcode_names)):
                raise UserError(
                    _('The following barcode(s) were found in other active products: {0}.'
                      '\nNote that product barcodes should not repeat themselves both in '
                      '"Barcode" field and "Additional Barcodes" field.').format(
                            ", ".join(barcode_names)
                      )
                )
