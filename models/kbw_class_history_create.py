from odoo import api, models, fields, exceptions, _, Command

class ClassHistoryCreate(models.Model):
	_name = "kbw.class.history.create"
	_inherit = "mail.thread"
	_description = _("Student Class Management")
	_order = "id desc"

	def _default_student_ids(self):
		selected_ids = self._context.get('active_model') == 'kb.student' and self._context.get('active_ids') or []
		return [
			Command.create({
				'student_id': selected_id, 
			}) for selected_id in selected_ids
		]

	name = fields.Char(string=_("Reference"), default=_("Draft"), readonly=True, copy=False)
	line_ids = fields.One2many("kbw.class.history.create.line", "bulk_id", default=_default_student_ids)
	state = fields.Selection([
		("draft", "Draft"),
		("to_approve", "Pending Approval"), # Only accessible if double validation is active
		("done", "Done")
	], default="draft")

	@api.model_create_multi
	def create(self, vals_list):
		for values in vals_list:
			values['name'] = self.env['ir.sequence'].sudo().next_by_code('%s.sequence' % self._name)
		return super(ClassHistoryCreate, self).create(vals_list)

	"""
		This function will also set the state to 'done' indicating approval.
	"""
	def _create_student_class(self):
		for rec in self:
			for line in rec.line_ids:
				linked_history_id = self.env['kb.class.history'].create({
					'student_id': line.student_id.id,
					'class_id': line.next_class_id.id,
					'term_id': line.next_term_id.id if line.next_term_id else False,
				}).id
			rec.write({
				'state': 'done'
			})

	def validate_class(self):
		for rec in self:
			double_validation = self.env['ir.config_parameter'].sudo().get_param('kb_student_base.double_validation_student_class')

			if double_validation:
				rec.write({
					'state': 'to_approve'
				})
			else:
				rec._create_student_class()

			if self._context.get('active_model') == 'kb.student':
				return {
					'type': 'ir.actions.act_window',
					'res_model': self._model,
					'res_id': rec.id,
					'view_mode': 'form',
					'target': 'new',
				}

	def approve_class(self):
		for rec in self:
			rec._create_student_class()

			if self._context.get('active_model') == 'kb.student':
				return {
					'type': 'ir.actions.act_window',
					'res_model': self._model,
					'res_id': rec.id,
					'view_mode': 'form',
					'target': 'new',
				}


class ClassHistoryCreateLine(models.Model):
	_name = "kbw.class.history.create.line"
	_description = _("Student Class Management Line")
	_rec_name = "student_id"

	bulk_id = fields.Many2one("kbw.class.history.create", ondelete="cascade")
	student_id = fields.Many2one("kb.student", ondelete="cascade", required=True)
	school_id = fields.Many2one("kb.school", compute="_compute_initial_student_class", store=True)
	current_class = fields.Char(compute="_compute_initial_student_class", store=True)
	sequence = fields.Integer(compute="_compute_initial_student_class", store=True)
	next_class_id = fields.Many2one("kb.class", ondelete="cascade", required=True, domain="[('sequence', '>', sequence), ('school_id', '=', school_id)]")
	next_term_id = fields.Many2one("kb.term", ondelete="set null")
	linked_history_id = fields.Many2one("kb.class.history", ondelete="set null", readonly=True, copy=False)

	@api.depends("student_id")
	def _compute_initial_student_class(self):
		for rec in self:
			if rec.student_id:
				rec.school_id = rec.student_id.school_id.id
				last_class_history = sorted(rec.student_id.class_ids, key=lambda history: history.class_id.sequence, reverse=True)[0] if rec.student_id.class_ids else False

				if last_class_history:
					if last_class_history.term_id:
						rec.current_class = "%s (%s)" % (last_class_history.class_id.name, last_class_history.term_id.name)
					else:
						rec.current_class = "%s" % last_class_history.class_id.name
					rec.sequence = last_class_history.sequence
				else:
					rec.current_class = "N/A"
					rec.sequence = 0
			else:
				rec.school_id = False
				rec.current_class = "N/A"
				rec.sequence = 0