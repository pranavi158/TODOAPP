from flask import Flask, render_template, request, redirect, session, flash, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, User, Task
import razorpay

import os
from dotenv import load_dotenv

load_dotenv()

SECRET_KEY = os.environ.get('SECRET_KEY', 'your_fallback_secret_key')
DATABASE_URI = os.environ.get('DATABASE_URI', 'sqlite:///database.sqlite')
RAZORPAY_KEY = os.environ.get('RAZORPAY_KEY')
RAZORPAY_SECRET = os.environ.get('RAZORPAY_SECRET')

app = Flask(__name__)
app.secret_key = SECRET_KEY
app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URI
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
client = razorpay.Client(auth=(RAZORPAY_KEY, RAZORPAY_SECRET))

db.init_app(app)

with app.app_context():
    db.create_all()

# --- Auth Routes ---
@app.route('/create-order', methods=['POST'])
def create_order():
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    data = { "amount": 50000, "currency": "INR", "receipt": "order_rcptid_11" }
    order = client.order.create(data=data)
    
    return jsonify({
        'order_id': order['id'], 
        'key_id': RAZORPAY_KEY,
        'amount': data['amount'],
        'currency': data['currency']
    })

@app.route('/upgrade-success', methods=['POST'])
def upgrade_success():
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    user = User.query.get(session['user_id'])
    if user:
        user.role = 'Premium'
        db.session.commit()
    return jsonify({'success': True})

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if User.query.filter_by(username=username).first():
            flash('Username already exists', 'danger')
            return redirect('/signup')
            
        new_user = User(username=username, password_hash=generate_password_hash(password))
        db.session.add(new_user)
        db.session.commit()
        flash('Account created! Please login.', 'success')
        return redirect('/login')
    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password_hash, password):
            session['user_id'] = user.id
            session['username'] = user.username
            flash(f'Welcome back, {user.username}!', 'success')
            return redirect('/')
        flash('Invalid credentials', 'danger')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')

# --- Task Routes ---

@app.route('/')
def index():
    if 'user_id' not in session:
        return redirect('/login')
    
    search_query = request.args.get('query')
    if search_query:
        tasks = Task.query.filter(Task.user_id == session['user_id'], 
                                  Task.title.contains(search_query)).all()
    else:
        tasks = Task.query.filter_by(user_id=session['user_id']).all()
        
    user = User.query.get(session['user_id'])
    return render_template('index.html', tasks=tasks, user=user)

@app.route('/task/create', methods=['GET', 'POST'])
def create_task():
    if 'user_id' not in session: return redirect('/login')
    
    if request.method == 'POST':
        title = request.form.get('title')
        if not title:
            flash("Title is required!", "warning")
            return redirect('/task/create')
            
        new_task = Task(title=title, 
                        description=request.form.get('description'),
                        priority=request.form.get('priority'),
                        user_id=session['user_id'])
        db.session.add(new_task)
        db.session.commit()
        flash("Task added!", "success")
        return redirect('/')
    return render_template('create_task.html')

@app.route('/task/edit/<int:id>', methods=['GET', 'POST'])
def edit_task(id):
    task = Task.query.get_or_404(id)
    if task.user_id != session['user_id']: return redirect('/')
    
    if request.method == 'POST':
        task.title = request.form.get('title')
        task.priority = request.form.get('priority')
        db.session.commit()
        flash("Task updated!", "info")
        return redirect('/')
    return render_template('edit_task.html', task=task)

@app.route('/task/delete/<int:id>')
def delete_task(id):
    task = Task.query.get_or_404(id)
    if task.user_id == session['user_id']:
        db.session.delete(task)
        db.session.commit()
        flash("Task removed", "secondary")
    return redirect('/')

@app.route('/task/toggle/<int:id>', methods=['POST'])
def toggle_task(id):
    task = Task.query.get_or_404(id)
    if task.user_id == session['user_id']:
        task.status = 'Completed' if request.form.get('status') else 'Pending'
        db.session.commit()
    return redirect('/')

# --- API Route ---
@app.route('/api/tasks')
def api_tasks():
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    tasks = Task.query.filter_by(user_id=session['user_id']).all()
    tasks_list = []
    for task in tasks:
        tasks_list.append({
            'id': task.id,
            'title': task.title,
            'description': task.description,
            'status': task.status,
            'priority': task.priority
        })
    return jsonify(tasks_list)


if __name__ == '__main__':
    app.run(debug=True)
