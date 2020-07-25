from flask import Flask, render_template, flash, redirect, url_for, session, request, logging
# from data import Articles
from flask_mysqldb import MySQL
from wtforms import Form, StringField, TextAreaField, DateTimeField, TimeField, IntegerField, PasswordField, validators
from passlib.hash import sha256_crypt
from functools import wraps
from MySQLdb.cursors import DictCursor
from datetime import datetime
#import matplotlib.pyplot as plt
#import matplotlib.dates as mdates
#from matplotlib import style

app = Flask(__name__)

# Config MySQL
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'matthias'
app.config['MYSQL_PASSWORD'] = 'bilbobaggins'
app.config['MYSQL_DB'] = 'irrigation_rigo'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'

#inicialize MySQL
mysql = MySQL(app)

# Articles = Articles() - Was used before to pull data from file

# Index
@app.route('/')
def index():
    # Create Cursor
    cur = mysql.connection.cursor()

    # Get Cisterns
    result= cur.execute("SELECT * FROM level_tbl, cistern_tbl WHERE level_tbl.cistern_id=cistern_tbl.cistern_id ORDER BY level_id DESC LIMIT 2 ")
    levels= cur.fetchall()

    if result > 0:
        return render_template('home.html', levels=levels)
    else:
        msg = 'No Cisterns available'
        return render_template('home.html', msg=msg)
    # Close Connection
    cur.close()

    # return render_template('home.html')

# About
@app.route('/about')
def about():
    return render_template('about.html')

# Status of WellCasabianca
@app.route('/status')
def status(chartID = 'chart_ID', chart_type = 'line', chart_height = 380):
	# Create Cursor
    cur = mysql.connection.cursor(cursorclass=DictCursor)
    # Get level_values of the last 10 day for WellCasabianca
    cur.execute("SELECT * FROM level_tbl, cistern_tbl WHERE level_tbl.cistern_id=cistern_tbl.cistern_id AND cistern_tbl.cistern_id=2 ORDER BY level_id DESC LIMIT 2880")
    result= cur.fetchall()
    dataSet=[]
    for row in result:
        # convert datestring to timestamp in milliseconds
        datestring=row['date_time']
        dt_obj = datetime.timestamp(datestring)
        millisec = dt_obj * 1000
        # calculate current cistern volume
        level_value_string=(row['level_value'])
        cistern_depth_string=row['cistern_depth']
        cistern_vol_string=row['cistern_vol']
        cisternvolume=(cistern_depth_string - level_value_string)/cistern_depth_string*cistern_vol_string
        tmp=[millisec,float(cisternvolume)]
        dataSet.append(tmp)
        cistern_name_string=row['cistern_name']
    pageType = 'graph'
    chart = {"renderTo": chartID, "type": chart_type, "height": chart_height, "zoomType":'x'}
    series = [{"name":'Fill level in m³', "data":dataSet}]
    graphtitle = {"text": cistern_name_string}
    subtitleText = {"text": 'fill level during the last 10 days'}
    xAxis = {"type":"datetime"}
    yAxis = {"title": {"text": 'Fill Level (m³)'}}
    return render_template('status.html', pageType=pageType, subtitleText=subtitleText, chartID=chartID, chart=chart, series=series, graphtitle=graphtitle, xAxis=xAxis, yAxis=yAxis)

    # Close Connection
    cur.close()

# Status of Single Cistern
@app.route('/status/<string:id>')
def singlestatus(id, chartID = 'chart_ID', chart_type = 'line', chart_height = 380):
	# Create Cursor
    cur = mysql.connection.cursor(cursorclass=DictCursor)
    # Get level_values of the last 10 day for both cisterns
    cur.execute("SELECT * FROM level_tbl, cistern_tbl WHERE level_tbl.cistern_id=cistern_tbl.cistern_id AND cistern_tbl.cistern_id=%s ORDER BY level_id DESC LIMIT 600" , [id])
    result= cur.fetchall()
    dataSet=[]
    for row in result:
        # convert datestring to timestamp in milliseconds
        datestring=row['date_time']
        dt_obj = datetime.timestamp(datestring)
        millisec = dt_obj * 1000
        # calculate current cistern volume
        level_value_string=(row['level_value'])
        cistern_depth_string=row['cistern_depth']
        cistern_vol_string=row['cistern_vol']
        cisternvolume=(cistern_depth_string - level_value_string)/cistern_depth_string*cistern_vol_string
        tmp=[millisec,float(cisternvolume)]
        dataSet.append(tmp)
        cistern_name_string=row['cistern_name']
    pageType = 'graph'
    chart = {"renderTo": chartID, "type": chart_type, "height": chart_height, "zoomType":'x'}
    series = [{"name":'Fill level in m³', "data":dataSet}]
    graphtitle = {"text": cistern_name_string}
    subtitleText = {"text": 'fill level during the last 10 days'}
    xAxis = {"type":"datetime"}
    yAxis = {"title": {"text": 'Fill Level (m³)'}}
    return render_template('status.html', pageType=pageType, subtitleText=subtitleText, chartID=chartID, chart=chart, series=series, graphtitle=graphtitle, xAxis=xAxis, yAxis=yAxis)

    # Close Connection
    cur.close()

