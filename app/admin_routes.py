from flask import (
    Blueprint, render_template, redirect, url_for, flash, request, jsonify
)
from flask_login import login_required, current_user
from datetime import datetime
from sqlalchemy import or_

from . import db
from .models import (
    Room, Equipment, User, Subject, StudentSubject, PCAssignment,
    IssueReport, Maintenance, BorrowRequest, BorrowRequestStatus,
    EquipmentType
)
from .decorators import admin_required

# Create a Blueprint for admin routes with a URL prefix
admin = Blueprint('admin', __name__, url_prefix='/admin')


@admin.route('/dashboard')
@login_required
def admin_dashboard():
    """
    Admin dashboard route that displays rooms, subjects, PC assignments,
    maintenance tasks, new issues, and pending borrow requests.
    """
    if current_user.role != 'Admin':
        flash('You do not have permission to access this page.', 'danger')
        return redirect(url_for('main.dashboard'))

    # Fetch data for the dashboard
    rooms = Room.query.all()
    subjects = Subject.query.all()
    pc_assignments = PCAssignment.query.all()
    maintenances = Maintenance.query.order_by(
        Maintenance.scheduled_date.desc()
    ).all()
    new_issues = IssueReport.query.filter_by(status='Pending').all()
    pending_borrow_requests = BorrowRequest.query.filter_by(
        status=BorrowRequestStatus.Pending
    ).all()

    # Prepare a dictionary to hold current maintenance for each equipment
    maintenance_dict = {}
    for assignment in pc_assignments:
        equipment = assignment.equipment
        current_maintenance = Maintenance.query.filter(
            Maintenance.equipment_id == equipment.id,
            Maintenance.status.in_(['Scheduled', 'In Progress'])
        ).first()
        maintenance_dict[equipment.id] = current_maintenance

    # Render the admin dashboard template with fetched data
    return render_template(
        'admin/admin_dashboard.html',
        rooms=rooms,
        subjects=subjects,
        pc_assignments=pc_assignments,
        maintenances=maintenances,
        new_issues=new_issues,
        pending_borrow_requests=pending_borrow_requests,
        maintenance_dict=maintenance_dict
    )


# CRUD Operations for Rooms

@admin.route('/rooms/create', methods=['GET', 'POST'])
@admin_required
def create_room():
    """
    Route to create a new room. Automatically adds 35 PCs to the room.
    """
    if request.method == 'POST':
        room_name = request.form['room_name'].strip()
        if not room_name:
            flash('Room name cannot be empty.', 'danger')
            return redirect(url_for('admin.create_room'))

        # Check if the room already exists
        existing_room = Room.query.filter_by(room_name=room_name).first()
        if existing_room:
            flash('Room already exists.', 'danger')
            return redirect(url_for('admin.create_room'))

        # Create new room
        new_room = Room(room_name=room_name)
        db.session.add(new_room)
        db.session.commit()

        # Add 35 PCs to the new room
        for i in range(1, 36):
            pc = Equipment(
                room_id=new_room.id,
                equipment_name=f'PC-{i}',
                status='Operational',
                is_available=True,
                equipment_type=EquipmentType.PC  # Ensure equipment type is PC
            )
            db.session.add(pc)
        db.session.commit()

        flash('Room created successfully with 35 PCs.', 'success')
        return redirect(url_for('admin.admin_dashboard'))

    # Render the room creation form
    return render_template('admin/create_room.html')


@admin.route('/rooms/<int:room_id>/edit', methods=['GET', 'POST'])
@admin_required
def edit_room(room_id):
    """
    Route to edit an existing room's name.
    """
    room = Room.query.get_or_404(room_id)
    if request.method == 'POST':
        room_name = request.form['room_name'].strip()
        if not room_name:
            flash('Room name cannot be empty.', 'danger')
            return redirect(url_for('admin.edit_room', room_id=room.id))

        # Update room name
        room.room_name = room_name
        db.session.commit()
        flash('Room updated successfully.', 'success')
        return redirect(url_for('admin.admin_dashboard'))

    # Render the room edit form
    return render_template('admin/edit_room.html', room=room)


