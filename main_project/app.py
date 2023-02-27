from flask import Flask, render_template, url_for, request, redirect, session,jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import load_only
import datetime
import http.client
import pandas as pd 
from sqlalchemy import create_engine
from sqlalchemy import func
import logging
import requests
import json

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///Todo.db'
app.config['SQLALCHEMY_BINDS'] = {
    'users': 'sqlite:///users.db',
    'projects': 'sqlite:///projects.db' ,
    'graph': 'sqlite:///graph.db' 

}

db = SQLAlchemy(app)

class Todo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String(200), nullable=False)
    notes = db.Column(db.String(200), nullable=False)
    date_created = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    deadline = db.Column(db.DateTime)
    progress = db.Column(db.String(200))
    list_type = db.Column(db.String(200))
    userid = db.Column(db.String(200), nullable=False)
    related_project = db.Column(db.String(200), nullable=True)


    # username = db.Column(db.int)

class Users(db.Model):
    __bind_key__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(15), nullable=False)
    password = db.Column(db.String(15), nullable=False)
    date_created = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    isadmin = db.Column(db.Boolean, default= False, nullable= False)

class Projects(db.Model):
    __bind_key__ = 'projects'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(15), nullable=False)
    deadline= db.Column(db.DateTime)
    status = db.Column(db.String(200))
    assigned_name = db.Column(db.String(200), nullable=True)

class Graph(db.Model):
    __bind_key__ = 'graph'
    id = db.Column(db.Integer, primary_key=True)
    date_created = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    percentage = percentage = db.Column(db.Float())

    def __repr__(self):
        return 'User %r' % self.id

url = "https://worldtime5.p.rapidapi.com/api/world-time/datetime-now"

payload = {
	"datetime_format": "iso8601",
	"timezones": ["Europe/London"]
}
headers = {
	"content-type": "application/json",
	"X-RapidAPI-Key": "4bb0975d23msh2cbfb61f6a6bf87p188ea4jsn99cd5c89eb4a",
	"X-RapidAPI-Host": "worldtime5.p.rapidapi.com"
}

response = requests.request("POST", url, json=payload, headers=headers)
current_date = response.text[26:36]

labels = []
values = []
data= []
percentage = 0
counter = 0

@app.route('/', methods=['POST', 'GET'])
def index():
        return redirect('/login')

@app.route('/daily_list/<username>/<key>', methods=['POST', 'GET'])
def daily(username, key):
    if request.method == 'POST':
        task_content = request.form['content']
        task_notes = request.form['notes']
        task_progress = request.form['progress']
        formatt = "%Y-%m-%d"
        try:
            task_deadline = datetime.datetime.strptime(request.form['deadline'], formatt)
        except: 
            task_deadline = datetime.datetime.strptime('9999-9-9', formatt)
        for project in Projects.query.all():
            if username in project.assigned_name:
                task_assigned_project = project.name
        new_task = Todo(content = task_content, notes = task_notes, deadline = task_deadline, progress = task_progress, list_type = 'daily_list', userid = key, related_project = task_assigned_project)
        db.session.add(new_task)    
        db.session.commit()
        return redirect(url_for('daily',username = username, key = key))
    else:
        tasks = Todo.query.filter_by(list_type='daily_list').order_by(Todo.date_created).all()
        users = Users.query.order_by(Users.id).all()
        projects = Projects.query.order_by(Projects.name).all()
        return render_template('index.html', tasks = tasks,username = username, key = key,users = users, projects = projects)

@app.route('/adminpage/<username>/<key>')
def adminpage(username, key):
    data = []
    users_list = Users.query.order_by(Users.date_created).all()
    projects = Projects.query.order_by(Projects.deadline).all()
    exists = db.session.query(Projects.id).first() is not None
    if exists:
        for graph_value in Graph.query.all():
            data += [(str(graph_value.date_created.date()),graph_value.percentage)]
    labels = [row[0] for row in data]
    values = [row[1] for row in data]
    return render_template('adminpage.html', users_list = users_list, username = username, key = key, projects = projects, labels = labels, values = values, current_date = current_date)

@app.route('/refresh/<username>/<key>')
def refresh(username, key):
    percentage = 0
    counter = 0
    exists = db.session.query(Projects.id).first() is not None
    if exists:
        for project in Projects.query.all():
            counter += 1
            print(counter)
            if project.status == 'Done':
                percentage = percentage + 100
            print(percentage)
        percentagetemp = percentage / counter
        new_graph = Graph(percentage = percentagetemp)
        db.session.add(new_graph)
        db.session.commit()
    else:
        percentagetemp = 0
    return redirect(url_for('adminpage',username = username, key = key))


@app.route('/undo/<username>/<key>')
def undo(username, key):
    exists = db.session.query(Graph.id).first() is not None
    if exists:
        last_refresh = Graph.query.order_by(Graph.date_created.desc()).first()
        print(last_refresh)
        db.session.delete(last_refresh)
        db.session.commit()
        return redirect(url_for('adminpage',username = username, key = key))
    else:
        return redirect(url_for('adminpage',username = username, key = key))

