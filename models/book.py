from odoo import models, fields, api

class Book(models.Model):
    _name = 'lib.book'
    _description = 'Library Books'

    name = fields.Char("Name")
    author = fields.Char(string = 'Author')
    isbn = fields.Char(string = 'ISBN')
    pages = fields.Integer(string = 'Pages')
    published_date = fields.Date(string = 'Published Date')
    