@admin.route('/rooms/<int:room_id>/delete', methods=['POST'])
@admin_required
def delete_room(room_id):
    """
    Route to delete a room and its associated PCs.
    """
    room = Room.query.get_or_404(room_id)
    db.session.delete(room)
    db.session.commit()
    flash('Room and its PCs deleted successfully.', 'success')
    return redirect(url_for('admin.admin_dashboard'))


@admin.route('/rooms/<int:room_id>/pcs')
@admin_required
def view_pcs(room_id):
    """
    Route to view all PCs in a specific room.
    """
    room = Room.query.get_or_404(room_id)
    pcs = room.pcs
    return render_template('admin/view_pcs.html', room=room, pcs=pcs)


# PC Management

@admin.route('/pcs/<int:pc_id>/edit', methods=['GET', 'POST'])
@admin_required
def edit_pc(pc_id):
    """
    Route to edit PC details such as equipment name, status, and availability.
    """
    pc = Equipment.query.get_or_404(pc_id)
    if request.method == 'POST':
        equipment_name = request.form['equipment_name'].strip()
        status = request.form['status']
        is_available = 'is_available' in request.form

        if not equipment_name:
            flash('Equipment name cannot be empty.', 'danger')
            return redirect(url_for('admin.edit_pc', pc_id=pc.id))

        # Update PC details
        pc.equipment_name = equipment_name
        pc.status = status
        pc.is_available = is_available
        db.session.commit()
        flash('PC updated successfully.', 'success')
        return redirect(url_for('admin.view_pcs', room_id=pc.room_id))

    # Render the PC edit form
    return render_template('admin/edit_pc.html', pc=pc)


@admin.route('/pcs/<int:pc_id>/delete', methods=['POST'])
@admin_required
def delete_pc(pc_id):
    """
    Route to delete a PC from the system.
    """
    pc = Equipment.query.get_or_404(pc_id)
    room_id = pc.room_id
    db.session.delete(pc)
    db.session.commit()
    flash('PC deleted successfully.', 'success')
    return redirect(url_for('admin.view_pcs', room_id=room_id))


# Subject Management

@admin.route('/subjects/create', methods=['GET', 'POST'])
@admin_required
def create_subject():
    """
    Route to create a new subject and assign it to a room.
    """
    rooms = Room.query.all()
    if request.method == 'POST':
        subject_code = request.form['subject_code'].strip().upper()
        subject_name = request.form['subject_name'].strip()
        room_id = request.form['room_id']
        start_time_str = request.form['start_time']
        end_time_str = request.form['end_time']

        # Parse start and end times
        try:
            start_time = datetime.strptime(start_time_str, '%Y-%m-%dT%H:%M')
            end_time = datetime.strptime(end_time_str, '%Y-%m-%dT%H:%M')
        except ValueError:
            flash('Invalid date/time format.', 'danger')
            return redirect(url_for('admin.create_subject'))

        if start_time >= end_time:
            flash('Start time must be before end time.', 'danger')
            return redirect(url_for('admin.create_subject'))

        # Check if subject code already exists
        existing_subject = Subject.query.filter_by(subject_code=subject_code).first()
        if existing_subject:
            flash('Subject code already exists.', 'danger')
            return redirect(url_for('admin.create_subject'))

        # Create new subject
        subject = Subject(
            subject_code=subject_code,
            subject_name=subject_name,
            room_id=room_id,
            start_time=start_time,
            end_time=end_time
        )
        db.session.add(subject)
        db.session.commit()
        flash('Subject created successfully.', 'success')
        return redirect(url_for('admin.admin_dashboard'))

    # Render the subject creation form
    return render_template('admin/create_subject.html', rooms=rooms)


