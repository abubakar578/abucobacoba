from odoo import models, fields, api
import logging

_logger = logging.getLogger(__name__)


class ResUsers(models.Model):
    _inherit = 'res.users'

    team_member_ids = fields.Many2many('res.users', 'res_users_2_rel', 'sales_person', string='Members', compute='_get_member')

    def _get_member(self):
        for user in self:
            team_obj = self.env['crm.team']
            users = []
            # Di sini, kita ingin lihat, apakah user ini merupakan team leader?
            # Kalau team leader, ta usah lah dia tengok kanan kiri
            admin = self.env.ref('base.user_admin')
            teams = team_obj.with_user(admin).search([('user_id', '=', user.id)], limit=1)
            if teams:
                member_team = []
                team_childs = team_obj.search([('id', 'child_of', teams.id)])
                for team in team_childs:
                    member_team.append(team.user_id.id)
                    for member in team.member_ids:
                        member_team.append(member.id)
                user.team_member_ids = [(6, 0, member_team)]
            else:
                user.team_member_ids = [(6, 0, user.ids)]