# Irrigate
@app.route('/irrigate')
def irrigate():
    # Create Cursor
    cur = mysql.connection.cursor()
    # Get active actions
    result = cur.execute("SELECT * FROM action_tbl, relais_tbl, status_tbl WHERE action_tbl.relais_id=relais_tbl.relais_id AND action_tbl.action_status=status_tbl.status_id AND action_status>4 ORDER BY action_tbl.relais_id ASC")
    actions = cur.fetchall()

    # Get relais
    result_2 = cur.execute("SELECT * FROM relais_tbl WHERE relais_id>3 ORDER BY relais_id ASC")
    relais = cur.fetchall()

    if result > 0:
        return render_template('irrigate.html', actions=actions, relais=relais)
    else:
        msg = 'No active irrigations found'
#        return render_template('irrigate.html', msg=msg, relais=relais)
        return render_template('irrigate.html', relais=relais)

    # Close Connection
    cur.close()

# History
@app.route('/history')
def history():
    # Create Cursor
    cur = mysql.connection.cursor()
    # Get active actions
    result = cur.execute("SELECT * FROM action_tbl, relais_tbl, status_tbl WHERE action_tbl.relais_id=relais_tbl.relais_id AND action_tbl.action_status=status_tbl.status_id AND action_status<5 ORDER BY action_id DESC LIMIT 50")
    actions = cur.fetchall()

    # Get relais
    result_2 = cur.execute("SELECT * FROM relais_tbl WHERE relais_id>3")
    relais = cur.fetchall()

    if result > 0:
        return render_template('history.html', actions=actions, relais=relais)
    else:
        msg = 'No active irrigations found'
        return render_template('history.html', msg=msg, relais=relais)

    # Close Connection
    cur.close()


# Timers
@app.route('/timers')
def timers():
    # Create Cursor
    cur = mysql.connection.cursor()

    # Get timers
    # result = cur.execute("SELECT * FROM timer_tbl")
    result = cur.execute("SELECT * FROM timer_tbl, relais_tbl WHERE timer_tbl.relais_id=relais_tbl.relais_id")
    timers = cur.fetchall()

    if result > 0:
        return render_template('timers.html', timers=timers)
    else:
        msg = 'No Timers Found'
        return render_template('timers.html', msg=msg)
    # Close Connection
    cur.close()

# Single Timer
@app.route('/timer/<string:id>')
def timer(id):
    # Create Cursor
    cur = mysql.connection.cursor()

    # Get timers
    # result = cur.execute("SELECT * FROM timer_tbl WHERE timer_id = %s", [id])
    result = cur.execute("SELECT * FROM timer_tbl, relais_tbl WHERE timer_tbl.relais_id=relais_tbl.relais_id and timer_id = %s", [id])
    timer = cur.fetchone()

    return render_template('timer.html', timer=timer)

# Register Form Class
class RegisterForm(Form):
    name = StringField('Name', [validators.Length(min=1, max=50)])
    username = StringField('Username', [validators.Length(min=4, max=25)])
    email =  StringField('Email', [validators.Length(min=6, max=50)])
    password = PasswordField('Password', [
        validators.DataRequired(),
        validators.EqualTo('confirm', message='Passwords do not match')
    ])
    confirm = PasswordField('Confirm Password')

# User Register
@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm(request.form)
    if request.method == 'POST' and form.validate():
        name = form.name.data
        email = form.email.data
        username = form.username.data
        password = sha256_crypt.encrypt(str(form.password.data))

        # Create cursor
        cur = mysql.connection.cursor()

        # execute query
        cur.execute("INSERT INTO users_tbl(name, email, username, password) VALUES(%s, %s, %s, %s)", (name, email, username, password))

        # commit to DB
        mysql.connection.commit()

        # close connection
        cur.close()

        flash('You are now registered and can log in', 'success')

        return redirect(url_for('login'))
    return render_template('register.html', form=form)

