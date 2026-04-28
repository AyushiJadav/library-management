from odoo import models, fields, api
from odoo.exceptions import ValidationError
#to run this module in terminal -  (venv311) PS D:\odoo18\server> python odoo-bin -u library_mgmt -c d:\odoo18\config\odoo.conf
#to activate venv - & "d:\odoo18\venv311\Scripts\Activate.ps1"
class Book(models.Model):
    _name = 'lib.book'
    _description = 'Library Books'

    name = fields.Char("Name")
    author = fields.Char(string = 'Author')
    isbn = fields.Char(string = 'ISBN')
    pages = fields.Integer(string = 'Pages')
    published_date = fields.Date(string = 'Published Date')
    state = fields.Selection([('available','Available'),
                              ('borrowed','Borrowed'),
                              ('lost','Lost')], 
                              default = 'available', string = 'State')
    borrower_id = fields.Many2one('res.partner', String = 'Borrower')
    is_borrowed = fields.Boolean(String = 'Is Borrowed', compute='_compute_borrowed', store = True)


    """_sql_constraints = [
    (constraint_name,sql_rule,error_message),
    ]"""
    _sql_constraints = [
        ('isbn_unique', 'UNIQUE(isbn)', 'A book with this ISBN already exists.'),
    ]

    @api.depends('state')
    def _compute_borrowed(self):
        for i in self:
            if i.state == "borrowed":
                i.is_borrowed = True
            else:
                i.is_borrowed = False

    @api.constrains('state', 'borrower_id')
    def _check_borrower(self):
        for rec in self:
            if rec.state == 'borrowed' and not rec.borrower_id:
                raise ValidationError(
                    'A borrowed book must have a borrower assigned.'
                )

    def action_open_borrow_wizard(self):
        """Opens the Borrow wizard pre-filled with this book."""
        return {
            'type':      'ir.actions.act_window',
            'name':      'Borrow Book',
            'res_model': 'borrow.wizard',
            'view_mode': 'form',
            'target':    'new',
            'context':   {'default_book_id': self.id},
        }

    def action_return(self):
        for i in self:
            i.state = 'available'
    
    def action_return(self):
        self.write({'state': 'available', 'borrower_id': False})