# -*- coding: utf-8 -*-
from odoo import api, models, fields
from odoo.exceptions import Warning as UserError
from odoo.tools.translate import _
import odoo.addons.decimal_precision as dp


class SaleLayoutCategory(models.Model):
    _inherit = "sale.layout_category"

    discount_ref = fields.Char(string='Use for invoices discount')
    
    
                            
class ProductTemplate(models.Model):
    _inherit = "product.template"

    is_discount = fields.Boolean(string='Is discount')

class AccountInvoice(models.Model):
    _inherit = "account.invoice"
    
    @api.model
    def create(self, vals):
        ret = super(AccountInvoice, self).create(vals)
        #ret._compute_discounts()
        return ret
 
    @api.multi
    def write(self, vals):
        ret = super(AccountInvoice, self).write(vals) 
        #self._compute_discounts()        
        return ret

    @api.one
    @api.depends('invoice_line_ids.price_subtotal', 'tax_line_ids.amount', 'currency_id', 'company_id', 'date_invoice', 'type')
    def _compute_amount(self):
        disc = 0.0
        total_ht = 0.0
        for order in self:
            for line in order.invoice_line_ids:
                    if not line.product_id.is_discount:
                        total_ht += line.price_subtotal
                    else:
                        disc += line.price_subtotal
        self.amount_discount = disc
        self.amount_befor_discount = total_ht #self.amount_untaxed+self.amount_discount        
        round_curr = self.currency_id.round
        self.amount_untaxed = sum(line.price_subtotal for line in self.invoice_line_ids)
        self.amount_tax = sum(round_curr(line.amount) for line in self.tax_line_ids)
        self.amount_total = self.amount_untaxed + self.amount_tax
        amount_total_company_signed = self.amount_total
        amount_untaxed_signed = self.amount_untaxed
        if self.currency_id and self.company_id and self.currency_id != self.company_id.currency_id:
            currency_id = self.currency_id.with_context(date=self.date_invoice)
            amount_total_company_signed = currency_id.compute(self.amount_total, self.company_id.currency_id)
            amount_untaxed_signed = currency_id.compute(self.amount_untaxed, self.company_id.currency_id)
        sign = self.type in ['in_refund', 'out_refund'] and -1 or 1
        self.amount_total_company_signed = amount_total_company_signed * sign
        self.amount_total_signed = self.amount_total * sign
        self.amount_untaxed_signed = amount_untaxed_signed * sign  
    
    amount_befor_discount = fields.Float(string="Amount Before Discount",  required=False,compute='_compute_amount' )
    amount_discount = fields.Float(string='Discount', digits=dp.get_precision('Account'), readonly=True, compute='_compute_amount')    
    discount_ids = fields.One2many(comodel_name="sale.order.discount.line", inverse_name="discount_line_id", string="Discounts", required=False, copy=True )

    @api.multi    
    def _compute_discounts(self):
        account_invoice_line_obj = self.env['account.invoice.line']
        layout_obj = self.env['sale.layout_category']
        product_obj = self.env['product.product']
         
        for invoice in self:              
            layout = layout_obj.search([('discount_ref', '=', 'invoice_multiple_discount.product_discount_section')])
            product = product_obj.search([('default_code', '=', 'DISCOUNT'),('is_discount', '=', True)])
             
            #Suppression de tous les rabais existants
            for discount in invoice.invoice_line_ids:
                if discount.product_id.id == product.id:
                    discount.unlink();
                  
            sequence = self._compute_sequence(invoice)
            ttl_amount_undisc = 0.0
            ttl_discount = 0.0
            for discount in invoice.discount_ids:
                if discount:
                    if discount.discount_type == 'amount':
                        disc = 0-discount.discount_rate
                        ttl_amount_undisc = self.compute_discount(1)
                        ttl_discount += disc
                    else:
                        ttl_amount_undisc = self.compute_discount(1)
                        disc = 0-(ttl_amount_undisc * discount.discount_rate ) / 100 
                        ttl_discount += ttl_amount_undisc                        
                    account_invoice_line_obj.create({'invoice_id': invoice.id,
                                             'product_id': product.id,
                                             'layout_category_id': layout.id,
                                             'name': discount.description,
                                             'quantity': 1,
                                             'price_unit': disc,
                                             'account_id': product.property_account_income_id.id,
                                             'invoice_line_tax_ids': [(6,0,[product.taxes_id.id])], 
                                             'sequence': sequence})
                self.amount_befor_discount = self.compute_discount(0)
                self.amount_discount = ttl_discount
        self.compute_taxes() 
                
    def _compute_sequence(self, invoice):
        """
        Returns the max sequence + 1
        Will allow us to place the rounding difference invoice line always at the end 
        """
        account_invoice_line_obj = self.env['account.invoice.line']
        account_invoice_lines = account_invoice_line_obj.search([('invoice_id', '=', invoice.id)])
        sequence = 0
        for invoice_line in account_invoice_lines:
            if invoice_line.sequence > sequence:
                sequence = invoice_line.sequence
                
        return sequence + 1
    
    @api.multi
    def compute_discount(self, discount ):
        for order in self:
            total_ht = 0.0
            if discount:
                for line in order.invoice_line_ids:
                    total_ht += line.price_subtotal                
            else:
                for line in order.invoice_line_ids:
                    if not line.product_id.is_discount:
                        total_ht += line.price_subtotal                 
        return total_ht
     
    @api.multi
    def button_reset_taxes(self):
        self._compute_discounts()
        return True
        
    #@api.onchange('invoice_line_ids', 'discount_ids')
    #def _onchange_invoice_line_ids(self):
        #self._compute_discounts()



class AccountInvoiceDiscointLine(models.Model):
    _name = 'sale.order.discount.line'
    name = fields.Char()
    discount_type = fields.Selection(string="Discount Type", selection=[('percent', 'Percentage'),
            ('amount', 'Amount') ], required=False, )
    discount_rate = fields.Float(string="Discount Rate",  required=False, )
    discount_line_id = fields.Many2one(comodel_name="account.invoice", string="Discount_line", required=False, copy=True )
    description = fields.Text(string="Description", required=False, )
 