# user log if __name__ == '__main__':
@app.route('/login', methods=['GET', 'POST'])
def login():
        if request.method == 'POST':
            #Get Form Fields
            username = request.form['username']
            password_candidate = request.form['password']

            # Create Cursor
            cur = mysql.connection.cursor()

            #Get user by username
            result = cur.execute("SELECT * FROM users_tbl WHERE username = %s", [username])

            if result > 0:
                # Get stored hash
                data = cur.fetchone()
                password = data['password']

                # Compare Passwords
                if sha256_crypt.verify(password_candidate, password):
                    # Passed
                    session['logged_in'] = True
                    session['username'] = username

                    flash('You are now logged in', 'success')
                    return redirect(url_for('dashboard'))
                else:
                    error = 'Invalid login'
                    return render_template('login.html', error=error)
                # Close connection
                cur.close()
            else:
                error = 'User not found'
                return render_template('login.html', error=error)

        return render_template('login.html')

# Check if user logged in

def is_logged_in(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args, **kwargs)
        else:
            flash('Unautorized, Please login', 'danger')
            return redirect(url_for('login'))
    return wrap

# Logout
@app.route('/logout')
@is_logged_in
def logout():
    session.clear()
    flash('You are now logged out', 'success')
    return redirect(url_for('login'))

# Dashboard
@app.route('/dashboard')
@is_logged_in
def dashboard():
    # Create Cursor
    cur = mysql.connection.cursor()

    # Get timers
    result = cur.execute("SELECT * FROM timer_tbl, relais_tbl, status_tbl WHERE timer_tbl.relais_id=relais_tbl.relais_id AND timer_tbl.timer_status=status_tbl.status_id")
    timers = cur.fetchall()

    if result > 0:
        return render_template('dashboard.html', timers=timers)
    else:
        msg = 'No Timers Found'
        return render_template('dashboard.html', msg=msg)

    # Get available Relais
    # result = cur.execute("SELECT * FROM relais_tbl")
    # relais = cur.fetchall()

    # Close Connection
    cur.close()

# Timer Form Class
class TimerForm(Form):
    timer_start = DateTimeField('Start Time',format='%Y-%m-%d %H:%M:%S')
    timer_end = DateTimeField('End Time',format='%Y-%m-%d %H:%M:%S')
    interrupt_hours = IntegerField('Repeat in (h)', [validators.NumberRange(min=1, max=96)], default=24)
    relais_id = IntegerField('Where? (Relais ID)', [validators.NumberRange(min=4, max=6)], default=4)

# Add Timer
@app.route('/add_timer', methods=['GET', 'POST'])
@is_logged_in
def add_timer():
    form = TimerForm(request.form)
    if request.method == 'POST' and form.validate():
        timer_start = form.timer_start.data
        timer_end = form.timer_end.data
        interrupt_hours = form.interrupt_hours.data
        relais_id = form.relais_id.data

        # Create Cursor
        cur = mysql.connection.cursor()

        # Execute
        cur.execute("INSERT INTO timer_tbl(timer_user, timer_start, timer_end, relais_id, timer_status, interrupt_hours) VALUES(%s, %s, %s, %s, %s, %s)", (session['username'], timer_start, timer_end, relais_id, 1, interrupt_hours))

        # Commit to DB
        mysql.connection.commit()

        # Close Connection
        cur.close()

        flash('Timer created', 'success')

        return redirect(url_for('dashboard'))

    return render_template('add_timer.html', form=form)

# Edit Timer
@app.route('/edit_timer/<string:id>', methods=['GET', 'POST'])
@is_logged_in
def edit_timer(id):
    # create cursor
    cur = mysql.connection.cursor()

    # get timer by id
    result = cur.execute("SELECT * FROM timer_tbl WHERE timer_id = %s", [id])

    timer = cur.fetchone()

    # Get form
    form = TimerForm(request.form)

    # Populate timer form fields
    form.timer_start.data = timer['timer_start']
    form.timer_end.data = timer['timer_end']
    form.interrupt_hours.data = timer['interrupt_hours']
    form.relais_id.data = timer['relais_id']

    if request.method == 'POST' and form.validate():
        timer_start = request.form['timer_start']
        timer_end = request.form['timer_end']
        interrupt_hours = request.form['interrupt_hours']
        relais_id = request.form['relais_id']

        # Create Cursor
        cur = mysql.connection.cursor()

        # Execute
        cur.execute("UPDATE timer_tbl SET timer_start=%s, timer_end=%s, interrupt_hours=%s, relais_id=%s WHERE timer_id=%s", (timer_start, timer_end, interrupt_hours, relais_id, id))

        # Commit to DB
        mysql.connection.commit()

        # Close Connection
        cur.close()

        flash('Timer Updated', 'success')

        return redirect(url_for('dashboard'))

    return render_template('edit_timer.html', form=form)

