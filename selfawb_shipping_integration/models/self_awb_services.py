from odoo import models, fields,api, _


class SelfAWBService(models.Model):
    _name = "self.awb.service"
    _description = ""
    _rec_name = 'service_name'

    service_name = fields.Char(string='Service Name')
    service_description = fields.Char(string='Service Description')

    def name_get(self):
        name_value = []
        for record in self:
            new_value = '%s - %s' % (record.service_name, record.service_description)
            name_value.append((record.id, new_value))
        return name_value