@app.route('/add_project/<username>/<key>', methods=['POST', 'GET'])
def add_project(username, key):
    percentage = 0
    counter = 1
    if request.method == 'POST':
        project_name = request.form['project_name']
        progress = request.form['progress']
        employee_name = request.form['assigned_name']
        formatt = "%Y-%m-%d"
        try:
            project_deadline = datetime.datetime.strptime(request.form['deadline'], formatt)
        except:
            project_deadline = datetime.datetime.strptime('9999-9-9', formatt)
        exists = db.session.query(Graph.id).first() is not None
        if exists:
            for project in Projects.query.all():
                counter += 1
                print(counter)
                if project.status == 'Done':
                    percentage = percentage + 100
            if progress == 'Done':
                percentage += 100
            percentagetemp = percentage / counter   
        elif progress == 'Done' and not exists:
            percentagetemp = 100
        else:
            percentagetemp = 0
        new_graph = Graph(percentage = percentagetemp)
        db.session.add(new_graph)
        new_project = Projects(name = project_name, assigned_name = employee_name, deadline = project_deadline, status = progress)
        db.session.add(new_project)
        db.session.commit()
        return redirect(url_for('adminpage',username = username, key = key))
    else:
        print(projects)
        users_list = Users.query.order_by(Users.date_created).all()
        return render_template('adminpage.html', username = username, key = key,users_list = users_list)



@app.route('/update_assigned/<username>/<key>/<int:id>', methods=['GET', 'POST'])
def update_assigned(username, key, id):
    project = Projects.query.get_or_404(id)
    if request.method == 'POST':
        project_name = request.form['project_name']
        if not project_name == '':
            project.name = request.form['project_name']
        assigned_name = request.form['assigned_name']
        if not assigned_name == '':
            project.assigned_name = request.form['assigned_name']
        progress = request.form['progress']
        if not progress == 'Not started':
            project.status = request.form['progress']
        formatt = "%Y-%m-%d"
        try:
            project.deadline = datetime.datetime.strptime(request.form['deadline'], formatt)
        except:
            project_deadline = datetime.datetime.strptime('9999-9-9', formatt)
        
        db.session.commit()
        return redirect(url_for('adminpage',username = username, key = key))
    else:
        return render_template('update_assigned.html',username = username, project = project, key = key)

@app.route('/done/<username>/<key>/<id>')
def done(username, key, id):
    project = Projects.query.get_or_404(id)
    project.status = 'Done'
    db.session.commit()
    return redirect(url_for('daily',username = username, key = key))



@app.route('/delete_project/<username>/<key>/<int:id>')
def delete_project(username, id, key):
    project_to_delete = Projects.query.get_or_404(id)
    try:
        db.session.delete(project_to_delete)
        db.session.commit()
        return redirect(url_for('adminpage',username = username, key = key))
    except:
        return 'woops, you are a fishi'

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        for user in Users.query.all():
            if username == user.name and password == user.password:
                aidi = user.id
                username = ' ' + username + ' '
                if user.isadmin == True:
                    return redirect(url_for('adminpage', username = username, key = aidi))
                return redirect(url_for('daily', username = username, key = aidi))
        return render_template('error.html')
    return render_template('login.html')

@app.route('/about/<username>/<key>')
def about(username,key):
    try:
        return render_template('about.html',username = username, key = key)
    except:
        return 'woops, you are a fishi'

@app.route('/importance/<username>/<key>')
def importance(username,key):
    try:
        return render_template('importance.html', username = username, key = key)
    except:
        return 'woops, you are a fishi'

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['pass1']
        password_verify = request.form['pass2']
        admin = False
        print(password, password)
        if password == password_verify:
            new_account = Users(name = username, password = password, isadmin = admin)
            db.session.add(new_account)
            db.session.commit()
            return render_template('success.html')
        else:
            return render_template('match_error.html')
    return render_template('register.html')

@app.route('/delete/<username>/<key>/<int:id>')
def delete(username,key, id):
    task_to_delete = Todo.query.get_or_404(id)
    source = task_to_delete.list_type
    try:
        db.session.delete(task_to_delete)
        db.session.commit()
        return redirect('/'  + source + '/' + username + '/'+ key)
    except:
        return 'woops, you are a fishi'

@app.route('/deleteuser/<username>/<key>/<int:id>')
def deleteuser(username, key,id):
    user_to_delete = Users.query.get_or_404(id)
    try:
        db.session.delete(user_to_delete)
        db.session.commit()
        return redirect('/adminpage/' + username + '/'+ key)
    except:
        return 'woops, you are a fishi'

@app.route('/update/<username>/<key>/<int:id>', methods=['GET', 'POST'])
def update(username,key,id):
    task = Todo.query.get_or_404(id)
    source = task.list_type
    if request.method == 'POST':
        if request.form['content'] != '':
            task.content = request.form['content']
        if request.form['notes'] != '':
            task.notes = request.form['notes']
        formatt = "%Y-%m-%d"
        try:
            task.deadline = datetime.datetime.strptime(request.form['deadline'], formatt)
            print(task_deadline)
        except:
            task_deadline = datetime.datetime.strptime('9999-9-9', formatt)
        task.progress = request.form['progress']
        try:
            db.session.commit()
            return redirect('/' + source + '/' + username + '/'+ key)
        except:
            return 'woops, you are a fishi'
    else:
        return render_template('update.html',username = username, key = key, task = task)





sql_engine = create_engine('sqlite:///Todo.db', echo = False)
results = pd.read_sql_query('select * from Todo', sql_engine)
results.to_csv('Todo.csv', index=False, sep=";")

sql_engine = create_engine('sqlite:///users.db', echo = False)
results = pd.read_sql_query('select * from Users', sql_engine)
results.to_csv('Users.csv', index=False, sep=";")

sql_engine = create_engine('sqlite:///projects.db', echo = False)
results = pd.read_sql_query('select * from Projects', sql_engine)
results.to_csv('Projects.csv', index=False, sep=";")

sql_engine = create_engine('sqlite:///graph.db', echo = False)
results = pd.read_sql_query('select * from Graph', sql_engine)
results.to_csv('Graph.csv', index=False, sep=";")
if __name__ == "__main__":
    app.run(debug=True)

