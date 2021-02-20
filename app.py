from flask import Flask, render_template,url_for,redirect,request,session,flash,Markup
from flask_mysqldb import MySQL
from werkzeug.security import generate_password_hash,check_password_hash
import yaml
import os
import math

app = Flask(__name__)

#Config a db
db = yaml.load(open('db.yaml'))
app.config['MYSQL_HOST'] = db['mysql_host']
app.config['MYSQL_USER'] = db['mysql_user']
app.config['MYSQL_PASSWORD'] = db['mysql_password']
app.config['MYSQL_DB'] = db['mysql_db']
app.config['MYSQL_PORT'] = 3307
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'
mysql = MySQL(app)

app.config['SECRET_KEY'] = os.urandom(24)

@app.route('/')
def index():

    return render_template('index1.html')

@app.route('/admin_reg', methods=['GET','POST'])
def admin_reg():
    if request.method=='POST':
        form = request.form
        admin_id = form['admin_id']
        admin_name = form['admin_name']
        admin_password = form['admin_password']
        if admin_password!=form['c_password']:
            flash('Passwords do not match! Try again', 'danger')
            return render_template('admin_reg.html')
        hash_pass = generate_password_hash(admin_password)
        cur = mysql.connection.cursor()
        cur.callproc('add_admin',(admin_id,admin_name,hash_pass))       #call to procedure
        mysql.connection.commit()
        cur.close()
        flash('Registration successful! Please login','success')
        return redirect(url_for('admin_login'))

    return render_template('admin_reg.html')

@app.route('/admin_login', methods=['GET','POST'])
def admin_login():
    if request.method=='POST':
        form = request.form
        admin_id = form['admin_id']
        admin_password = form['admin_password']
        cur = mysql.connection.cursor()
        result = cur.execute("select * from admin where admin_id=%s",[admin_id])
        if result > 0:
            data = cur.fetchone()
            db_password = data['admin_password']
            if check_password_hash(db_password,admin_password):
                session['login'] = True
                session['name'] = data['admin_name']
                session['admin_id'] = data['admin_id']
                flash('Welcome ' + session['name'] +'! You have been successfully logged in', 'success')
            else:
                cur.close()
                flash('Password does not match', 'danger')
                return render_template('admin_login.html')
        else:
            cur.close()
            flash('User not found', 'danger')
            return render_template('admin_login.html')
        cur.close()
        return redirect('/admin_profile')
    return render_template('admin_login.html')

@app.route('/admin_profile', methods = ['GET','POST'])
def admin_profile():
    if request.method =='POST':
        admin_id = session['admin_id']
        form = request.form
        class_name = form['class_name']
        cur = mysql.connection.cursor()
        result = cur.execute("select class_name from class where class_name=%s",[class_name])
        if result > 0:
            cur.close()
            flash("class name already exists",'danger')
            return redirect('/admin_profile')
        else:
            cur.execute("insert into class(class_name,admin_id) values(%s,%s)",(class_name,admin_id))
            mysql.connection.commit()
            flash("Class added successfully",'success')
            return render_template('admin_profile.html')
    return render_template('admin_profile.html')


@app.route('/register', methods=['GET','POST'])
def register():
    if request.method=='POST':
        form = request.form
        name = form['name']
        email = form['email']
        password = form['password']
        phone = form['phone']
        reg_no = form['reg_no']
        if password!=form['c_password']:
            flash('Passwords do not match! Try again', 'danger')
            return render_template('reg.html')
        cur = mysql.connection.cursor()
        result = cur.execute("select reg_id from student where reg_id=%s", [reg_no])
        if result > 0:
            cur.execute("insert into parent(p_name, email, password, phone_no, reg_id) values(%s, %s, %s, %s, %s)",(name,email,generate_password_hash(password),phone,reg_no))
            mysql.connection.commit()
            cur.close()
            flash('Registration successful! Please login','success')
            return redirect(url_for('login'))
        else:
            cur.close()
            flash('Invalid Registration No','danger')
            return render_template('reg.html')

    return render_template('reg.html')



