from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_user, login_required, logout_user, current_user
from .models import (
    User, Subject, PCAssignment, Equipment, IssueReport, Room,
    BorrowRequest, BorrowRequestStatus, EquipmentType, Maintenance
)
from . import db
from datetime import datetime
from flask import jsonify

# Create a Blueprint for main routes
main = Blueprint('main', __name__)

@main.route('/')
def index():
    return render_template('index.html')

@main.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        if current_user.role == 'Admin':
            return redirect(url_for('admin.admin_dashboard'))
        else:
            return redirect(url_for('main.dashboard'))
    if request.method == 'POST':
        email = request.form['email'].strip().lower()
        password = request.form['password']
        user = User.query.filter_by(email=email).first()
        if user and user.check_password(password):
            login_user(user)
            if user.role == 'Admin':
                return redirect(url_for('admin.admin_dashboard'))
            else:
                return redirect(url_for('main.dashboard'))
        else:
            flash('Invalid email or password.', 'danger')
    return render_template('login.html')

@main.route('/dashboard')
@login_required
def dashboard():
    if current_user.role == 'Admin':
        return redirect(url_for('admin.admin_dashboard'))
    subjects = current_user.subjects
    pc_assignments = {pa.subject_id: pa for pa in current_user.pc_assignments}
    issue_reports = IssueReport.query.filter_by(user_id=current_user.id).order_by(IssueReport.created_at.desc()).all()
    return render_template('user/dashboard.html', subjects=subjects, pc_assignments=pc_assignments, issue_reports=issue_reports)

@main.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.index'))



@main.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    if request.method == 'POST':
        current_user.full_name = request.form['full_name']
        current_user.email = request.form['email']
        db.session.commit()
        flash('Profile updated successfully.', 'success')
        return redirect(url_for('main.dashboard'))
    return render_template('user/edit_profile.html', user=current_user)



@main.route('/report_issue', methods=['GET', 'POST'])
@login_required
def report_issue():
    pcs = Equipment.query.filter_by(is_available=True).all()
    # Define the list of common software
    COMMON_SOFTWARE = [
        'Microsoft Access',
        'Cisco Packet Tracer',
        'Microsoft Excel',
        'Microsoft Visual Studio Code',
        'PyCharm',
        'IntelliJ IDEA',
        'Eclipse IDE',
        'NetBeans IDE',
        'Sublime Text',
        'Notepad++',
        'MATLAB',
    
        'Adobe Photoshop',
    
    ]
    if request.method == 'POST':
        equipment_id = request.form['equipment_id']
        description = request.form['description'].strip()
        issue_type = request.form['issue_type']
        software = None

        if issue_type in ['Software', 'Both']:
            selected_software = request.form.get('software', '')
            if selected_software == 'Other':
                software = request.form.get('software_other', '').strip()
            else:
                software = selected_software

        if not description:
            flash('Description cannot be empty.', 'danger')
            return redirect(url_for('main.report_issue'))

        issue = IssueReport(
            equipment_id=equipment_id,
            user_id=current_user.id,
            description=description,
            issue_type=issue_type,
            software=software,
            status='Pending'
        )
        db.session.add(issue)
        db.session.commit()
        flash('Issue reported successfully.', 'success')
        return redirect(url_for('main.dashboard'))
    return render_template('user/report_issue.html', pcs=pcs, common_software=COMMON_SOFTWARE)



# Route to view specific issue report details (optional)
@main.route('/issue/<int:issue_id>')
@login_required
def view_issue(issue_id):
    issue = IssueReport.query.get_or_404(issue_id)
    if issue.user_id != current_user.id and current_user.role != 'Admin':
        flash('You do not have permission to view this issue.', 'danger')
        return redirect(url_for('main.dashboard'))
    return render_template('user/view_issue.html', issue=issue)

@main.route('/borrow_laptop/<int:subject_id>', methods=['GET', 'POST'])
@login_required
def borrow_laptop(subject_id):
    subject = Subject.query.get_or_404(subject_id)
    # Check if the user is enrolled in the subject
    if subject not in current_user.subjects:
        flash('You are not enrolled in this subject.', 'danger')
        return redirect(url_for('main.dashboard'))
    
    # Check if the user's assigned PC is under maintenance during the subject's schedule
    pc_assignment = PCAssignment.query.filter_by(student_id=current_user.id, subject_id=subject.id).first()
    if not pc_assignment:
        flash('You do not have a PC assigned for this subject.', 'danger')
        return redirect(url_for('main.dashboard'))
    
    equipment = pc_assignment.equipment
    maintenance = next((m for m in equipment.maintenances if m.status in ['Scheduled', 'In Progress'] and m.scheduled_date <= subject.end_time and m.scheduled_date >= subject.start_time), None)
    if not maintenance:
        flash('Your assigned PC is not under maintenance during this subject.', 'danger')
        return redirect(url_for('main.dashboard'))
    
    # Get available laptops
    laptops = Equipment.query.filter_by(equipment_type=EquipmentType.Laptop, is_available=True).all()
    if not laptops:
        flash('No laptops are currently available.', 'danger')
        return redirect(url_for('main.dashboard'))
    
    if request.method == 'POST':
        laptop_id = request.form['laptop_id']
        borrow_request = BorrowRequest(
            user_id=current_user.id,
            equipment_id=laptop_id,
            status=BorrowRequestStatus.Pending
        )
        db.session.add(borrow_request)
        db.session.commit()
        flash('Laptop borrow request submitted successfully.', 'success')
        return redirect(url_for('main.dashboard'))
    
    return render_template('user/borrow_laptop.html', laptops=laptops, subject=subject)


@main.route('/get_subjects')
@login_required
def get_subjects():
    # Fetch the current user's subjects
    subjects = current_user.subjects  # Assuming you have a relationship set up
    events = []
    for subject in subjects:
        events.append({
            'title': f'{subject.subject_code} - {subject.subject_name}',
            'start': subject.start_time.isoformat(),
            'end': subject.end_time.isoformat(),
            # Optionally, add more fields like 'url' if needed
        })
    return jsonify(events)





