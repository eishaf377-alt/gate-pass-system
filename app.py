from flask import Flask, render_template, redirect, url_for, request, flash
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, User, GatePass
from datetime import datetime
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key_here'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///gatepass.db'

db.init_app(app)
login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
def home():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('dashboard'))
        flash('Invalid username or password')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        role = request.form.get('role', 'student') # Default to student
        
        if User.query.filter_by(username=username).first():
            flash('Username already exists')
            return redirect(url_for('register'))
            
        new_user = User(username=username, password=generate_password_hash(password, method='pbkdf2:sha256'), role=role)
        db.session.add(new_user)
        db.session.commit()
        login_user(new_user)
        return redirect(url_for('dashboard'))
    return render_template('register.html')

@app.route('/dashboard')
@login_required
def dashboard():
    if current_user.role == 'admin':
        passes = GatePass.query.filter_by(status='Pending').all()
        return render_template('dashboard.html', passes=passes, is_admin=True)
    else:
        passes = GatePass.query.filter_by(user_id=current_user.id).order_by(GatePass.created_at.desc()).all()
        return render_template('dashboard.html', passes=passes, is_admin=False)

@app.route('/apply', methods=['GET', 'POST'])
@login_required
def apply_pass():
    if request.method == 'POST':
        reason = request.form.get('reason')
        out_time_str = request.form.get('out_time')
        in_time_str = request.form.get('in_time')
        
        try:
            out_time = datetime.strptime(out_time_str, '%Y-%m-%dT%H:%M')
            in_time = datetime.strptime(in_time_str, '%Y-%m-%dT%H:%M')
        except ValueError:
            flash('Invalid date format')
            return redirect(url_for('apply_pass'))

        new_pass = GatePass(user_id=current_user.id, reason=reason, out_time=out_time, in_time=in_time)
        db.session.add(new_pass)
        db.session.commit()
        flash('Pass requested successfully')
        return redirect(url_for('dashboard'))
    return render_template('apply_pass.html')

@app.route('/update_pass/<int:pass_id>/<string:action>')
@login_required
def update_pass(pass_id, action):
    if current_user.role != 'admin':
        return "Unauthorized", 403
    
    gate_pass = GatePass.query.get_or_404(pass_id)
    if action == 'approve':
        gate_pass.status = 'Approved'
    elif action == 'reject':
        gate_pass.status = 'Rejected'
    
    db.session.commit()
    return redirect(url_for('dashboard'))

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

def create_db():
    with app.app_context():
        db.create_all()
        # Create a default admin if not exists
        if not User.query.filter_by(username='admin').first():
            admin = User(username='admin', password=generate_password_hash('admin123', method='pbkdf2:sha256'), role='admin')
            db.session.add(admin)
            db.session.commit()

if __name__ == '__main__':
    if not os.path.exists('gatepass.db'):
        create_db()
    app.run(debug=True)
