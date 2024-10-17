# app/models.py

from . import db, login_manager
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from sqlalchemy import Enum
import enum

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class IssueType(enum.Enum):
    Hardware = 'Hardware'
    Software = 'Software'
    Both = 'Both'


class BorrowRequestStatus(enum.Enum):
    Pending = 'Pending'
    Approved = 'Approved'
    Denied = 'Denied'
    Returned = 'Returned'
    
class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    student_number = db.Column(db.String(20), unique=True, nullable=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(150), nullable=False)
    full_name = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    role = db.Column(db.String(50), nullable=False, default='User')

    # Relationships
    subjects = db.relationship('Subject', secondary='student_subjects', backref='students')
    pc_assignments = db.relationship('PCAssignment', back_populates='student', lazy=True)
    issue_reports = db.relationship('IssueReport', back_populates='user', lazy=True)
    maintenances_reported = db.relationship('Maintenance', back_populates='reporter', lazy=True)  # Maintenances reported by user

    # Specify the foreign_keys to resolve ambiguity
    borrow_requests = db.relationship(
        'BorrowRequest',
        back_populates='user',
        foreign_keys='BorrowRequest.user_id',
        lazy=True
    )

    def set_password(self, password):
        self.password_hash = generate_password_hash(password, method='pbkdf2:sha256')

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Room(db.Model):
    __tablename__ = 'rooms'
    id = db.Column(db.Integer, primary_key=True)
    room_name = db.Column(db.String(50), nullable=False)
    pcs = db.relationship('Equipment', backref='room', lazy=True, cascade="all, delete-orphan")
    subjects = db.relationship('Subject', backref='room', lazy=True)

class EquipmentType(enum.Enum):
    PC = 'PC'
    Laptop = 'Laptop'

class Equipment(db.Model):
    __tablename__ = 'equipment'
    id = db.Column(db.Integer, primary_key=True)
    room_id = db.Column(db.Integer, db.ForeignKey('rooms.id'), nullable=True)  # Laptops may not be assigned to a room
    equipment_name = db.Column(db.String(100), nullable=False)
    status = db.Column(db.String(50), default='Operational')
    is_available = db.Column(db.Boolean, default=True)
    equipment_type = db.Column(db.Enum(EquipmentType), nullable=False, default=EquipmentType.PC)  # New field

    # Relationships
    issue_reports = db.relationship('IssueReport', back_populates='equipment', lazy=True)
    pc_assignments = db.relationship('PCAssignment', back_populates='equipment', lazy=True)
    maintenances = db.relationship('Maintenance', back_populates='equipment', lazy=True)


class IssueReport(db.Model):
    __tablename__ = 'issue_reports'
    id = db.Column(db.Integer, primary_key=True)
    equipment_id = db.Column(db.Integer, db.ForeignKey('equipment.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    description = db.Column(db.Text, nullable=False)
    issue_type = db.Column(db.Enum(IssueType), nullable=False)  # Ensure this attribute exists
    software = db.Column(db.String(100), nullable=True)  # Optional, for software-related issues
    status = db.Column(db.String(50), default='Pending')  # e.g., Pending, In Progress, Resolved
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)

    # Relationships
    equipment = db.relationship('Equipment', back_populates='issue_reports')
    user = db.relationship('User', back_populates='issue_reports')

class Subject(db.Model):
    __tablename__ = 'subjects'
    id = db.Column(db.Integer, primary_key=True)
    subject_code = db.Column(db.String(20), unique=True, nullable=False)
    subject_name = db.Column(db.String(100), nullable=False)
    room_id = db.Column(db.Integer, db.ForeignKey('rooms.id'), nullable=False)
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime, nullable=False)

    # Relationships
    pc_assignments = db.relationship('PCAssignment', back_populates='subject', lazy=True)

class StudentSubject(db.Model):
    __tablename__ = 'student_subjects'
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    subject_id = db.Column(db.Integer, db.ForeignKey('subjects.id'), nullable=False)

class PCAssignment(db.Model):
    __tablename__ = 'pc_assignments'
    id = db.Column(db.Integer, primary_key=True)
    subject_id = db.Column(db.Integer, db.ForeignKey('subjects.id'), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    equipment_id = db.Column(db.Integer, db.ForeignKey('equipment.id'), nullable=False)

    # Relationships
    subject = db.relationship('Subject', back_populates='pc_assignments')
    student = db.relationship('User', back_populates='pc_assignments')
    equipment = db.relationship('Equipment', back_populates='pc_assignments')

class Maintenance(db.Model):
    __tablename__ = 'maintenances'
    id = db.Column(db.Integer, primary_key=True)
    equipment_id = db.Column(db.Integer, db.ForeignKey('equipment.id'), nullable=False)
    reported_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)  # User who reported
    description = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(50), default='Scheduled')  # e.g., Scheduled, In Progress, Completed
    scheduled_date = db.Column(db.DateTime, nullable=False)
    completed_date = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)

    # Relationships
    equipment = db.relationship('Equipment', back_populates='maintenances')
    reporter = db.relationship('User', back_populates='maintenances_reported')



class BorrowRequestStatus(enum.Enum):
    Pending = 'Pending'
    Approved = 'Approved'
    Denied = 'Denied'
    Returned = 'Returned'

class BorrowRequest(db.Model):
    __tablename__ = 'borrow_requests'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    equipment_id = db.Column(db.Integer, db.ForeignKey('equipment.id'), nullable=False)
    request_date = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.Enum(BorrowRequestStatus), default=BorrowRequestStatus.Pending)
    admin_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)  # Admin who processed the request

    # Relationships
    user = db.relationship(
        'User',
        foreign_keys=[user_id],
        back_populates='borrow_requests'
    )
    equipment = db.relationship('Equipment', backref='borrow_requests')
    admin = db.relationship('User', foreign_keys=[admin_id])

