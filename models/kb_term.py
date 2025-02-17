from odoo import api, models, fields, exceptions, _

YEARS = [
	("2020", "2020"),
	("2021", "2021"),
	("2022", "2022"),
	("2023", "2023"),
	("2024", "2024"),
	("2025", "2025"),
	("2026", "2026"),
	("2027", "2027"),
	("2028", "2028"),
	("2029", "2029"),
	("2030", "2030"),
	("2031", "2031"),
	("2032", "2032"),
	("2033", "2033"),
	("2034", "2034"),
	("2035", "2035"),
	("2036", "2036"),
	("2037", "2037"),
	("2038", "2038"),
	("2039", "2039"),
	("2040", "2040"),
]

class Term(models.Model):
	_name = "kb.term"
	_description = _("Study Term")
	_order = "start_year desc"

	name = fields.Char(compute="_compute_reference", store=True)
	company_id = fields.Many2one("res.company", ondelete="cascade", default=lambda self: self.env.company)
	start_year = fields.Selection(YEARS, required=True)
	end_year = fields.Selection(YEARS, required=True)

	@api.depends("start_year", "end_year")
	def _compute_reference(self):
		for rec in self:
			if rec.start_year and rec.end_year:
				rec.name = "%s - %s" % (rec.start_year, rec.end_year)
			else:
				rec.name = _("New")