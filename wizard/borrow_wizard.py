from odoo import fields, models, api
from odoo.exceptions import ValidationError

class Borrow_wizard(models.TransientModel):
    _name = 'borrow.wizard'
    _description = 'Wizard for borrow book'

    book_id = fields.Many2one('lib.book', String = 'Book ID', require = True)
    borrower_id = fields.Many2one('res.partner', String = 'Borrower', require = True)
    due_date = fields.Date(String = 'Due Date', require = True)


    @api.constrains('book_id')
    def _check_book_availability(self):
        for rec in self:
            if rec.book_id.state == 'borrowed':
                raise ValidationError(
                    f'"{rec.book_id.name}" is already borrowed. '
                    'Please choose an available book.'
                )

    def confirm(self):
        self.ensure_one()
        self.book_id.write({
            'state':       'borrowed',
            'borrower_id': self.borrower_id.id,
        })
        return {'type': 'ir.actions.act_window_close'}