@admin.route('/subjects/<int:subject_id>/assign_students', methods=['GET', 'POST'])
@admin_required
def assign_students(subject_id):
    """
    Route to assign students to a subject.
    """
    subject = Subject.query.get_or_404(subject_id)
    users = User.query.filter_by(role='User').all()

    if request.method == 'POST':
        student_ids = request.form.getlist('student_ids')
        # Remove existing assignments
        StudentSubject.query.filter_by(subject_id=subject.id).delete()
        db.session.commit()

        # Assign new students
        for student_id in student_ids:
            assignment = StudentSubject(student_id=student_id, subject_id=subject.id)
            db.session.add(assignment)
        db.session.commit()
        flash('Students assigned successfully.', 'success')
        return redirect(url_for('admin.admin_dashboard'))

    assigned_student_ids = [student.id for student in subject.students]
    return render_template(
        'admin/assign_students.html',
        subject=subject,
        users=users,
        assigned_student_ids=assigned_student_ids
    )


@admin.route('/subjects/<int:subject_id>/assign_pcs', methods=['GET', 'POST'])
@admin_required
def assign_pcs(subject_id):
    """
    Route to assign PCs to students for a specific subject.
    """
    subject = Subject.query.get_or_404(subject_id)
    students = subject.students
    room_pcs = Equipment.query.filter_by(room_id=subject.room_id).all()

    if request.method == 'POST':
        # Remove existing PC assignments for this subject
        PCAssignment.query.filter_by(subject_id=subject.id).delete()
        db.session.commit()

        # Assign PCs to students
        for student in students:
            equipment_id = request.form.get(f'pc_student_{student.id}')
            if equipment_id:
                # Check for overlapping assignments
                overlapping_assignments = PCAssignment.query.join(Subject).filter(
                    PCAssignment.equipment_id == equipment_id,
                    Subject.start_time < subject.end_time,
                    Subject.end_time > subject.start_time
                ).all()
                if overlapping_assignments:
                    flash(
                        f"PC {Equipment.query.get(equipment_id).equipment_name} "
                        "is already assigned during this time.",
                        'danger'
                    )
                    return redirect(url_for('admin.assign_pcs', subject_id=subject.id))

                assignment = PCAssignment(
                    subject_id=subject.id,
                    student_id=student.id,
                    equipment_id=equipment_id
                )
                db.session.add(assignment)
        db.session.commit()
        flash('PCs assigned to students successfully.', 'success')
        return redirect(url_for('admin.admin_dashboard'))

    # Map student IDs to their assigned PC IDs
    pc_assignments = {pa.student_id: pa.equipment_id for pa in subject.pc_assignments}
    return render_template(
        'admin/assign_pcs.html',
        subject=subject,
        students=students,
        pcs=room_pcs,
        pc_assignments=pc_assignments
    )


# Maintenance Management

@admin.route('/maintenances')
@admin_required
def list_maintenances():
    """
    Route to list all maintenance tasks.
    """
    maintenances = Maintenance.query.order_by(
        Maintenance.scheduled_date.desc()
    ).all()
    return render_template('admin/list_maintenances.html', maintenances=maintenances)


@admin.route('/maintenances/create', methods=['GET', 'POST'])
@admin_required
def create_maintenance():
    """
    Route to create a new maintenance task for equipment.
    """
    equipments = Equipment.query.all()
    if request.method == 'POST':
        equipment_id = request.form['equipment_id']
        description = request.form['description'].strip()
        scheduled_date_str = request.form['scheduled_date']

        # Parse scheduled date
        try:
            scheduled_date = datetime.strptime(scheduled_date_str, '%Y-%m-%dT%H:%M')
        except ValueError:
            flash('Invalid date/time format. Please use the date picker.', 'danger')
            return redirect(url_for('admin.create_maintenance'))

        if not description:
            flash('Description cannot be empty.', 'danger')
            return redirect(url_for('admin.create_maintenance'))

        # Create new maintenance task
        maintenance = Maintenance(
            equipment_id=equipment_id,
            reported_by=current_user.id,
            description=description,
            status='Scheduled',
            scheduled_date=scheduled_date
        )
        db.session.add(maintenance)
        db.session.commit()
        flash('Maintenance task created successfully.', 'success')
        return redirect(url_for('admin.list_maintenances'))

    # Render the maintenance creation form
    return render_template('admin/create_maintenance.html', equipments=equipments)


