from odoo import api, models, fields, exceptions, _

class StudentDocument(models.Model):
	_name = _("kb.student.document")
	_description = "Student Documents"

	name = fields.Char(compute="_compute_name")
	type_id = fields.Many2one("kb.document.type", ondelete="restrict", required=True, copy=False)
	application_id = fields.Many2one("kb.application", ondelete="set null")
	student_id = fields.Many2one("kb.student", ondelete="set null")
	document = fields.Binary(required=True, copy=False)
	
	# Ownership
	user_id = fields.Many2one("res.users", ondelete="set null", readonly=True, copy=False) # Ideally points to the parent's portal user

	def write(self, values):
		res = super(StudentDocument, self).write(values)
		for rec in self:
			if not rec.application_id and not rec.student_id:
				raise exceptions.ValidationError(_("Document"))
		return res

	@api.depends("application_id", "student_id")
	def _compute_name(self):
		for rec in self:
			if rec.student_id:
				rec.name = "%s %s" % (rec.student_id.name, rec.type_id.name)
			elif rec.application_id:
				rec.name = "%s %s" % (rec.application_id.name, rec.type_id.name)
			else:
				rec.name = "%s %s" % ('Unknown', rec.type_id.name)