@app.route('/tregister', methods=['GET','POST'])
def tregister():
    if request.method =='POST':
        form = request.form
        t_name = form['t_name']
        t_phone = form['t_phone']
        t_address = form['t_address']
        t_type = form['t_type']
        t_class = form['t_class']
        t_subject = form['t_subject']
        t_class_sub1 = form['t_class_sub1']
        t_class_sub2 = form['t_class_sub2']
        t_password = form['t_password']

        #For drop down data
        cur = mysql.connection.cursor()
        cur.execute("select *from subject")
        subjects = cur.fetchall()
        cur.execute("select *from class")
        classes = cur.fetchall()
        cur.close()

        if t_password!=form['c_password']:
            flash('Passwords do not match! Try again', 'danger')
            return render_template('t_reg.html',classes = classes,subjects = subjects)
        cur = mysql.connection.cursor()
        result1 = cur.execute("select *from class_subjects where class_id=%s and sub_id=%s",(t_class_sub1,t_subject))
        result2 = cur.execute("select *from class_subjects where class_id=%s and sub_id=%s",(t_class_sub2,t_subject))
        if result1 > 0 and result2 > 0:
            cur.close()
            flash('Teacher already assigned to class or subject','danger')
            return render_template('t_reg.html',classes = classes,subjects = subjects)
        else:
            if t_type == 'class teacher':
                result = cur.execute("select class_id from teacher where class_id=%s",[t_class])
                if result > 0:
                    cur.close()
                    flash('Class teacher already exists','danger')
                    return render_template('t_reg.html',classes = classes,subjects = subjects)
                else:
                    cur.execute("insert into teacher(t_name, phone, t_address, type, t_password, sub_id, class_id) values(%s,%s,%s,%s,%s,%s,%s)",(t_name,t_phone,t_address,t_type,generate_password_hash(t_password),t_subject,t_class))
                    mysql.connection.commit()
            else:
                cur.execute("insert into teacher(t_name, phone, t_address, type, t_password, sub_id) values(%s,%s,%s,%s,%s,%s)",(t_name,t_phone,t_address,t_type,generate_password_hash(t_password),t_subject))
                mysql.connection.commit()

            cur.execute("insert into class_subjects(class_id,sub_id) values(%s,%s)",(t_class_sub1,t_subject))
            mysql.connection.commit()
            cur.execute("insert into class_subjects(class_id,sub_id) values(%s,%s)",(t_class_sub2,t_subject))
            mysql.connection.commit()
            cur.execute("select t_id from teacher where phone=%s",[t_phone])
            data_teacher = cur.fetchone()
            cur.execute("insert into teaches(class_id,t_id) values(%s,%s)",(t_class_sub1,data_teacher['t_id']))
            mysql.connection.commit()
            cur.execute("insert into teaches(class_id,t_id) values(%s,%s)",(t_class_sub2,data_teacher['t_id']))
            mysql.connection.commit()
            cur.close()
            flash('Registration successful! Your id is ' + str(data_teacher['t_id']) + ' Please login','success')
            return redirect('/tlogin')
    else:
        cur = mysql.connection.cursor()
        cur.execute("select *from subject")
        subjects = cur.fetchall()
        cur.execute("select *from class")
        classes = cur.fetchall()
        cur.close()
        return render_template('t_reg.html', classes = classes,subjects = subjects)
    

