from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "secret123"

# DATABASE
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# LOGIN
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"


# ================= MODELS ================= #

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), default='user')


class ContactMessage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    email = db.Column(db.String(100))
    subject = db.Column(db.String(200))
    message = db.Column(db.Text)


class Appointment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    phone = db.Column(db.String(20))
    date = db.Column(db.String(20))
    age = db.Column(db.String(10))
    disease = db.Column(db.String(200))


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# ================= ROUTES ================= #

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/home')
@login_required
def home():
    return render_template('home.html')


@app.route('/about')
@login_required
def about():
    return render_template('about.html')


@app.route('/services')
@login_required
def services():
    return render_template('services.html')


# ================= CONTACT ================= #

@app.route('/contact', methods=['GET', 'POST'])
@login_required
def contact():
    if request.method == 'POST':
        msg = ContactMessage(
            name=request.form.get('name'),
            email=request.form.get('email'),
            subject=request.form.get('subject'),
            message=request.form.get('message')
        )
        db.session.add(msg)
        db.session.commit()

        return "<script>alert('Message sent'); window.location='/contact'</script>"

    return render_template('contact.html')


# ================= APPOINTMENT (🔥 10 LIMIT FIXED) ================= #

@app.route('/appointment', methods=['GET', 'POST'])
@login_required
def appointment():
    if request.method == 'POST':

        date = request.form.get('date')

        # 🔥 10 per day limit
        count = Appointment.query.filter_by(date=date).count()

        if count >= 10:
            return """
            <script>
                alert('⚠️ This date is FULL (10/10). Choose another date.');
                window.location='/appointment';
            </script>
            """

        appt = Appointment(
            name=request.form.get('name'),
            phone=request.form.get('phone'),
            date=date,
            age=request.form.get('age'),
            disease=request.form.get('disease')
        )

        db.session.add(appt)
        db.session.commit()

        return """
        <script>
            alert('✅ Appointment booked successfully');
            window.location='/appointment';
        </script>
        """

    return render_template('appointment.html')


# ================= AUTH ================= #

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':

        user = User(
            name=request.form.get('name'),
            email=request.form.get('email'),
            password=generate_password_hash(request.form.get('password')),
            role='user'
        )

        db.session.add(user)
        db.session.commit()

        return redirect(url_for('login'))

    return render_template('signup.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':

        name = request.form.get('name')
        password = request.form.get('password')

        user = User.query.filter_by(name=name).first()

        if user and check_password_hash(user.password, password):
            login_user(user)

            if user.role == "admin":
                return redirect(url_for('admin_dashboard'))
            else:
                return redirect(url_for('home'))

        return "<script>alert('Invalid login'); window.location='/login'</script>"

    return render_template('login.html')


# ================= ADMIN ================= #

@app.route('/admin')
@login_required
def admin_dashboard():
    if current_user.role != "admin":
        return "Access denied"

    return render_template(
        'admin_dashboard.html',
        msg_count=ContactMessage.query.count(),
        appt_count=Appointment.query.count(),
        users=User.query.filter_by(role='user').all()
    )


@app.route('/admin/messages')
@login_required
def admin_messages():
    if current_user.role != "admin":
        return "Access denied"

    return render_template('admin_messages.html',
                           messages=ContactMessage.query.all())


@app.route('/admin/appointments')
@login_required
def admin_appointments():
    if current_user.role != "admin":
        return "Access denied"

    return render_template('admin_appointments.html',
                           data=Appointment.query.all())


# ================= DELETE ================= #

@app.route('/delete_user/<int:id>')
@login_required
def delete_user(id):
    if current_user.role != "admin":
        return "Access denied"

    user = User.query.get(id)
    if user:
        db.session.delete(user)
        db.session.commit()

    return redirect(url_for('admin_dashboard'))


@app.route('/delete_message/<int:id>')
@login_required
def delete_message(id):
    m = ContactMessage.query.get(id)
    if m:
        db.session.delete(m)
        db.session.commit()

    return redirect(url_for('admin_messages'))


@app.route('/delete_appointment/<int:id>')
@login_required
def delete_appointment(id):
    a = Appointment.query.get(id)
    if a:
        db.session.delete(a)
        db.session.commit()

    return redirect(url_for('admin_appointments'))


# ================= LOGOUT ================= #

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))


# ================= RUN ================= #

if __name__ == '__main__':
    with app.app_context():
        db.create_all()

        if not User.query.filter_by(email="admin@gmail.com").first():
            admin = User(
                name="admin",
                email="admin@gmail.com",
                password=generate_password_hash("admin123"),
                role="admin"
            )
            db.session.add(admin)
            db.session.commit()

    app.run(debug=True)