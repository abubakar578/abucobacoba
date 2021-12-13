from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from odoo.osv import expression
import re
import logging

_logger = logging.getLogger(__name__)


class EditCrossRef(models.Model):
    _name = 'rvd.edit.cross'

    def _get_last_value(self):
        ctx = self.env.context
        _logger.info("Contex")
        _logger.info(ctx)
        name = 'A'
        return name

    last_name_value = fields.Char("Last Value", default=_get_last_value)
    new_name_value = fields.Char("New Value")