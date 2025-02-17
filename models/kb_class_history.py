from odoo import api, models, fields, exceptions, _

class ClassHistory(models.Model):
	_name = "kb.class.history"
	_description = _("Class History")
	_order = "sequence desc"

	name = fields.Char(compute="_compute_reference", store=True)
	student_id = fields.Many2one("kb.student", ondelete="cascade", required=True)
	class_id = fields.Many2one("kb.class", ondelete="cascade", required=True)
	sequence = fields.Integer(related="class_id.sequence", store=True)
	term_id = fields.Many2one("kb.term", ondelete="restrict")

	@api.depends("student_id", "class_id", "term_id")
	def _compute_reference(self):
		for rec in self:
			if rec.term_id:
				rec.name = "%s (%s %s)" % (rec.student_id.name, rec.class_id.name, rec.term_id.name)
			else:
				rec.name = "%s (%s)" % (rec.student_id.name, rec.class_id.name)