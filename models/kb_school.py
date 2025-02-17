from odoo import api, models, fields, exceptions, _

class School(models.Model):
	_name = "kb.school"
	_description = _("Schools")

	name = fields.Char(required=True, copy=False)
	company_id = fields.Many2one("res.company", ondelete="cascade", default=lambda self: self.env.company)
	street = fields.Char()
	street2 = fields.Char()
	city = fields.Char()
	state_id = fields.Many2one("res.country.state", ondelete="set null")
	country_id = fields.Many2one("res.country", ondelete="set null", default=lambda self: self.env.company.country_id)
	class_ids = fields.One2many("kb.class", "school_id")

	# Sequencing creation
	student_number_sequence_id = fields.Many2one("ir.sequence", ondelete="set null", readonly=True, copy=False)
	seq_code_prefix = fields.Char()
	seq_number_padding = fields.Integer()
	seq_code_suffix = fields.Char()
	seq_test = fields.Char(compute="_compute_sequence_test")

	_sql_constraints = [("unique_name", "UNIQUE(name)", _("Name must be unique for each school. Duplicate detected"))]

	@api.depends("seq_code_prefix", "seq_code_suffix", "seq_number_padding")
	def _compute_sequence_test(self):
		for rec in self:
			sequence = ""
			if rec.seq_code_prefix:
				sequence += rec.seq_code_prefix
			if rec.seq_number_padding > 0:
				sequence += "1".zfill(rec.seq_number_padding)
			else:
				sequence += "1"
			if rec.seq_code_suffix:
				sequence += rec.seq_code_suffix
			rec.seq_test = sequence

	def apply_numbering_sequence(self):
		for rec in self:
			rec.student_number_sequence_id = self.env['ir.sequence'].sudo().create({
				'name': 'Student Number Format - %s' % rec.name,
				'code': 'student_numbering_%s' % rec.id,
				'prefix': rec.seq_code_prefix,
				'suffix': rec.seq_code_suffix,
				'padding': rec.seq_number_padding,
				'company_id': rec.company_id.id,
			}).id

	def reset_numbering_sequence(self):
		for rec in self:
			rec.student_number_sequence_id.sudo().unlink()