@app.route('/login', methods=['GET','POST'])
def login():
    if request.method=='POST':
        form = request.form
        reg_id = form['reg_id']
        password = form['password']
        cur = mysql.connection.cursor()
        result = cur.execute("select * from parent where reg_id=%s", [reg_id])
        if result > 0:
            data = cur.fetchone()
            db_password = data['password']
            if check_password_hash(db_password, password):
                cur.execute("select s_class(%s) as class_id",[data['reg_id']])              #call to function
                class_id = cur.fetchone()
                session['class_id'] = class_id['class_id']
                session['login'] = True
                session['name'] = data['p_name']
                session['reg_id'] = data['reg_id']
                flash('Welcome ' + session['name'] +'! You have been successfully logged in', 'success')
            else:
                cur.close()
                flash('Password does not match', 'danger')
                return render_template('login.html')
        else:
            cur.close()
            flash('User not found', 'danger')
            return render_template('login.html')
        cur.close()
        return redirect('/profile')

    return render_template('login.html')


@app.route('/tlogin', methods=['GET','POST'])
def tlogin():
    if request.method=='POST':
        form = request.form
        t_id = form['t_id']
        t_password = form['t_password']
        cur = mysql.connection.cursor()
        result = cur.execute("select * from teacher where t_id=%s", [t_id])
        if result > 0:
            data = cur.fetchone()
            db_password = data['t_password']
            if check_password_hash(db_password, t_password):
                cur.execute("select type from teacher where t_id=%s", [t_id])
                t_type = cur.fetchone()
                session['login'] = True
                session['t_id'] = data['t_id']
                session['sub_id'] = data['sub_id']
                flash('Welcome ! You have been successfully logged in', 'success')
            else:
                cur.close()
                flash('Password does not match', 'danger')
                return render_template('t_login.html')
        else:
            cur.close()
            flash('User not found', 'danger')
            return render_template('t_login.html')
        cur.close()
        if t_type['type'] == "class teacher":   
            return redirect(url_for('show_students'))
        else:
            return redirect(url_for('manage_exams'))

    return render_template('t_login.html')
        

@app.route('/profile')
def profile():
    reg_id = session['reg_id']
    cur = mysql.connection.cursor()
    cur.execute("select student.reg_id,student.name,class.class_name,teacher.t_name from student inner join class on student.class_id=class.class_id inner join teacher on class.class_id=teacher.class_id where reg_id=%s;", [reg_id])
    data = cur.fetchone()
    #print(data)
    return render_template('profile.html', data = data)



@app.route('/add_student', methods=['GET','POST'])
def add_student():
    if request.method == 'POST':
        form =request.form
        s_roll_no = form['s_roll_no']
        s_name = form['s_name']
        s_dob = form['s_dob']
        s_address = form['s_address']
        teacher_id = session['t_id']
        cur = mysql.connection.cursor()
        cur.execute("select class_id from teacher where t_id=%s",[teacher_id])
        cid = cur.fetchone()
        result = cur.execute("select roll_no from student where roll_no=%s and class_id=%s",(s_roll_no,cid['class_id']))
        if result > 0:
            cur.close()
            flash('Roll No already exists','danger')
            return redirect('/add_student')
        else:
            cur.execute("insert into student(roll_no, name, dob, address, class_id ) values(%s,%s,%s,%s,%s)",(s_roll_no,s_name,s_dob,s_address,cid['class_id']))
            mysql.connection.commit()
            cur.close()
            flash('Student added successfully','success')
            return redirect('/add_student')

    return render_template('add_student.html')


@app.route('/edit_student/<int:sid>', methods=['GET','POST'])
def edit_student(sid):
    if request.method == 'POST':
        form =request.form
        s_roll_no = form['s_roll_no']
        s_name = form['s_name']
        s_dob = form['s_dob']
        s_address = form['s_address']
        cur = mysql.connection.cursor()
        cur.execute("update student set roll_no=%s, name=%s, dob=%s, address=%s where reg_id=%s",(s_roll_no,s_name,s_dob,s_address,sid))
        mysql.connection.commit()
        cur.close()
        flash('Student edited successfully','success')
        return redirect('/show_students')
    else:
        cur = mysql.connection.cursor()
        cur.execute("select *from student where reg_id=%s",[sid])
        student = cur.fetchone()
        student_form = {}
        student_form['roll_no'] = student['roll_no']
        student_form['name'] = student['name']
        student_form['dob'] = student['dob']
        student_form['address'] = student['address']
        cur.close()
        return render_template('edit_student.html',student_form = student_form)



