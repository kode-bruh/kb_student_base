from odoo import api, models, fields, exceptions, _

class ApplicationStage(models.Model):
	_name = "kb.application.stage"
	_description = _("Application Stages")
	_order = "sequence asc"
	
	name = fields.Char(required=True)
	is_acceptance_stage = fields.Boolean(help=_("If ticked, a student record can be created when application is in this stage."))
	sequence = fields.Integer(default=1, help=_("Used to order stages. Lower is better."))
	require_document = fields.Boolean(copy=False)
	template_ids = fields.Many2many("kb.application.document.template", string="Document Templates")
	company_id = fields.Many2one("res.company", ondelete="cascade", default=lambda self: self.env.company)
	fallback_stage_id = fields.Many2one("kb.application.stage", ondelete="set null", domain="[('sequence', '<', sequence)]", help=_("When the current stage is deleted, all student application of the current stage will be set to fallback stage automatically."))

	_sql_constraints = [("unique_name", "UNIQUE(name)", _("Name must be unique for each stage. Duplicate detected"))]

	def unlink(self):
		for rec in self:
			# Control applications stage when this stage is deleted
			applications = self.env['kb.application'].search([('stage_id', '=', rec.id)])
			if rec.fallback_stage_id:
				applications.write({
					'stage_id': rec.fallback_stage_id.id	
				})
			else:
				initial_stage = self.search([('id', '!=', rec.id)], limit=1, order="sequence asc")
				if initial_stage:
					applications.write({
						'stage_id': initial_stage.id
					})
				else:
					raise exceptions.ValidationError(_("There is no other application stage to revert existing applications to. Please set the fallback stage for this stage or create another stage."))
		return super(ApplicationStage, self).unlink()