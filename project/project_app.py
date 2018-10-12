from flask import Flask, session, redirect, url_for, escape, request, render_template, flash
import sqlite3
import sys
import pyfingerprint
import I2C_LCD_driver
from time import *
import datetime
import calendar
import time

first_app = Flask(__name__)
first_app.config.from_object(__name__) # load config from this file
first_app.config.update(
    USERNAME='admin',
    PASSWORD='1234'
)
first_app.config.from_envvar('FLASKR_SETTINGS', silent=True)
# Set the secret key to some random bytes. Keep this really secret!
first_app.secret_key = b'_5#y2L"F4Q8z\n\xec]/'
@first_app.route('/')
@first_app.route('/index')
def index():
    error = None
    if 'username' in session:
        if session['username'] == first_app.config['USERNAME'] and session['password'] == first_app.config['PASSWORD']:
            flash('You were successfully logged in')
            return render_template('main.html', name = session['username'])
        else:
            error = 'Error: Invalid Username/Password!'
    return render_template('login.html', error = error)
# Login code
@first_app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        session['username'] = request.form['username']
        session['password'] = request.form['password']
        return redirect(url_for('index'))
    return render_template('login.html')

# Logout code
@first_app.route('/logout')
def logout():
# remove the username from the session if it's there
    session.pop('username', None)
    return redirect(url_for('login'))

#Student Enroll form
@first_app.route('/enroll_student')
def enroll_student():
    error = " Can't Access Without Login! "
    if 'username' in session:
        if session['username'] == first_app.config['USERNAME'] and session['password'] == first_app.config['PASSWORD']:
            return render_template('enroll_form.html')
    return render_template('login.html', error = error)

#Saves enrolled data
@first_app.route('/save_enroll', methods=['POST'])
def save_enroll():
    conn = sqlite3.connect('/home/pi/attendance/app.db')
    curs = conn.cursor()
    curs.execute(' INSERT INTO enroll_student (fname, lname, rollnum, dept, grp, email, mobile) values(?, ?, ?, ?, ?, ?, ?) ',
    [request.form['firstname'], request.form['lastname'], request.form['roll'], request.form['dept'], request.form['grup'], request.form['email'], request.form['mobnum']])
    conn.commit()
    conn.close()
    return render_template('enroll_form.html')
# Generating repots view
@first_app.route('/generate_reports')
def generate_reports():
    error = " Can't Access Without Login! "
    if 'username' in session:
        if session['username'] == first_app.config['USERNAME'] and session['password'] == first_app.config['PASSWORD']:
            return render_template('generate_reports.html')
    return render_template('login.html', error = error)

#Resulting views by_date, by_roll, by_group
@first_app.route('/by_date', methods=['POST'])
def by_date():
    if request.method == 'POST':
        error = " Can't Access Without Login! "
        if 'username' in session:
            if session['username'] == first_app.config['USERNAME'] and session['password'] == first_app.config['PASSWORD']:
                sdate = request.form['start_date']
                edate = request.form['end_date']
                conn = sqlite3.connect("/home/pi/attendance/app.db")
                curs = conn.cursor()
                curs.execute("SELECT rollnum, date, status, statusexit, statusnoon, statusnoonexit from attendance where date BETWEEN ? and ? ",(sdate, edate))
                val = curs.fetchall()
                val_len = len(val)
                conn.close()
                return render_template('by_date.html', allValues = val, val_len = val_len)
        return render_template('login.html', error = error)
    return "Method is not a POST"

@first_app.route('/by_roll', methods=['POST'])
def by_roll():
    if request.method == 'POST':
        error = " Can't Access Without Login! "
        if 'username' in session:
            if session['username'] == first_app.config['USERNAME'] and session['password'] == first_app.config['PASSWORD']:
                id = request.form['idnum']
                conn = sqlite3.connect("/home/pi/attendance/app.db")
                curs = conn.cursor()
                curs.execute("SELECT date from attendance where (rollnum, statusexit) in (values(?, ?)) ",(id,'present'))
                val = curs.fetchall()
                curs.execute("SELECT date from attendance where (rollnum, statusnoonexit) in (values(?, ?)) ",(id,'present'))
                val2 = curs.fetchall()
                val_len = len(val)+len(val2)
                conn.close()
                conn = sqlite3.connect("/home/pi/attendance/app.db")
                curs = conn.cursor()
                curs.execute("SELECT fname, lname from enroll_student where rollnum = ? ",(id,))
                val = curs.fetchall()
                conn.close()
                if not val:
                    return render_template('by_roll.html', id = id, val = len(val))
                else:
                    for row in val:
                        name = row[0]+" "+row[1]
                    return render_template('by_roll.html', name = name, id = id, present_days = val_len, val = len(val))
        return render_template('login.html', error = error)
    return "Method is not a POST"
@first_app.route('/by_group', methods=['POST'])
def by_group():
    if request.method == 'POST':
        error = " Can't Access Without Login! "
        if 'username' in session:
            if session['username'] == first_app.config['USERNAME'] and session['password'] == first_app.config['PASSWORD']:
                gp = request.form['grup_res']
                day_no = int(request.form['days'])
                conn = sqlite3.connect("/home/pi/attendance/app.db")
                curs = conn.cursor()
                curs.execute("SELECT enroll_student.rollnum, enroll_student.fname, enroll_student.lname, attendance.date, attendance.statusexit, attendance.statusnoonexit from enroll_student INNER JOIN attendance ON enroll_student.rollnum = attendance.rollnum WHERE enroll_student.grp = ? ",(gp,))
                val = curs.fetchall()
                conn.close()
                val_len = len(val)
                names = []  ## TO STORE ALL NAMES IN A LIST
                rolls = [] ## TO STORE ALL ROLL NUMBERS IN A LIST
                rolls_noDup = [] ##TO STORE ROLL NUMBERS WITHOUT DUPLICATES
                for row in val:
                    rolls.append(row[0])

                    if row[0] in rolls_noDup:
                        continue
                    else:
                        rolls_noDup.append(row[0])

                    if row[1]+" "+row[2] in names:
                        continue
                    else:
                        names.append(row[1]+" "+row[2])
                dd = {}
                ## CALCULATING ATTENDANCE FOR EACH ROLL Number
                conn = sqlite3.connect("/home/pi/attendance/app.db")
                curs = conn.cursor()
                for i in range(len(rolls_noDup)):
                    curs.execute("SELECT date from attendance where (rollnum, statusexit) in (values(?, ?)) ",(rolls_noDup[i],'present'))
                    value1 = curs.fetchall()
                    curs.execute("SELECT date from attendance where (rollnum, statusnoonexit) in (values(?, ?)) ",(rolls_noDup[i],'present'))
                    value2 = curs.fetchall()
                    vals = len(value1)+len(value2)
                    dd[rolls_noDup[i]] = vals
                conn.close()

                ## CREATING DICTIONARIY FOR ROLL NUMBERS AND NAMES
                name_dic = {}
                for i in range(len(rolls_noDup)):
                    name_dic[rolls_noDup[i]] = names[i]

                ## GROUP ROLLNUMBERS WITH THEIR NUMBER OF PRESENTS. EX:{'15001F0037': 7, '15001F0052': 1, '15001F0044': 2}
                d = {x:rolls.count(x) for x in rolls}
                print(d)
                return render_template('by_group.html', allValues = dd, val_len = val_len, gp = gp, days = day_no, names_dic = name_dic)
        return render_template('login.html', error = error)
    return "Method is not a POST"


if __name__ == '__main__' :
    first_app.run(host = '0.0.0.0')