@app.route('/show_students')
def show_students():
    teacher_id = session['t_id']
    cur = mysql.connection.cursor()
    result = cur.execute("select student.reg_id,student.roll_no,student.name,student.dob,student.address from student inner join teacher on student.class_id=teacher.class_id where t_id=%s",[teacher_id])
    if result > 0:
        students = cur.fetchall()
        return render_template('show_students.html',students = students)
    else:
        return render_template('show_students.html',students = None)

    cur.close()


@app.route('/delete_student/<int:sid>')
def delete_student(sid):
    cur = mysql.connection.cursor()
    cur.execute("delete from student where reg_id=%s",[sid])            #trigger for deletion
    mysql.connection.commit()
    cur.close()
    flash('Student deleted successfully','success')
    return redirect('/show_students')


@app.route('/student_activity')
def student_activity():
    teacher_id = session['t_id']
    cur = mysql.connection.cursor()
    result = cur.execute("select student.reg_id,student.roll_no,student.name from student inner join teacher on student.class_id=teacher.class_id where t_id=%s",[teacher_id])
    if result > 0:
        students = cur.fetchall()
        return render_template('student_activity.html',students = students)
    else:
        return render_template('student_activity.html',students = None)

    cur.close()


@app.route('/add_activities', methods = ['GET','POST'])
def add_activities():
    if request.method =='POST':
        form = request.form
        a_name = form['a_name']
        category = form['category']
        cur = mysql.connection.cursor()
        result = cur.execute("select a_name from activities where a_name=%s",[a_name])
        if result > 0:
            cur.close()
            flash('Activity already exists','danger')
            return redirect('/add_activities')
        else:
            cur.execute("insert into activities(a_name,category) values(%s,%s)",(a_name,category))
            mysql.connection.commit()
            cur.close()
            flash('Activity added successfully','success')
            return redirect('/add_activities')
    return render_template('add_activities.html')


@app.route('/s_activity/<int:sid>', methods = ['GET','POST'])
def s_activity(sid):
    cur = mysql.connection.cursor()
    if request.method =='POST':
        form = request.form
        a_id = form['a_id']
        position = form['position']
        result = cur.execute("select *from student_activities where reg_id=%s and a_id=%s",(sid,a_id))
        if result > 0:
            cur.close()
            flash('Record already exists','danger')
            return redirect(url_for('s_activity',sid = sid))
        else:
            cur.execute("insert into student_activities(reg_id,a_id,position) values(%s,%s,%s)",(sid,a_id,position))
            mysql.connection.commit()
            flash('Activity added successfully','success')
            return redirect('/student_activity')
    else:
        cur.execute("select a_id,a_name from activities")
        activities = cur.fetchall()
        
        cur.close()
        return render_template('s_activity.html',activities = activities,sid = sid)



@app.route('/add_exam', methods = ['GET','POST'])
def add_exam():
    if request.method =='POST':
        admin_id = session['admin_id']
        form = request.form
        exam_name = form['exam_name']
        exam_date = form['exam_date']
        exam_marks = form['exam_marks']
        #exam_class = form['exam_class']
        cur = mysql.connection.cursor()

        result = cur.execute("select e_name from exams where e_name=%s",[exam_name])
        if result > 0:
            cur.close()
            flash("Exam already exists",'danger')
            return redirect('/add_exam')
        else:
            cur.execute("insert into exams(e_name, exam_date, tot_marks, admin_id) values(%s,%s,%s,%s)",(exam_name,exam_date,exam_marks,admin_id))
            mysql.connection.commit()
            flash("Exam added successfully",'success')
            return render_template('add_exam.html')
        

    return render_template('add_exam.html')


