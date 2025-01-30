import os
from datetime import datetime, timedelta
from flask import Flask, jsonify, request, render_template, send_from_directory, url_for, redirect
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin, login_user, login_required, logout_user, current_user, LoginManager
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import InputRequired, Length, ValidationError
from flask_bcrypt import Bcrypt
from flask_migrate import Migrate

app = Flask(__name__)
bcrypt = Bcrypt(app)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'supersecret'
app.config['DEBUG'] = False

db = SQLAlchemy(app)
migrate = Migrate(app, db)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))







class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), nullable=False,unique=True)
    password = db.Column(db.String(80), nullable=False)



task_user = db.Table('task_user',
    db.Column('task_id', db.Integer, db.ForeignKey('task.id'), primary_key=True),
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True)
)

class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    due_date = db.Column(db.String(20), nullable=True)
    priority = db.Column(db.String(20), default="Normal")
    completed = db.Column(db.Boolean, default=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    user = db.relationship('User', backref=db.backref('tasks', lazy=True))
    shared_with = db.relationship('User', secondary=task_user, backref=db.backref('shared_tasks', lazy='dynamic'))




class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    message = db.Column(db.String(255), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    read = db.Column(db.Boolean, default=False)

    user = db.relationship('User', backref=db.backref('notifications', lazy=True))







class RegisterForm(FlaskForm):
    username = StringField('Username', validators=[InputRequired(), Length(min=4, max=20)],
        render_kw={'placeholder': 'Username'})

    password = PasswordField('Password', validators=[InputRequired(), Length(min=8)],
        render_kw={'placeholder': 'Password'})

    submit = SubmitField('Register')



    def validate_username(self, username):
        existing_user_username = User.query.filter_by(
            username=username.data).first()

        if existing_user_username:
            raise ValidationError(
                'That username already exists. Please choose a different one.')


class LoginForm(FlaskForm):
    username = StringField(validators=[
                           InputRequired(), Length(min=4, max=20)], render_kw={"placeholder": "Username"})

    password = PasswordField(validators=[
                             InputRequired(), Length(min=8, max=20)], render_kw={"placeholder": "Password"})

    submit = SubmitField('Login')




UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Przykładowa lista zadań
tasks = []


@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/homepage')
def homepage():
    return render_template('index.html')
@app.route('/')
def home():
    return render_template('home.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    error = None

    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user)
            return redirect(url_for('index'))
        else:
            error = 'Incorrect username or password'
    return render_template('login.html', form=form, error=error)


@app.route('/index', methods=['GET', 'POST'])
@login_required
def index():
    return render_template('index.html')

@app.route("/logout", methods=['GET', 'POST'])
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()

    if form.validate_on_submit():
        hashed = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        new_user = User(username=form.username.data, password=hashed)
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('login'))

    return render_template('register.html', form=form)





@app.route('/tasks', methods=['GET'])
@login_required
def get_all_tasks():
    user_tasks = Task.query.filter_by(user_id=current_user.id).all()
    shared_tasks = Task.query.filter(Task.shared_with.any(id=current_user.id)).all()

    tasks_list = [
        {
            'id': task.id,
            'title': task.title,
            'start': task.due_date,  # FullCalendar wymaga pola "start"
            'description': task.description,
            'priority': task.priority,
            'completed': task.completed,
            'due_date': task.due_date,  # Dodaj due_date do danych wyjściowych
            'color': '#ff5555' if task.priority == 'High' else '#5bc0de',
        } for task in user_tasks + shared_tasks
    ]

    return jsonify(tasks_list), 200






# Dodawanie nowego zadania
@app.route('/tasks/', methods=['POST'])
@login_required
def create_task():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Invalid data'}), 400

    new_task = Task(
        title=data['title'],
        description=data.get('description', ''),
        due_date=data.get('due_date', None),
        priority=data.get('priority', 'Normal'),
        user_id=current_user.id
    )

    db.session.add(new_task)
    db.session.commit()

    return jsonify({
        'id': new_task.id,
        'title': new_task.title,
        'description': new_task.description,
        'due_date': new_task.due_date,
        'priority': new_task.priority,
        'completed': new_task.completed
    }), 201



# OSOBNY ENDPOINT TASKS
@app.route('/tasks/<int:task_id>', methods=['GET'])
@login_required
def get_task(task_id):
    task = Task.query.filter(
        (Task.id == task_id) &
        ((Task.user_id == current_user.id) | (Task.shared_with.any(id=current_user.id)))
    ).first()

    if not task:
        return jsonify({'error': 'Task not found or access denied'}), 404

    return jsonify({
        'id': task.id,
        'title': task.title,
        'description': task.description,
        'due_date': task.due_date,
        'priority': task.priority,
        'completed': task.completed,
        'shared_with': [user.username for user in task.shared_with],
        'is_owner': task.user_id == current_user.id  # Dodanie informacji o właścicielu
    }), 200







# Edytowanie istniejącego zadania
@app.route('/tasks/<int:task_id>', methods=['PUT'])
@login_required
def update_task(task_id):
    print(f"Attempting to update task {task_id} for user {current_user.username}")
    task = Task.query.filter(
        (Task.id == task_id) &
        ((Task.user_id == current_user.id) | (Task.shared_with.any(id=current_user.id)))
    ).first()

    if not task:
        print(f"Task {task_id} not found or access denied for user {current_user.username}")
        return jsonify({'error': 'Task not found or access denied'}), 404

    data = request.get_json()
    print(f"Received data: {data}")

    changes = []

    if task.user_id == current_user.id:
        
        print("Editing as owner")
        if task.title != data.get('title', task.title):
            changes.append(f"Title changed from '{task.title}' to '{data['title']}'")
            task.title = data.get('title', task.title)

        if task.description != data.get('description', task.description):
            changes.append("Description changed.")
            task.description = data.get('description', task.description)

        if task.due_date != data.get('due_date', task.due_date):
            changes.append(f"Due date changed from '{task.due_date}' to '{data['due_date']}'")
            task.due_date = data.get('due_date', task.due_date)

        if task.priority != data.get('priority', task.priority):
            changes.append(f"Priority changed from '{task.priority}' to '{data['priority']}'")
            task.priority = data.get('priority', task.priority)

        if task.completed != data.get('completed', task.completed):
            changes.append(f"Task marked as {'completed' if data['completed'] else 'incomplete'}")
            task.completed = data.get('completed', task.completed)

        if 'shared_with' in data:
            new_shared_with = [username.strip() for username in data['shared_with'].split(',') if username.strip()]
            current_shared_with = [user.username for user in task.shared_with]

            added_users = set(new_shared_with) - set(current_shared_with)
            removed_users = set(current_shared_with) - set(new_shared_with)

            if added_users:
                changes.append(f"Added shared users: {', '.join(added_users)}")
            if removed_users:
                changes.append(f"Removed shared users: {', '.join(removed_users)}")

            users_to_share = User.query.filter(User.username.in_(new_shared_with)).all()
            task.shared_with = users_to_share


    elif current_user in task.shared_with:
       
        print("Editing as shared user")
        if task.completed != data.get('completed', task.completed):
            changes.append(f"Task marked as {'completed' if data['completed'] else 'incomplete'}")
            task.completed = data.get('completed', task.completed)

        if task.description != data.get('description', task.description):
            changes.append("Description changed.")
            task.description = data.get('description', task.description)

        if task.priority != data.get('priority', task.priority):
            changes.append(f"Priority changed from '{task.priority}' to '{data['priority']}'")
            task.priority = data.get('priority', task.priority)

    else:
        print(f"Unauthorized access to task {task_id} by user {current_user.username}")
        return jsonify({'error': 'Unauthorized to edit this task'}), 403

    db.session.commit()

    
    print(f"Changes made: {changes}")
    if changes:
        for user in task.shared_with:
            if user.id != current_user.id:
                create_notification(
                    user_id=user.id,
                    message=f"Task '{task.title}' updated by {current_user.username}: {', '.join(changes)}"
                )

        if task.user_id != current_user.id:
            create_notification(
                user_id=task.user_id,
                message=f"Task '{task.title}' updated by {current_user.username}: {', '.join(changes)}"
            )

    return jsonify({
        'id': task.id,
        'title': task.title,
        'description': task.description,
        'due_date': task.due_date,
        'priority': task.priority,
        'completed': task.completed,
        'shared_with': [user.username for user in task.shared_with]
    }), 200



# Przycisk Completed
@app.route('/tasks/<int:task_id>/complete', methods=['PATCH'])
@login_required
def mark_task_complete(task_id):
    task = Task.query.filter_by(id=task_id, user_id=current_user.id).first()
    if not task:
        return jsonify({'error': 'Task not found'}), 404

    # Przełącz status completed
    task.completed = not task.completed
    db.session.commit()

    return jsonify({
        'id': task.id,
        'completed': task.completed
    }), 200



# Usuwanie zadania 
@app.route('/tasks/<int:task_id>', methods=['DELETE'])
@login_required
def delete_task(task_id):
    task = Task.query.filter_by(id=task_id, user_id=current_user.id).first()
    if not task:
        return jsonify({'error': 'Task not found'}), 404

    db.session.delete(task)
    db.session.commit()
    return '', 204


# Filtrowanie zadań
@app.route('/tasks/filter/<filter_type>', methods=['GET'])
@login_required
def filter_tasks(filter_type):
    today = datetime.now().date()

    user_tasks = Task.query.filter_by(user_id=current_user.id).all()
    shared_tasks = Task.query.filter(Task.shared_with.any(id=current_user.id)).all()

    if filter_type == 'all':  # Obsługa filtra "All"
        filtered_tasks = user_tasks + shared_tasks
    elif filter_type == 'recent':
        filtered_tasks = user_tasks[-5:]
    elif filter_type == 'due_today':
        filtered_tasks = [task for task in user_tasks if task.due_date == today.isoformat()]
    elif filter_type == 'due_this_week':
        start_of_week = today - timedelta(days=today.weekday())
        end_of_week = start_of_week + timedelta(days=6)
        filtered_tasks = [
            task for task in user_tasks
            if task.due_date and start_of_week <= datetime.fromisoformat(task.due_date).date() <= end_of_week
        ]
    elif filter_type == 'due_this_month':
        filtered_tasks = [
            task for task in user_tasks
            if task.due_date and datetime.fromisoformat(task.due_date).date().month == today.month
        ]
    elif filter_type == 'shared':
        filtered_tasks = shared_tasks
    else:
        return jsonify({'error': 'Invalid filter type'}), 400

    filtered_tasks.sort(key=lambda task: datetime.fromisoformat(task.due_date).date() if task.due_date else today)

    tasks_list = [
        {
            'id': task.id,
            'title': task.title,
            'description': task.description,
            'due_date': task.due_date,
            'priority': task.priority,
            'completed': task.completed,
            'shared_by': task.user.username if task.user.id != current_user.id else None
        } for task in filtered_tasks
    ]

    return jsonify(tasks_list), 200










def create_notification(user_id, message):
    notification = Notification(user_id=user_id, message=message)
    db.session.add(notification)
    db.session.commit()

@app.route('/notifications/unread_count', methods=['GET'])
@login_required
def get_unread_notifications_count():
    unread_count = Notification.query.filter_by(user_id=current_user.id, read=False).count()
    return jsonify({'unread_count': unread_count}), 200



@app.route('/notifications/mark_all_as_read', methods=['POST'])
@login_required
def mark_all_notifications_as_read():
    notifications = Notification.query.filter_by(user_id=current_user.id, read=False).all()
    for notification in notifications:
        notification.read = True
    db.session.commit()
    return jsonify({'message': 'All notifications marked as read'}), 200




@app.route('/notifications', methods=['GET'])
@login_required
def get_notifications():
    notifications = Notification.query.filter_by(user_id=current_user.id, read=False).all()
    print(notifications)  # Debug: wypisuje listę powiadomień w konsoli backendu
    return jsonify([{
        'id': n.id,
        'message': n.message,
        'timestamp': n.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
    } for n in notifications])


@app.route('/tasks/statistics', methods=['GET'])
@login_required
def get_statistics():
    total_tasks = Task.query.filter_by(user_id=current_user.id).count()
    high_priority_tasks = Task.query.filter_by(user_id=current_user.id, priority='High').count()
    completed_tasks = Task.query.filter_by(user_id=current_user.id, completed=True).count()

    return jsonify({
        'total_tasks': total_tasks,
        'high_priority_tasks': high_priority_tasks,
        'completed_tasks': completed_tasks
    }), 200



if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
