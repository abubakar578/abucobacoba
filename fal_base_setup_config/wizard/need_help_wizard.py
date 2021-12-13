from odoo import models, api, fields, _


class CluedooHelp(models.TransientModel):
    _name = "cluedoo.help.wizard"
    _description = "Cluedoo Help and Support Request"

    company_name = fields.Char(
        'Company Name',
        default=lambda self: self.env.company.name, help="Company Name/Requestor")
    email_from = fields.Char(
        'Email',
        help="Email address of the contact",
        default=lambda self: self.env.company.email)
    email_to = fields.Char(
        'Email To',
        default='sales@falinwa.com')
    phone = fields.Char('Phone')
    address = fields.Char('Addrress')

    def button_send(self):
        context = dict(self._context)
        mail_body = _("""
            <b>CLuedoo Support Request</b>
            <p>Module Name: %s</p>
            <p>Technical Name: %s</p>
            <br/>
            <b>Company Information</b>
            <p>Company Name: %s</p>
            <p>Phone: %s</p>
            <p>Address: %s</p>
            """) % (context.get('module_name', ''), context.get('technical_name', ''), self.company_name, (self.phone or ''), (self.address or ''))
        mail = self.env['mail.mail'].create({
            'subject': _('CLuedoo Support Request'),
            'email_from': self.email_from,
            'email_to': self.email_to,
            'body_html': mail_body,
        })
        mail.send()
        # raise EnvironmentError