@app.route('/add_subject', methods = ['GET','POST'])
def add_subject():
    if request.method =='POST':
        admin_id = session['admin_id']
        form = request.form
        sub_name = form['sub_name']
        cur = mysql.connection.cursor()
        result = cur.execute("select sub_name from subject where sub_name=%s",[sub_name])
        if result > 0:
            cur.close()
            flash("Subject already exists",'danger')
            return redirect('/add_subject')
        else:
            cur.execute("insert into subject(sub_name,admin_id) values(%s,%s)",(sub_name,admin_id))
            mysql.connection.commit()
            flash("Subject added successfully",'success')
            return render_template('add_subject.html')
    return render_template('add_subject.html')

@app.route('/class_exams', methods = ['GET','POST'])
def class_exams():
    if request.method =='POST':
        #admin_id = session['admin_id']
        form = request.form
        e_id = form['e_id']
        class_id = form.getlist('classes')

        cur = mysql.connection.cursor()
        for n in range(len(class_id)):
            cur.execute("insert into class_exams(class_id,id) values(%s,%s)",(class_id[n],e_id))
            mysql.connection.commit()
        flash('Exam assigned successfully','success')
        cur.close()
        cur = mysql.connection.cursor()
        cur.execute("select *from exams")
        e_options = cur.fetchall()
        cur.execute("select *from class")
        c_options = cur.fetchall()
        return render_template('class_exams.html', c_options = c_options,e_options = e_options)
    else:
        cur = mysql.connection.cursor()
        cur.execute("select *from exams")
        e_options = cur.fetchall()
        cur.execute("select *from class")
        c_options = cur.fetchall()
        return render_template('class_exams.html',c_options = c_options,e_options = e_options)


@app.route('/manage_exams', methods = ['GET','POST'])
def manage_exams():
    t_id = session['t_id']
    if request.method =='POST':
        form = request.form
        exam_id = form['exam_id']
        class_id = form.getlist('class_id')
        c1 = class_id[0]
        c2 = class_id[1]
        return redirect(url_for('subject_students',eid=exam_id, c1=c1, c2=c2))
    else:
        cur = mysql.connection.cursor()
        cur.execute("select id,e_name from exams where id in (select distinct class_exams.id from class_exams inner join teaches on class_exams.class_id=teaches.class_id where t_id=%s)",[t_id])
        exams = cur.fetchall()
        cur.execute("select class_id,class_name from class where class_id in (select class_id from teaches where t_id=%s)",[t_id])
        classes = cur.fetchall()
        cur.close()
        flash('Fill form to add marks','info')
        return render_template('manage_exams.html',exams = exams, classes = classes)


@app.route('/subject_students/<int:eid>/<int:c1>/<int:c2>')
def subject_students(eid,c1,c2):
    t_id = session['t_id']
    cur = mysql.connection.cursor()
    cur.execute("select reg_id, roll_no, name from student where class_id=%s or class_id=%s",(c1,c2))
    students = cur.fetchall()
    cur.execute("select teacher.sub_id,subject.sub_name from teacher inner join subject on teacher.sub_id=subject.sub_id where t_id=%s",[t_id])
    subject = cur.fetchone()
    cur.close()
    return render_template('subject_students.html',students = students,eid = eid,c1 = c1,c2 = c2,subject = subject)


