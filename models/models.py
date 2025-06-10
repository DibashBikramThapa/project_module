# -*- coding: utf-8 -*-

from odoo import api, Command, fields, models, tools, SUPERUSER_ID, _, _lt
from pytz import UTC
from datetime import timedelta, datetime, time


class Task(models.Model):
    _inherit = "project.task"

    date_start = fields.Datetime(string="Initial Start Date")

    def _compute_display(self):
        current_date = datetime.now()
        tasks_to_update = self.env['project.task'].search([
            ('date_deadline', '!=', False),
            ('date_deadline', '<=', current_date),
            ('parent_id', '=', False),
        ])
        if tasks_to_update:
            tasks_to_update.write({'display_in_project': True})
            for each in tasks_to_update:
                each.set_display_in_project()
        return {
            'name': 'My Tasks',
            'type': 'ir.actions.act_window',
            'res_model': 'project.task',
            'view_mode': 'tree,kanban,form,activity,calendar,pivot,graph',
            'domain': [('display_in_project', '=', True)],
            'context': {'search_default_open_tasks': 1, 'default_user_ids': [(4, self.env.user.id)]},
        }

    def set_display_in_project(self, parent_delta=timedelta(seconds=0)):
        for each in self:
            if each.child_ids:
                for child in each.child_ids:
                    if child.date_deadline and child.date_start:
                        delta = child.date_deadline - child.date_start
                        parent_deadline = each.date_deadline
                        to_update= {'date_deadline': child.date_start + parent_delta + delta}
                        child.update(to_update)
                        if parent_deadline >=child.date_deadline or parent_deadline <= datetime.now():
                            child.update({'display_in_project': True})
                        else:
                            child.update({'display_in_project': False})
                        if child.child_ids:
                            child.set_display_in_project(parent_delta)
            elif each.parent_id and each.date_deadline and each.parent_id.date_deadline and each.parent_id.date_deadline >=each.date_deadline:
                each.update({'display_in_project': True})
            else:
                each.update({'display_in_project': False})

    def write(self, vals):
        parent_delta = False
        if vals.get('date_deadline'):
            if isinstance(vals['date_deadline'], datetime):
                new_deadline = vals['date_deadline']
            else:
                new_deadline = datetime.strptime(vals.get('date_deadline'), '%Y-%m-%d %H:%M:%S')
            parent_delta = new_deadline - self.date_deadline
        res = super().write(vals)
        if parent_delta:
            self.set_display_in_project(parent_delta)
        return res