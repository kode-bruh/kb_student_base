from odoo import api, models, fields, exceptions, _

class Student(models.Model):
	_name = "kb.student"
	_description = _("Students")
	_inherit = ["mail.thread", "mail.activity.mixin"]
	_order = "id desc"

	name = fields.Char(compute="_compute_full_name", store=True, tracking=True)
	school_id = fields.Many2one("kb.school", ondelete="restrict", required=True, tracking=True)
	company_id = fields.Many2one("res.company", ondelete="cascade", default=lambda self: self.env.company)
	first_name = fields.Char(required=True)
	middle_name = fields.Char()
	last_name = fields.Char()
	image = fields.Binary()
	student_number = fields.Char(readonly=True, copy=False, tracking=True)
	application_ids = fields.One2many("kb.application", "student_id")
	application_count = fields.Integer(compute="_compute_application_count")

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
	height = fields.Float(default=0, tracking=True)
	height_uom = fields.Selection([
		("cm", "cm"),
		("ft", "ft"),
	], default="cm")
	weight = fields.Float(default=0, tracking=True)
	weight_uom = fields.Selection([
		("kg", "kg"),
		("lbs", "lbs"),
	], default="kg")

	# Parent / guardian information
	father_name = fields.Char(tracking=True)
	father_mobile = fields.Char(tracking=True)
	mother_name = fields.Char(tracking=True)
	mother_mobile = fields.Char(tracking=True)
	has_guardian = fields.Boolean(tracking=True)
	guardian_name = fields.Char(tracking=True)
	guardian_mobile = fields.Char(tracking=True)

	# Address information
	street = fields.Char()
	street2 = fields.Char()
	city = fields.Char()
	state_id = fields.Many2one("res.country.state", ondelete="set null")
	country_id = fields.Many2one("res.country", ondelete="set null", default=lambda self: self.env.company.country_id)

	# Classes 
	class_id = fields.Many2one("kb.class", ondelete="set null", compute="_compute_current_class")
	class_ids = fields.One2many("kb.class.history", "student_id", readonly=True, copy=False)

	# Documents
	document_ids = fields.One2many("kb.student.document", "student_id")
	
	# Ownership
	user_id = fields.Many2one("res.users", ondelete="set null", readonly=True, copy=False) # Ideally points to the parent's portal user

	_sql_constraints = [('unique_school_number', 'UNIQUE(school_id, student_number)', _('Registration number must be unique for each student.'))]

	@api.model_create_multi
	def create(self, vals_list):
		for values in vals_list:
			school = self.env['kb.school'].browse(values.get('school_id', 0))
			if not school.student_number_sequence_id:
				raise exceptions.ValidationError(_("The selected school %s does not have pre-defined sequence for student numbering. Please define the sequence first." % school.name))
			values['student_number'] = self.env['ir.sequence'].sudo().next_by_code('student_numbering_%s' % school.id)
		return super(Student, self).create(vals_list)

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

	@api.depends("application_ids")
	def _compute_application_count(self):
		for rec in self:
			rec.application_count = len(rec.application_ids)

	@api.depends("class_ids")
	def _compute_current_class(self):
		for rec in self:
			if rec.class_ids:
				rec.class_id = sorted(rec.class_ids, key=lambda history: history.class_id.sequence, reverse=True)[0].class_id.id
			else:
				rec.class_id = False

	def view_documents(self):
		for rec in self:
			return {
				'type': 'ir.actions.act_window',
				'name': _("%s Documents" % rec.name),
				'res_model': 'kb.student.document',
				'view_mode': 'list,form',
				'target': 'current',
				'domain': "[('student_id', '=', %s)]" % rec.id,
			}

	def add_class_history(self):
		for rec in self:
			return {
				'type': 'ir.actions.act_window',
				'name': _("Add New Class"),
				'res_model': 'kbw.class.history.create',
				'view_mode': 'form',
				'target': 'new',
				'context': {
					'default_line_ids': [(0, 0, {
						'student_id': rec.id
					})],
				}
			}

	def view_class_history(self):
		for rec in self:
			return {
				'type': 'ir.actions.act_window',
				'name': _("%s Classes" % rec.name),
				'res_model': 'kb.class.history',
				'view_mode': 'list',
				'target': 'current',
				'domain': "[('id', 'in', %s)]" % rec.class_ids.ids,
			}

	def view_student_application(self):
		for rec in self:
			return {
				'type': 'ir.actions.act_window',
				'name': _("%s Applications" % rec.name),
				'res_model': 'kb.application',
				'view_mode': 'list,form',
				'target': 'current',
				'domain': "[('id', 'in', %s)]" % rec.application_ids.ids,
				'context': {
					'default_student_id': rec.id,
					'default_company_id': rec.company_id.id,
					'default_first_name': rec.first_name,
					'default_middle_name': rec.middle_name,
					'default_last_name': rec.last_name,
					'default_birth_date': rec.birth_date,
					'default_gender': rec.gender,
					'default_blood_type': rec.blood_type,
					'default_blood_rhesus': rec.blood_rhesus,
					'default_religion': rec.religion,
					'default_nationality_id': rec.nationality_id.id,
					'default_father_name': rec.father_name,
					'default_father_mobile': rec.father_mobile,
					'default_mother_name': rec.mother_name,
					'default_mother_mobile': rec.mother_mobile,
					'default_has_guardian': rec.has_guardian,
					'default_guardian_name': rec.guardian_name,
					'default_guardian_mobile': rec.guardian_mobile,
					'default_street': rec.street,
					'default_street2': rec.street2,
					'default_city': rec.city,
					'default_state_id': rec.state_id.id,
					'default_country_id': rec.country_id.id,
				}
			}

	def create_student_application(self):
		for rec in self:
			return {
				'type': 'ir.actions.act_window',
				'res_model': 'kb.application',
				'view_mode': 'form',
				'target': 'current',
				'context': {
					'default_student_id': rec.id,
					'default_company_id': rec.company_id.id,
					'default_first_name': rec.first_name,
					'default_middle_name': rec.middle_name,
					'default_last_name': rec.last_name,
					'default_image': rec.image,
					'default_birth_date': rec.birth_date,
					'default_gender': rec.gender,
					'default_blood_type': rec.blood_type,
					'default_blood_rhesus': rec.blood_rhesus,
					'default_religion': rec.religion,
					'default_nationality_id': rec.nationality_id.id,
					'default_father_name': rec.father_name,
					'default_father_mobile': rec.father_mobile,
					'default_mother_name': rec.mother_name,
					'default_mother_mobile': rec.mother_mobile,
					'default_has_guardian': rec.has_guardian,
					'default_guardian_name': rec.guardian_name,
					'default_guardian_mobile': rec.guardian_mobile,
					'default_street': rec.street,
					'default_street2': rec.street2,
					'default_city': rec.city,
					'default_state_id': rec.state_id.id,
					'default_country_id': rec.country_id.id,
				}
			}