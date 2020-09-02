# -*- coding: utf-8 -*-
"""
Created on Sat Jul 25 14:04:23 2020

@author: josure
"""

from flask import Flask,render_template,url_for, request, session, redirect, Response
import pandas as pd 

from sklearn.feature_extraction.text import CountVectorizer
from sklearn.naive_bayes import MultinomialNB

from flask_mysqldb import MySQL
import MySQLdb.cursors
from fpdf import FPDF


app = Flask (__name__)

app.secret_key = 'your secret key'

# Enter your database connection details below
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'udom'

# Intialize MySQL
mysql = MySQL(app)

@app.route('/logout')
def logout():
    # Remove session data, this will log the user out
   session.pop('loggedin', None)
   session.pop('id', None)
   session.pop('email', None)
   # Redirect to login page
   return redirect(url_for('log'))

@app.route('/views.http')
def view():
    return render_template("views.html")

@app.route('/admin', methods=['GET', 'POST'])
def log():
    # Output message if something goes wrong...
    msg = ''
    # Check if "username" and "password" POST requests exist (user submitted form)
    if request.method == 'POST' and 'email' in request.form and 'password' in request.form:
        # Create variables for easy access
        email = request.form['email']
        password = request.form['password']
        # Check if account exists using MySQL
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM login WHERE email = %s AND password = %s', (email, password,))
        # Fetch one record and return result
        account = cursor.fetchone()
        # If account exists in accounts table in out database
        if account:
            # Create session data, we can access this data in other routes
            session['loggedin'] = True
            session['id'] = account['id']
            session['email'] = account['email']
            # Redirect to home page
            return render_template('adminInside.html')
        else:
            # Account doesnt exist or username/password incorrect
            msg = 'Incorrect email/password!'
    # Show the login form with message (if any)
    return render_template('login.html', msg=msg)


@app.route("/")
def index():
    
    return render_template("index.html")

@app.route("/login")
def login():
    
    return render_template("login.html")
@app.route('/predict',methods=['POST'])
def predict():
    df= pd.read_csv("co.csv", encoding="latin-1")
    # Features and Labels
    df['label'] = df['tag'].map({'academic': 0, 'hospital': 1, 'library':2, 'cafeteria':3})
    X = df['post']
    y = df['label']
    # Extract Feature With CountVectorizer
    cv = CountVectorizer()
    X = cv.fit_transform(X) # Fit the Data
    from sklearn.model_selection import train_test_split
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.33, random_state=42)
    #Naive Bayes Classifier
    from sklearn.naive_bayes import MultinomialNB
    clf = MultinomialNB()
    clf.fit(X_train,y_train)
    clf.score(X_test,y_test)
    if request.method == 'POST':
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        
        message = request.form['message']
        data = [message]
        vect = cv.transform(data).toarray()
        my_prediction = clf.predict(vect)
        
    if my_prediction == 0:
        cursor.execute("INSERT INTO academic(suggestion) VALUES (%s)", [message])
        mysql.connection.commit()
    elif my_prediction == 1:
        cursor.execute("INSERT INTO hospital(suggestion) VALUES (%s)", [message])
        mysql.connection.commit()
    elif my_prediction == 2:
        cursor.execute("INSERT INTO library(suggestion) VALUES (%s)", [message])
        mysql.connection.commit()
    elif my_prediction == 3:
        cursor.execute("INSERT INTO cafeteria(suggestion) VALUES (%s)", [message])
        mysql.connection.commit()
        
    msg = 'Thank you for suggesting'    
        
    
    return render_template("userSuggest.html", msg=msg)

@app.route('/getfeed', methods=['GET'])
def getf():
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT * FROM feedback')
    data = cursor.fetchall()
    
    
    #data from database
    print(data)
    
    return render_template('feeds.html', data=data)

@app.route('/views', methods=['GET'])
def display():
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT * FROM cafeteria')
    data = cursor.fetchall()
    cursor.execute('SELECT * FROM academic')
    d = cursor.fetchall()
    cursor.execute('SELECT * FROM hospital')
    ds = cursor.fetchall()
    
    
    #data from database
    print(ds)
    
    return render_template('views.html', ds=ds, data=data, d=d)

@app.route('/viewlib', methods=['GET'])
def displib():
     cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
     cursor.execute('SELECT * FROM library')
     dl = cursor.fetchall()
    
    #data from database
     print(dl)
    
     return render_template('viewlibr.html', dl=dl)


@app.route('/viewcafe', methods=['GET'])
def viewcafe():
     cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
     cursor.execute('SELECT * FROM cafeteria')
     data = cursor.fetchall()
    
    #data from database
     print(data)
    
     return render_template('viewcafe.html', data=data)

@app.route('/viewacad', methods=['GET'])
def viewacad():
     cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
     cursor.execute('SELECT * FROM academic')
     dp = cursor.fetchall()
    
    #data from database
     print(dp)
    
     return render_template('viewacad.html', dp=dp)
 
@app.route('/feedprocessing', methods=['GET','POST'])
def feedpro():
    
    if request.method == 'POST':
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        message = request.form['message']
        cursor.execute("INSERT INTO feedback(feedback) VALUES (%s)", [message])
        mysql.connection.commit()
        
        msg="feedback provided successfully"
        
        return render_template('adminInside.html', msg=msg)


@app.route("/back")
def back():
    return render_template("index.html")

@app.route("/adminInside")
def adminInside():
    
    return render_template("adminInside.html")

@app.route("/userSuggest")
def userSuggest():
    
    return render_template("userSuggest.html")

@app.route('/download/report/pdf')
def download_report():
	
	
	try:
		
		cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
		
		cursor.execute("SELECT id, suggestion FROM library")
		result = cursor.fetchall()
		
		pdf = FPDF()
		pdf.add_page()
		
		page_width = pdf.w - 2 * pdf.l_margin
		pdf.set_font('Times','B',14.0) 
		pdf.cell(page_width, 0.0, 'Library Data', align='C')
		pdf.ln(10)

		pdf.set_font('Courier', '', 12)
		
		col_width = page_width/4
		
		pdf.ln(1)
		
		th = pdf.font_size
		
		for row in result:
			pdf.cell(col_width, th, str(row['id']), border=1)
			pdf.cell(col_width, th, row['suggestion'], border=1)

           
			
			pdf.ln(th)
		
		pdf.ln(10)
		
		pdf.set_font('Times','',10.0) 
		pdf.cell(page_width, 0.0, '- end of report -', align='C')
		
		return Response(pdf.output(dest='S').encode('latin-1'), mimetype='application/pdf', headers={'Content-Disposition':'attachment;filename=library_report.pdf'})
	except Exception as e:
		print(e)
	return render_template("reporty.html")     

@app.route('/reportyy')
def reporty():
    return render_template("reporty.html")


    
@app.route('/feed', methods=['GET','POST'])
def feed():
    
    return render_template('feeds.html')


if __name__ == '__main__':
	app.run()