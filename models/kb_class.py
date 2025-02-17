from odoo import api, models, fields, exceptions, _

class Class(models.Model):
	_name = "kb.class"
	_description = _("Classes")
	_order = "sequence asc"

	name = fields.Char(compute="_compute_class_name", store=True)
	company_id = fields.Many2one("res.company", ondelete="cascade", default=lambda self: self.env.company)
	class_name = fields.Char(required=True)
	class_sub_name = fields.Char()
	sequence = fields.Integer(default=1)
	school_id = fields.Many2one("kb.school", ondelete="cascade", required=True)

	@api.constrains("sequence")
	def _validate_sequence(self):
		for rec in self:
			if rec.sequence <= 0:
				raise exceptions.ValidationError(_("Sequence of a class must be a positive number."))

	@api.depends("class_name", "class_sub_name")
	def _compute_class_name(self):
		for rec in self:
			names = []
			if rec.class_name:
				names.append(rec.class_name)
			if rec.class_sub_name:
				names.append(rec.class_sub_name)
			rec.name = " ".join(names) if names else _("New Class")