@admin.route('/maintenances/<int:maintenance_id>/edit', methods=['GET', 'POST'])
@admin_required
def edit_maintenance(maintenance_id):
    """
    Route to edit an existing maintenance task.
    """
    maintenance = Maintenance.query.get_or_404(maintenance_id)
    equipments = Equipment.query.all()

    if request.method == 'POST':
        maintenance.equipment_id = request.form['equipment_id']
        maintenance.description = request.form['description'].strip()
        scheduled_date_str = request.form['scheduled_date']

        # Parse scheduled date
        try:
            maintenance.scheduled_date = datetime.strptime(
                scheduled_date_str, '%Y-%m-%dT%H:%M'
            )
        except ValueError:
            flash(
                'Invalid scheduled date/time format. Please use the date picker.',
                'danger'
            )
            return redirect(url_for('admin.edit_maintenance', maintenance_id=maintenance.id))

        # Parse completed date if provided
        completed_date_str = request.form.get('completed_date', None)
        if completed_date_str:
            try:
                maintenance.completed_date = datetime.strptime(
                    completed_date_str, '%Y-%m-%dT%H:%M'
                )
            except ValueError:
                flash(
                    'Invalid completed date/time format. Please use the date picker.',
                    'danger'
                )
                return redirect(url_for('admin.edit_maintenance', maintenance_id=maintenance.id))

        db.session.commit()
        flash('Maintenance task updated successfully.', 'success')
        return redirect(url_for('admin.list_maintenances'))

    # Render the maintenance edit form
    return render_template(
        'admin/edit_maintenance.html',
        maintenance=maintenance,
        equipments=equipments
    )


@admin.route('/maintenances/<int:maintenance_id>/delete', methods=['POST'])
@admin_required
def delete_maintenance(maintenance_id):
    """
    Route to delete a maintenance task.
    """
    maintenance = Maintenance.query.get_or_404(maintenance_id)
    db.session.delete(maintenance)
    db.session.commit()
    flash('Maintenance task deleted successfully.', 'success')
    return redirect(url_for('admin.list_maintenances'))


# API Endpoint to get available PCs in a room

@admin.route('/rooms/<int:room_id>/available_pcs')
@admin_required
def get_available_pcs(room_id):
    """
    API endpoint to get a list of available PCs in a specific room.
    """
    room = Room.query.get_or_404(room_id)
    pcs = Equipment.query.filter_by(room_id=room_id).all()

    # Create a list of PCs with their ID and name
    pc_list = [{'id': pc.id, 'name': pc.equipment_name} for pc in pcs]
    return jsonify(pc_list)


# Issue Reports Management

@admin.route('/issue_reports')
@admin_required
def view_issue_reports():
    """
    Route to view all issue reports submitted by students.
    """
    issues = IssueReport.query.order_by(IssueReport.created_at.desc()).all()
    return render_template('admin/view_issue_reports.html', issues=issues)


@admin.route('/issue_reports/<int:issue_id>/update_status', methods=['POST'])
@admin_required
def update_issue_status(issue_id):
    """
    Route to update the status of an issue report.
    """
    issue = IssueReport.query.get_or_404(issue_id)
    new_status = request.form['status']
    issue.status = new_status
    db.session.commit()
    flash('Issue status updated successfully.', 'success')
    return redirect(url_for('admin.view_issue_reports'))


# Borrow Requests Management

@admin.route('/borrow_requests')
@admin_required
def view_borrow_requests():
    """
    Route to view all laptop borrow requests.
    """
    requests = BorrowRequest.query.order_by(
        BorrowRequest.request_date.desc()
    ).all()
    return render_template(
        'admin/borrow_requests.html',
        requests=requests,
        BorrowRequestStatus=BorrowRequestStatus
    )


