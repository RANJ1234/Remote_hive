from flask import redirect, url_for
from app import app

# Redirect old admin URLs to new admin blueprint URLs
@app.route('/admin/dashboard')
def admin_dashboard_redirect():
    return redirect(url_for('admin.admin_dashboard'))

@app.route('/admin/users')
def admin_users_redirect():
    return redirect(url_for('admin.manage_users'))

@app.route('/admin/jobs')
def admin_jobs_redirect():
    return redirect(url_for('admin.manage_jobs'))

@app.route('/admin/companies')
def admin_companies_redirect():
    return redirect(url_for('admin.manage_companies'))

@app.route('/admin/applications')
def admin_applications_redirect():
    return redirect(url_for('admin.manage_applications'))

@app.route('/admin/categories')
def admin_categories_redirect():
    return redirect(url_for('admin.manage_categories'))

@app.route('/admin/analytics')
def admin_analytics_redirect():
    return redirect(url_for('admin.analytics_dashboard'))

@app.route('/admin/google-analytics')
def admin_google_analytics_redirect():
    return redirect(url_for('admin.google_analytics_setup'))

@app.route('/admin/site-content')
def admin_site_content_redirect():
    return redirect(url_for('admin.manage_site_content'))
