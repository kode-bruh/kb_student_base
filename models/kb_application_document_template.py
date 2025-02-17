from odoo import api, models, fields, exceptions, _

class ApplicationDocumentTemplate(models.Model):
	_name = "kb.application.document.template"
	_description = _("Application Document Template")

	def _get_default_name(self):
		existing_template = self.search_count([])
		return "Document Template %s" % (str(existing_template + 1).zfill(2))

	active = fields.Boolean(default=True)
	name = fields.Char(default=_get_default_name, required=True)
	company_id = fields.Many2one("res.company", ondelete="cascade", default=lambda self: self.env.company)
	document_ids = fields.One2many("kb.application.document.template.line", "template_id")

class ApplicationDocumentTemplateLine(models.Model):
	_name = "kb.application.document.template.line"
	_description = _("Application Document Template Line")
	_rec_name = "type_id"

	template_id = fields.Many2one("kb.application.document.template", ondelete="cascade", required=True)
	type_id = fields.Many2one("kb.document.type", ondelete="restrict", required=True)
	description = fields.Char(string="Description", required=True)