@app.route('/add_marks/<int:reg_id>/<int:eid>/<int:c1>/<int:c2>', methods = ['GET','POST'])
def add_marks(reg_id,eid,c1,c2):
    t_id = session['t_id']
    sub_id = session['sub_id']
    if request.method == 'POST':
        form = request.form
        sub_id = form['sub_id']
        marks = form['marks']
        cur = mysql.connection.cursor()
        cur.execute("insert into score_table(reg_id,sub_id,id,marks) values(%s,%s,%s,%s)",(reg_id,sub_id,eid,marks))
        mysql.connection.commit()
        cur.close()
        flash('Marks added successfully','success')
        return redirect(url_for('subject_students',eid=eid, c1=c1, c2=c2))
    else:
        cur = mysql.connection.cursor()
        result = cur.execute("select *from score_table where reg_id=%s and id=%s and sub_id=%s",(reg_id,eid,sub_id))
        if result == 0:
            cur.execute("select subject.sub_id from subject inner join teacher on subject.sub_id=teacher.sub_id where t_id=%s",[t_id])
            subject = cur.fetchone()
            cur.execute("select tot_marks from exams where id=%s",[eid])
            tot_marks = cur.fetchone()
            cur.close()
            return render_template('add_marks.html',subject = subject,tot_marks=tot_marks) 
        else:
            cur.close()
            flash('Marks already added','danger')
            return redirect(url_for('subject_students',eid=eid, c1=c1, c2=c2))


@app.route('/show_marks/<int:eid>/<int:c1>/<int:c2>')
def show_marks(eid,c1,c2):
    sub_id = session['sub_id']
    t_id = session['t_id']
    cur = mysql.connection.cursor()
    cur.execute("select e_name,tot_marks from exams where id=%s",[eid])
    exam = cur.fetchone()
    cur.execute("select teacher.sub_id,subject.sub_name from teacher inner join subject on teacher.sub_id=subject.sub_id where t_id=%s",[t_id])
    subject = cur.fetchone()
    result = cur.execute("select student.reg_id,student.name,score_table.marks from student inner join score_table on student.reg_id=score_table.reg_id where class_id in (%s,%s) and id=%s and sub_id=%s",(c1,c2,eid,sub_id))
    if result > 0:
        students = cur.fetchall()
        max_marks = 0
        toppers = []
        for x in students:
            if x['marks'] > max_marks:
                max_marks = x['marks']

        for y in students:
            if y['marks'] == max_marks:
                toppers.append(y) 
        return render_template('show_marks.html',students=students,eid=eid,exam=exam,c1=c1,c2=c2,subject = subject,toppers=toppers)
    else:
        return render_template('show_marks.html',students=None,exam=exam,subject = subject)
    cur.close()
   

@app.route('/edit_marks/<int:reg_id>/<int:eid>/<int:c1>/<int:c2>', methods = ['GET','POST'])
def edit_marks(reg_id,eid,c1,c2):
    sub_id = session['sub_id']
    if request.method == 'POST':
        form = request.form
        reg_id = form['reg_id']
        name = form['name']
        marks = form['marks']
        cur = mysql.connection.cursor()
        cur.execute("update score_table set marks=%s where reg_id=%s and id=%s and sub_id=%s",(marks,reg_id,eid,sub_id))
        mysql.connection.commit()
        cur.close()
        flash('Marks updated seccessfully','success')
        return redirect(url_for('show_marks',eid=eid,c1=c1,c2=c2))
    else:
        cur = mysql.connection.cursor()
        cur.execute("select student.reg_id,student.name,score_table.marks from student inner join score_table on student.reg_id=score_table.reg_id where score_table.reg_id=%s and score_table.id=%s and score_table.sub_id=%s",(reg_id,eid,sub_id))
        student = cur.fetchone()
        cur.execute("select tot_marks from exams where id=%s",[eid])
        tot_marks = cur.fetchone()
        cur.close()
        return render_template('edit_marks.html',student=student,tot_marks=tot_marks)




@app.route('/exams')
def exams():
    reg_id = session['reg_id']
    cur = mysql.connection.cursor()
    cur.execute("select id,e_name,exam_date,tot_marks from exams where id in (select class_exams.id from student inner join class_exams on student.class_id=class_exams.class_id where reg_id=%s)",[reg_id])
    exams = cur.fetchall()
    cur.close()
    return render_template('exams.html',exams = exams)