@admin.route('/borrow_requests/<int:request_id>/update_status', methods=['POST'])
@admin_required
def update_borrow_request_status(request_id):
    """
    Route to update the status of a borrow request.
    """
    borrow_request = BorrowRequest.query.get_or_404(request_id)
    new_status_value = request.form['status']

    # Validate and set new status
    try:
        new_status = BorrowRequestStatus(new_status_value)
        borrow_request.status = new_status
    except ValueError:
        flash('Invalid status.', 'danger')
        return redirect(url_for('admin.view_borrow_requests'))

    borrow_request.admin_id = current_user.id

    # Update laptop availability based on status
    if new_status == BorrowRequestStatus.Approved:
        borrow_request.equipment.is_available = False
    elif new_status == BorrowRequestStatus.Returned:
        borrow_request.equipment.is_available = True

    db.session.commit()
    flash('Borrow request status updated successfully.', 'success')
    return redirect(url_for('admin.view_borrow_requests'))


@admin.route('/edit_equipment_maintenance/<int:equipment_id>', methods=['GET', 'POST'])
@login_required
def edit_equipment_maintenance(equipment_id):
    """
    Route to edit maintenance information for a specific equipment.
    """
    if current_user.role != 'Admin':
        flash('You do not have permission to access this page.', 'danger')
        return redirect(url_for('main.dashboard'))

    equipment = Equipment.query.get_or_404(equipment_id)

    # Get current maintenance task if it exists
    current_maintenance = Maintenance.query.filter(
        Maintenance.equipment_id == equipment.id,
        Maintenance.status.in_(['Scheduled', 'In Progress'])
    ).first()

    if request.method == 'POST':
        status = request.form['status']
        scheduled_date_str = request.form['scheduled_date']
        description = request.form['description'].strip()

        try:
            scheduled_date = datetime.strptime(scheduled_date_str, '%Y-%m-%dT%H:%M')
        except ValueError:
            flash('Invalid date/time format.', 'danger')
            return redirect(
                url_for('admin.edit_equipment_maintenance', equipment_id=equipment.id)
            )

        if current_maintenance:
            # Update existing maintenance
            current_maintenance.status = status
            current_maintenance.scheduled_date = scheduled_date
            current_maintenance.description = description
        else:
            # Create new maintenance task
            new_maintenance = Maintenance(
                equipment_id=equipment.id,
                reported_by=current_user.id,
                description=description,
                status=status,
                scheduled_date=scheduled_date,
                created_at=datetime.utcnow()
            )
            db.session.add(new_maintenance)

        db.session.commit()
        flash('Maintenance information updated successfully.', 'success')
        return redirect(url_for('admin.admin_dashboard'))

    # Render the maintenance edit form
    return render_template(
        'admin/edit_equipment_maintenance.html',
        equipment=equipment,
        maintenance=current_maintenance
    )


@admin.route('/add_laptops', methods=['GET', 'POST'])
@admin_required
def add_laptops():
    """
    Route to add multiple laptops to the system.
    """
    if request.method == 'POST':
        num_laptops = request.form.get('num_laptops', type=int, default=30)
        starting_index = request.form.get('starting_index', type=int, default=1)

        # Validate inputs
        if num_laptops < 1:
            flash('Number of laptops must be at least 1.', 'danger')
            return redirect(url_for('admin.add_laptops'))

        added_laptops = []
        for i in range(starting_index, starting_index + num_laptops):
            laptop_name = f'Laptop-{i}'
            # Check if laptop already exists
            existing_laptop = Equipment.query.filter_by(
                equipment_name=laptop_name
            ).first()
            if existing_laptop:
                flash(f'{laptop_name} already exists.', 'warning')
                continue  # Skip adding this laptop

            laptop = Equipment(
                equipment_name=laptop_name,
                equipment_type=EquipmentType.Laptop,
                status='Operational',
                is_available=True
            )
            db.session.add(laptop)
            added_laptops.append(laptop_name)

        db.session.commit()

        if added_laptops:
            flash(f"Added laptops: {', '.join(added_laptops)}.", 'success')
        else:
            flash("No new laptops were added.", 'info')

        return redirect(url_for('admin.admin_dashboard'))

    # Render the add laptops form
    return render_template('admin/add_laptops.html')
