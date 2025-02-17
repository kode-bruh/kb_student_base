from odoo import api, fields, models

class ResConfigSettings(models.TransientModel):
	_inherit = 'res.config.settings'
	
	# Application settings
	group_application_document = fields.Boolean(string="Application Document", group='base.group_user', implied_group='kb_student_base.group_application_document')
	application_document_active = fields.Boolean(config_parameter="kb_student_base.application_document_active")

	def view_document_template(self):
		return {
			'type': 'ir.actions.act_window',
			'name': 'Document Templates',
			'res_model': 'kb.application.document.template',
			'view_mode': 'list,form',
			'target': 'current'
		}

	def view_document_type(self):
		return {
			'type': 'ir.actions.act_window',
			'name': 'Document Types',
			'res_model': 'kb.document.type',
			'view_mode': 'list,form',
			'target': 'current'
		}

	@api.onchange("group_application_document")
	def _set_application_document(self):
		self.application_document_active = self.group_application_document

	# Class History Bulk settings
	double_validation_student_class = fields.Boolean(config_parameter="kb_student_base.double_validation_student_class")