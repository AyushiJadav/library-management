from odoo import models, fields, api

class ToDo(models.Model):
    _name = 'to.do'
    _description = 'To Do Item'


    name = fields.Char(string='Title', required=True)
    description = fields.Text(string='Description')
    is_done = fields.Boolean(string='Done', default=False)
    due_date = fields.Date(string='Due Date')

    @api.model
    def create(self, vals):
        # Custom logic before creating a To Do item
        return super(ToDo, self).create(vals)

    def mark_as_done(self):
        for record in self:
            record.is_done = True

    def mark_as_not_done(self):
        for record in self:
            record.is_done = False