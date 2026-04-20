from odoo import models, fields


class PackageDetails(models.Model):
    _inherit = 'stock.package.type'

    package_carrier_type = fields.Selection(selection_add=[("self_awb_provider", "SelfAWB")],
                                            ondelete={'self_awb_provider': 'set default'})
    parcel_type = fields.Selection([("parcel", "parcel"),
                                    ("envelope", "envelope")])