@app.route('/result/<int:eid>')
def result(eid):
    reg_id = session['reg_id']
    cur = mysql.connection.cursor()
    result = cur.execute("select *from score_table where reg_id=%s and id=%s",(reg_id,eid))
    if result == 0:
        cur.close()
        flash('Result for this exam is not declared yet','info')
        return redirect('/exams')
    cur.execute("select student.reg_id,student.name,class.class_name from student inner join class on student.class_id=class.class_id where reg_id=%s",[reg_id])
    student = cur.fetchone()
    cur.execute("select e_name,tot_marks from exams where id=%s",[eid])
    exam = cur.fetchone()
    session['tot_marks'] = exam['tot_marks']
    cur.execute("select score_table.sub_id,score_table.marks,subject.sub_name from score_table inner join subject on score_table.sub_id=subject.sub_id where reg_id=%s and id=%s",(reg_id,eid))
    marks = cur.fetchall()
    #print(marks)
    #print(type(marks))
    result = {}
    sum_f = 0
    sum_o = 0
    for mark in marks:
        per = math.trunc((mark['marks']*100)/session['tot_marks'])
        if per>=91:
            mark['grade'] = 'A+'
            mark['remark'] = 'Excellent'
        elif per>=81:
            mark['grade'] = 'A'
            mark['remark'] = ' Very Good'
        elif per>=71:
            mark['grade'] = 'B+'
            mark['remark'] = 'Good'
        elif per>=61:
            mark['grade'] = 'B'
            mark['remark'] = 'Average'
        elif per>=51:
            mark['grade'] = 'C'
            mark['remark'] = 'Needs Improvement'
        else:
            mark['grade'] = 'D'
            mark['remark'] = 'Fail'
        sum_f+= session['tot_marks']
        sum_o+= mark['marks']
    result['fmarks'] = sum_f
    result['omarks'] = sum_o
    percent = math.trunc((result['omarks']*100)/result['fmarks'])
    if percent>=91:
        result['fgrade'] = 'A+'
    elif percent>=81:
        result['fgrade'] = 'A'
    elif percent>=71:
        result['fgrade'] = 'B+'
    elif percent>=61:
        result['fgrade'] = 'B'
    elif percent>=51:
        result['fgrade'] = 'C'
    else:
        result['fgrade'] = 'D'

    #print(marks)
    cur.close()
    return render_template('result.html',student = student, exam = exam, marks = marks,result = result)


@app.route('/view_activity')
def view_activity():
    reg_id = session['reg_id']
    cur = mysql.connection.cursor()
    result = cur.execute("select activities.a_name,activities.category,student_activities.position from activities inner join student_activities on activities.a_id=student_activities.a_id where reg_id=%s",[reg_id])
    if result > 0:
        activities = cur.fetchall()
        return render_template('view_activity.html',activities = activities)
    else:
        return render_template('view_activity.html',activities = None)

    cur.close()
   
    

@app.route('/subjects')
def subjects():
    #reg_id = session['reg_id']
    class_id = session['class_id']
    cur = mysql.connection.cursor()
    cur.execute("select teacher.sub_id,teacher.t_name,subject.sub_name from teacher inner join subject on teacher.sub_id=subject.sub_id  where t_id in ( select t_id from teaches where class_id=%s)",[class_id])
    subjects = cur.fetchall()
    cur.close()
    return render_template('subjects.html',subjects = subjects)


@app.route('/about_us')
def about_us():
    return render_template('about_us.html')
  
@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

@app.route('/log')
def log():
    reg_id = session['reg_id']
    cur = mysql.connection.cursor()
    lst = [1,2,3,4,5]
    #x = cur.execute("select *from score_table where reg_id=%s",[reg_id])
    #if x > 0:
    #ids = cur.fetchall()
    cur.execute("select id,e_name,exam_date,tot_marks from exams where id in (select class_exams.id from student inner join class_exams on student.class_id=class_exams.class_id where reg_id=%s and id in (%s))",(reg_id,lst))
    exams = cur.fetchall()
    print(exams)


    
    


    


if __name__ == '__main__':
    app.run(debug=True)