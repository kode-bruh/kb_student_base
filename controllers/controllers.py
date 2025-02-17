# -*- coding: utf-8 -*-
from odoo import _
from odoo.http import request, route, Controller
from odoo.exceptions import AccessError, MissingError
from odoo.addons.portal.controllers.portal import CustomerPortal, pager as portal_pager

class StudentApplicationPortal(CustomerPortal):
	"""	
	Prepare values to be used in /my/home portal page.
	Values will be rendered using 'portal_my_home_application' view
	"""	
	def _prepare_home_portal_values(self, counters):
		values = super()._prepare_home_portal_values(counters)
		partner = request.env.user.partner_id

		Application = request.env['kb.application']
		if 'application_count' in counters:
			values['application_count'] = Application.search_count([]) if Application.has_access('read') else 0

		return values

	"""
	Prepare all readable records to be rendered in 'portal_my_home_application_list' view
	Values will be returned to 'portal_my_orders()' function
	"""
	def _prepare_application_portal_rendering_values(self, page=1, date_begin=None, date_end=None, sortby=None, **kwargs):
		Application = request.env['kb.application']
		if not sortby:
			sortby = 'create_date'
		partner = request.env.user.partner_id
		values = self._prepare_portal_layout_values()

		url = "/my/application"
		domain = []
		searchbar_sortings = {
			'create_date': {'label': _('Submission Date'), 'order': 'create_date desc'},
			'name': {'label': _('Name'), 'order': 'name asc'},
		}
		sort_order = searchbar_sortings[sortby]['order']

		if date_begin and date_end:
			domain += [('create_date', '>', date_begin), ('create_date', '<=', date_end)]

		pager_values = portal_pager(
			url=url,
			total=Application.search_count(domain),
			page=page,
			step=10,
			url_args={'date_begin': date_begin, 'date_end': date_end, 'sortby': sortby},
		)
		applications = Application.search(domain, order=sort_order, limit=10, offset=pager_values['offset'])
		values.update({
			'date': date_begin,
			'applications': applications.sudo(),
			'page_name': 'application_list',
			'pager': pager_values,
			'default_url': url,
		})
		if len(searchbar_sortings) > 1:
			values.update({
				'sortby': sortby,
				'searchbar_sortings': searchbar_sortings,
			})
		return values
	
	"""
	Prepare and render listing of all readable records
	Render values into 'portal_my_home_application_list' view
	"""
	@route(['/my/application', '/my/application/page/<int:page>'], type='http', auth="user", website=True)
	def portal_my_orders(self, **kwargs):
		values = self._prepare_application_portal_rendering_values(**kwargs)
		request.session['my_application_history'] = values['applications'].ids[:100]
		return request.render("kb_student_base.portal_my_home_application_list", values)

	"""
	Prepare selected record and render the record into 'application_portal_template' view
	"""
	@route(['/my/application/<int:application_id>'], type='http', auth="user", website=True)
	def portal_student_application_render(self, application_id, report_type=None, access_token=None, message=False, download=False, **kw):
		try:
			application_sudo = self._document_check_access('kb.application', application_id, access_token=access_token)
		except (AccessError, MissingError):
			return request.redirect('/my')

		if report_type in ('html', 'pdf', 'text'):
			return self._show_report(
				model=application_sudo,
				report_type=report_type,
				report_ref='kb_student_base.student_application_form',
				download=download,
			)
		values = {
			'application': application_sudo,
			'schools': request.env['kb.school'].search([('company_id', '=', request.env.company.id)]),
			'message': message,
			'report_type': 'html',
			'res_company': application_sudo.company_id,
		}
		history_session_key = 'my_application_history'
		values = self._get_page_view_values(application_sudo, access_token, values, history_session_key, False)
		return request.render('kb_student_base.application_portal_template', values)

	"""
	Similar to 'portal_student_application_render()' function, although this one does not take any record
	 as this function renders a record creation form
	"""
	@route(['/my/application/new'], type='http', auth="user", website=True)
	def portal_new_student_application_render(self, message=False, **kw):
		values = {
			'schools': request.env['kb.school'].search([('company_id', '=', request.env.company.id)]),
			'message': message,
			'res_company': request.env.company,
		}
		return request.render('kb_student_base.application_portal_template', values)

	"""
	Saves / create record
	:param application_id: If exists, browse the record and update it, else create new record
	"""
	@route(['/my/application/<int:application_id>/save', '/my/application/save'], type='http', auth="user", website=True)
	def portal_save_student_application_render(self, application_id=False, message=False, **kw):
		if application_id: # Update existing application
			try:
				application_sudo = self._document_check_access('kb.application', application_id, access_token=kw.get('access_token', None))
			except (AccessError, MissingError):
				return request.redirect('/my')
			application_sudo.write({
				'first_name': kw.get('first-name', False),
				'middle_name': kw.get('middle-name', False),
				'last_name': kw.get('last-name', False),
				'birth_date': kw.get('birth-date', False),
				'gender': kw.get('gender', False),
				'school_id': int(kw.get('school', False)),
				'father_name': kw.get('father-name', False),
				'father_mobile': kw.get('father-phone', False),
				'mother_name': kw.get('mother-name', False),
				'mother_mobile': kw.get('mother-phone', False),
				'guardian_name': kw.get('guardian-name', False),
				'guardian_mobile': kw.get('guardian-phone', False),
				'has_guardian': True if kw.get('guardian-name', False) or kw.get('guardian-phone', False) else False,
			})
		else: # Create new application
			application_sudo = request.env['kb.application'].create({
				'first_name': kw.get('first-name', False),
				'middle_name': kw.get('middle-name', False),
				'last_name': kw.get('last-name', False),
				'birth_date': kw.get('birth-date', False),
				'gender': kw.get('gender', False),
				'school_id': int(kw.get('school', False)),
				'father_name': kw.get('father-name', False),
				'father_mobile': kw.get('father-phone', False),
				'mother_name': kw.get('mother-name', False),
				'mother_mobile': kw.get('mother-phone', False),
				'guardian_name': kw.get('guardian-name', False),
				'guardian_mobile': kw.get('guardian-phone', False),
				'has_guardian': True if kw.get('guardian-name', False) or kw.get('guardian-phone', False) else False,
				'user_id': request.env.uid,
			})

		return request.redirect('/my/application/%s' % application_sudo.id)