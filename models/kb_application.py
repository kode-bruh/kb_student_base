from odoo import api, models, fields, exceptions, _

class StudentApplication(models.Model):
	_name = "kb.application"
	_description = _("Student Applications")
	_inherit = ["portal.mixin", "mail.thread", "mail.activity.mixin"]
	_order = "create_date desc"

	name = fields.Char(compute="_compute_full_name", store=True, tracking=True)
	school_id = fields.Many2one("kb.school", ondelete="restrict", required=True, tracking=True)
	student_id = fields.Many2one("kb.student", ondelete="set null")
	company_id = fields.Many2one("res.company", ondelete="cascade", default=lambda self: self.env.company)
	first_name = fields.Char(required=True)
	middle_name = fields.Char()
	last_name = fields.Char()
	image = fields.Binary()

	# Personal information
	birth_date = fields.Date(required=True, tracking=True)
	gender = fields.Selection([
		("Male", _("Male")),
		("Female", _("Female"))
	], required=True, tracking=True)
	blood_type = fields.Selection([
		("a", "A"), 
		("b", "B"), 
		("ab", "AB"), 
		("o", "O"),
		("ros", "Ro Subtype"),
		("rhn", "Rh Null")
	], tracking=True)
	blood_rhesus = fields.Selection([
		("positive", _("Positive")),
		("negative", _("Negative"))
	], tracking=True)
	religion = fields.Selection([
		("protestant", _("Prostestant")),
		("catholic", _("Catholic")),
		("islam", _("Islam")),
		("hindu", _("Hindu")),
		("buddha", _("Buddha")),
		("other", _("Other")),
	], tracking=True)
	nationality_id = fields.Many2one("res.country", ondelete="set null", tracking=True)

	# Parent / guardian information
	father_name = fields.Char(tracking=True)
	father_mobile = fields.Char(tracking=True)
	mother_name = fields.Char(tracking=True)
	mother_mobile = fields.Char(tracking=True)
	has_guardian = fields.Boolean(help=_("Tick this if the child (applicant) does not live with his/her parents due to any reason and is living with a guardian / surrogate parents."), tracking=True)
	guardian_name = fields.Char(tracking=True)
	guardian_mobile = fields.Char(tracking=True)

	# Address information
	street = fields.Char()
	street2 = fields.Char()
	city = fields.Char()
	state_id = fields.Many2one("res.country.state", ondelete="set null")
	country_id = fields.Many2one("res.country", ondelete="set null", default=lambda self: self.env.company.country_id)

	# Workflow
	def _compute_first_stage(self):
		stage_id = self.env['kb.application.stage'].search([], limit=1, order="sequence asc")
		return stage_id.id if stage_id else False

	@api.model
	def _read_group_stage_ids(self, stages, domain):
		return stages.search([('company_id', '=', self.env.company.id)])

	stage_id = fields.Many2one("kb.application.stage", ondelete="set null", default=_compute_first_stage, group_expand='_read_group_stage_ids', tracking=True)
	is_ready = fields.Boolean(compute="_compute_is_ready_to_accept")
	document_ids = fields.One2many("kb.student.document", "application_id")

	# Ownership
	user_id = fields.Many2one("res.users", ondelete="set null", readonly=True, copy=False) # Ideally points to the parent's portal user

	@api.model_create_multi
	def create(self, vals_list):
		records = super(StudentApplication, self).create(vals_list)
		for rec in records:
			rec._portal_ensure_token()
		return records

	def write(self, values):
		for rec in self:
			# Generate documents required for application
			if 'stage_id' in values:
				application_document_activated = self.env['ir.config_parameter'].sudo().get_param('kb_student_base.application_document_active')
				if application_document_activated:
					rec._check_if_documents_received() # Run the check first
					stage = self.env['kb.application.stage'].browse(values['stage_id'])
					if stage and stage.require_document and stage.template_ids:
						rec._populate_document_requirement(stage.template_ids)
		return super(StudentApplication, self).write(values)

	def _check_if_documents_received(self):
		for rec in self:
			for doc in rec.document_ids:
				if not doc.document:
					raise exceptions.ValidationError(_("There are one or more documents that are not yet uploaded."))

	def _populate_document_requirement(self, template_ids):
		for rec in self:
			# Fetch all available documents for this application / student
			if rec.student_id:
				available_documents = self.env['kb.student.document'].search(['|', ('student_id', '=', rec.student_id.id), ('application_id', '=', rec.id)])
			else:
				available_documents = self.env['kb.student.document'].search([('application_id', '=', rec.id)])
			available_document_codes = [document.type_id.code for document in available_documents]

			# Generate the required documents
			for template in template_ids:
				for doc in template.document_ids:
					if doc.type_id.code not in available_document_codes: # This prevents duplicate documents being uploaded
						self.env['kb.student.document'].create({
							'type_id': doc.type_id.id,
							'application_id': rec.id,
						})

	@api.depends("first_name", "middle_name", "last_name")
	def _compute_full_name(self):
		for rec in self:
			names = []
			if rec.first_name:
				names.append(rec.first_name)
			if rec.middle_name:
				names.append(rec.middle_name)
			if rec.last_name:
				names.append(rec.last_name)
			rec.name = " ".join(names) if names else _("New Application")

	@api.depends("stage_id.is_acceptance_stage")
	def _compute_is_ready_to_accept(self):
		for rec in self:
			rec.is_ready = True if rec.stage_id.is_acceptance_stage else False

	def view_documents(self):
		for rec in self:
			return {
				'type': 'ir.actions.act_window',
				'name': _("%s Documents" % rec.name),
				'res_model': 'kb.student.document',
				'view_mode': 'list,form',
				'target': 'current',
				'domain': "[('application_id', '=', %s)]" % rec.id,
			}

	def move_to_prev_stage(self):
		for rec in self:
			prev_stage_id = self.env['kb.application.stage'].search([('sequence', '<', rec.stage_id.sequence)], limit=1, order="sequence desc")
			if not prev_stage_id:
				raise exceptions.UserError(_("This is the first stage of student application. Cannot move to previous stage."))
			else:
				return rec.write({
					'stage_id': prev_stage_id.id
				})

	def move_to_next_stage(self):
		for rec in self:
			next_stage_id = self.env['kb.application.stage'].search([('sequence', '>', rec.stage_id.sequence)], limit=1, order="sequence asc")
			if not next_stage_id:
				raise exceptions.UserError(_("This is the last stage of student application. Cannot move to next stage."))
			else:
				return rec.write({
					'stage_id': next_stage_id.id
				})

	"""
		Create student record based on this application if there aren't any yet. Ideally a new student will not have any `student_id` set.
	"""
	def create_student_record(self):
		for rec in self:
			if rec.is_ready:
				values = {
					'school_id': rec.school_id.id,
					'company_id': rec.company_id.id,
					'first_name': rec.first_name,
					'middle_name': rec.middle_name,
					'last_name': rec.last_name,
					'image': rec.image,
					'birth_date': rec.birth_date,
					'gender': rec.gender,
					'blood_type': rec.blood_type,
					'blood_rhesus': rec.blood_rhesus,
					'religion': rec.religion,
					'nationality_id': rec.nationality_id.id,
					'father_name': rec.father_name,
					'father_mobile': rec.father_mobile,
					'mother_name': rec.mother_name,
					'mother_mobile': rec.mother_mobile,
					'has_guardian': rec.has_guardian,
					'guardian_name': rec.guardian_name,
					'guardian_mobile': rec.guardian_mobile,
					'street': rec.street,
					'street2': rec.street2,
					'city': rec.city,
					'state_id': rec.state_id.id,
					'country_id': rec.country_id.id,
				}

				if not rec.student_id:
					# Create student record
					rec.student_id = self.env['kb.student'].create(values).id

					# Set documents to student record
					for doc in rec.document_ids:
						doc.write({
							'student_id': rec.student_id.id		
						})
			else:
				raise exceptions.ValidationError(_("This application is not in the ready-to-accept stage. Please move this application to a ready-to-accept stage to create the student record."))

			return rec.view_student_record()

	"""
		If a new application is required for the student (e.g., change from elementary to junior high),
			then a new application should be created from the student record.
	"""
	def update_student_record(self):
		for rec in self:
			if rec.is_ready:
				values = {
					'school_id': rec.school_id.id,
					'company_id': rec.company_id.id,
					'first_name': rec.first_name,
					'middle_name': rec.middle_name,
					'last_name': rec.last_name,
					'image': rec.image,
					'birth_date': rec.birth_date,
					'gender': rec.gender,
					'blood_type': rec.blood_type,
					'blood_rhesus': rec.blood_rhesus,
					'religion': rec.religion,
					'nationality_id': rec.nationality_id.id,
					'father_name': rec.father_name,
					'father_mobile': rec.father_mobile,
					'mother_name': rec.mother_name,
					'mother_mobile': rec.mother_mobile,
					'has_guardian': rec.has_guardian,
					'guardian_name': rec.guardian_name,
					'guardian_mobile': rec.guardian_mobile,
					'street': rec.street,
					'street2': rec.street2,
					'city': rec.city,
					'state_id': rec.state_id.id,
					'country_id': rec.country_id.id,
				}

				if rec.student_id:
					# Set the current date into the student record
					rec.student_id.write(values)

					# Set documents to student record
					for doc in rec.document_ids:
						doc.write({
							'student_id': rec.student_id.id		
						})
			else:
				raise exceptions.ValidationError(_("This application is not in the ready-to-accept stage. Please move this application to a ready-to-accept stage to update the student record."))

			return rec.view_student_record()

	def view_student_record(self):
		for rec in self:
			if not rec.student_id:
				raise exceptions.MissingError(_("This application is not connected to any student yet."))
			return {
				'type': 'ir.actions.act_window',
				'res_model': 'kb.student',
				'res_id': rec.student_id.id,
				'view_mode': 'form',
				'target': 'current',
			}