# Delete Timer
@app.route('/delete_timer/<string:id>', methods=['POST'])
@is_logged_in
def delete_timer(id):
    #Create Cursor
    cur= mysql.connection.cursor()

    # execute
    cur.execute("DELETE FROM timer_tbl WHERE timer_id = %s", [id])

    # Commit to DB
    mysql.connection.commit()

    # Close Connection
    cur.close()

    flash('Timer Deleted', 'success')

    return redirect(url_for('dashboard'))

# Action Form Class
class ActionForm(Form):
    action_duration = IntegerField('Duration',[validators.NumberRange(min=1, max=120)], default=60)

# Single Relais
@app.route('/irrigate/<string:id>', methods=['GET', 'POST'])
@is_logged_in
def relais(id):
    # Create Cursor
    cur = mysql.connection.cursor()

    # Get relais
    # result = cur.execute("SELECT * FROM timer_tbl WHERE timer_id = %s", [id])
    result = cur.execute("SELECT * FROM relais_tbl WHERE relais_id = %s", [id])
    relais = cur.fetchone()

    form = ActionForm(request.form)
    if request.method == 'POST' and form.validate():
        action_duration = form.action_duration.data

        # Create Cursor
        cur = mysql.connection.cursor()

        # Execute
        cur.execute("INSERT INTO action_tbl(action_user, action_start, action_end, relais_id, action_status, timer_id) VALUES(%s, NOW(), (NOW() + INTERVAL %s MINUTE), %s, %s, %s)", (session['username'], action_duration, id, 5, 0))

        # Commit to DB
        mysql.connection.commit()

        # Close Connection
        cur.close()

        flash('Action created', 'success')

        return redirect(url_for('irrigate'))

    return render_template('relais.html', form=form, relais=relais)
    return render_template('relais.html', relais=relais)

# Add Action - 30min
@app.route('/add_action/<string:id>', methods=['GET', 'POST'])
@is_logged_in
def add_action(id):
        # Create Cursor
        cur = mysql.connection.cursor()

        # Execute
        cur.execute("INSERT INTO action_tbl(action_user, action_start, action_end, relais_id, action_status, timer_id) VALUES(%s, NOW(), (NOW() + INTERVAL %s MINUTE), %s, %s, %s)", (session['username'], 30 , id, 5, 0))

        # Commit to DB
        mysql.connection.commit()

        # Close Connection
        cur.close()

        flash('Action created', 'success')

        return redirect(url_for('irrigate'))

# Delete Action
@app.route('/delete_action/<string:id>', methods=['POST'])
@is_logged_in
def delete_action(id):
    #Create Cursor
    cur= mysql.connection.cursor()

    # execute
    # check if the action to be deleted was caused by a timer
    result = cur.execute("SELECT timer_id FROM action_tbl WHERE action_id = %s", [id])
    timer=cur.fetchone()
    timer_id=timer['timer_id']
    print(timer_id)
    if timer_id > 0: # if the action was caused by a timer
        cur.execute("UPDATE action_tbl SET action_status=%s WHERE action_id = %s", (1, id)) # stop the action ("OFF_MANUALLY")
        cur.execute("UPDATE timer_tbl SET timer_status=%s WHERE timer_id = %s", (1, timer_id)) # and set the timer_status to "OFF_MANUALLY"
    else: #if the action was not caused by a timer, just stop the action ("OFF_MANUALLY")
        cur.execute("UPDATE action_tbl SET action_status=%s WHERE action_id = %s", (1, id))

            # Commit to DB
    mysql.connection.commit()

    # Close Connection
    cur.close()

    flash('Action Deleted', 'success')

    return redirect(url_for('irrigate'))


if __name__ == '__main__':
    app.secret_key='secret123'
#    app.run(debug=True)
    app.run(host='0.0.0.0')
