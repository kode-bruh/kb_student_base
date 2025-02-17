from odoo import api, models, fields, exceptions, _

class DocumentType(models.Model):
	_name = "kb.document.type"
	_description = _("Document Types")

	name = fields.Char(required=True, copy=False)
	code = fields.Char(required=True, copy=False)
	company_id = fields.Many2one("res.company", ondelete="cascade", default=lambda self: self.env.company)

	@api.model_create_multi
	def create(self, vals_list):
		for values in vals_list:
			values['code'] = values['code'].upper().replace(' ', '')
			values['name'] = values['name'].title()
		return super(DocumentType, self).create(vals_list)

	def write(self, values):
		if 'code' in values:
			values['code'] = values['code'].upper().replace(' ', '')
		if 'name' in values:
			values['name'] = values['name'].title()
		return super(DocumentType, self).write(values)

	_sql_constraints = [
		('unique_name_company', 'UNIQUE(name, company)', _("Name must be unique.")),
		('unique_code_company', 'UNIQUE(code, company)', _("Code must be unique."))
	]