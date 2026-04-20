from odoo import models, fields,api


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    use_self_awb_custom_pack = fields.Boolean(
        string="Use Custom Pack",copy=False,
        help="Enable this to manually set the number of packages."
    )
    self_awb_no_of_packages = fields.Integer(
        string="Number of Packages",default=1,copy=False,
        help="Specify how many packages (and labels) should be generated."
    )
    self_awb_custom_shipping_weight = fields.Float(string="SelfAwb Custom Shipping Weight",copy=False,compute='_compute_self_awb_shipping_custom_weight',readonly=False,store=True)

    @api.depends('move_line_ids.result_package_id', 'move_line_ids.result_package_id.shipping_weight', 'weight_bulk')
    def _compute_self_awb_shipping_custom_weight(self):
        for picking in self:
            # if shipping weight is not assigned => default to calculated product weight
            picking.self_awb_custom_shipping_weight = picking.weight_bulk + sum(
                [pack.shipping_weight or pack.weight for pack in picking.package_ids])