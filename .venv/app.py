# Tiny Concert Project
# By Myles Cruz 
# Project originally created for class at St. Norbert College
#   CSCI 322: Programming Languages, Dr. Ben Geisler
# Created: December 4, 2020
# Last Modified: November 07, 2022

from flask import Flask, flash, render_template, session, redirect, url_for, request
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired
from concerts import *
from seat import *
from user import *
import os.path
import re
import pprint

app = Flask(__name__)
app.config['SECRET_KEY'] = 'foo'

from flask_bootstrap import Bootstrap
bootstrap = Bootstrap(app)

# global variables
date = "None"
A_INDEX = 0
B_INDEX = 1
C_INDEX = 2
D_INDEX = 3
E_INDEX = 4
ROW_A_PRICE = 50
ROW_B_PRICE = 45
ROW_C_PRICE = 40
ROW_D_PRICE = 35
ROW_E_PRICE = 30
NUM_ROWS = 5
NUM_SEATS = 10
ROW_A = []
ROW_B = []
ROW_C = []
ROW_D = []
ROW_E = []
SEATS = [ROW_A,ROW_B,ROW_C,ROW_D,ROW_E]
EMPTY = "/static/empty.png"
RESERVED = "/static/occupied.png"
FIRST_NAME_INDEX = 0
LAST_NAME_INDEX = 1
EMAIL_INDEX = 2
PASSWORD_INDEX = 3

# Registration form: allows user to register for the website
class RegisterForm(FlaskForm):
    firstName = StringField('First Name:', validators=[DataRequired()])
    lastName = StringField('Last Name:', validators=[DataRequired()])
    email = StringField('Email:', validators=[DataRequired()])
    password = StringField('Password: ', validators=[DataRequired()])
    submit = SubmitField('Register')

# Login form: allows user to login into website to access their information and check reservations
class LoginForm(FlaskForm):
    email = StringField('Email:', validators=[DataRequired()])
    password = PasswordField('Password: ', validators=[DataRequired()])
    login = SubmitField('Login')

# Transaction form: user gives credit card information to process a transaction
# make creditCard field a 16-digit validator
# make expirationDate a 4-digit/1-character validator
# make cvv field a 3-digit validator
class TransactionForm(FlaskForm):
    creditCard = StringField('Credit Card Number: ', validators=[DataRequired()])
    expirationDate = StringField('Expiration Date (MM/YY): ', validators=[DataRequired()])
    cvv = StringField('CVV: ', validators=[DataRequired()])
    submit = SubmitField('Place Order')

# Cancel reservation form: allows user to cancel any current reservations
class ConfirmationForm(FlaskForm):
    password = PasswordField('Password: ', validators=[DataRequired()])
    confirm = SubmitField('Confirm')

# Home page
@app.route("/", methods = ['GET'])
def index():
    session.clear()
    return redirect(url_for('concerts'))
    #return render_template('index.html', name=session.get('firstName'))

# Login for an existing user
@app.route("/login", methods=['GET', 'POST'])
def login():
    loginForm = LoginForm()

    if loginForm.validate_on_submit():
        userFile = "data/users/" + loginForm.email.data + "/" + "info.txt"

        try:
            open(userFile)
        except IOError:
            flash('Email address not found. Please create a new account','error')
            return redirect(url_for('login'))
        
        with open(userFile,"r") as f:
            line = f.readline()
            userDetails = line.split()
            givenEmail = loginForm.email.data
            givenPassword = loginForm.password.data
            
            # print("Given e: ", givenEmail, " given p: ", givenPassword)
            # print("Known e: ", userDetails[EMAIL_INDEX], " known p: ", userDetails[PASSWORD_INDEX])

            if (givenEmail == userDetails[EMAIL_INDEX]) & (givenPassword == userDetails[PASSWORD_INDEX]):
                
                user = User(userDetails[FIRST_NAME_INDEX], userDetails[LAST_NAME_INDEX], userDetails[EMAIL_INDEX], userDetails[PASSWORD_INDEX])
        
                session['email'] = user.getEmail()
                session['password'] = user.getPassword()
                session['firstName'] = user.getFirstName()
                session['lastName'] = user.getLastName()
                flash('Logged in successfully!','info')

                if session.get('date') is not None:
                    return redirect(url_for('seatview', date = session.get('date')))
                else:
                    return redirect(url_for('concerts'))
            else:
                flash('Incorrect login credentials. Please try again to login!','error')
                return redirect(url_for('login'))

    return render_template('login.html', loginForm = loginForm, name = session.get('firstName'))  

# Logs out user by clearing all session data           
@app.route("/logout", methods=['GET','POST'])
def logout():
    session.clear()

    flash("Logout successful!")
    return redirect(url_for('login'))

# Registration for a new user
@app.route("/register", methods=['GET','POST'])
def register():
    registerForm = RegisterForm()
    if registerForm.validate_on_submit():
        userFile = "data/users/" + registerForm.email.data
        isUser = os.path.isdir(userFile)  

        if isUser: 
            flash('The email address you entered is already registered','error')
            return redirect(url_for('login'))
        else:
            StoreUser(registerForm)

            flash('Registered successfully!','info')
            return redirect(url_for('concerts'))
    
    return render_template('register.html', registerForm = registerForm)

# Displays the upcoming concerts
@app.route("/concerts")
def concerts():
    concerts = Concerts()
    musicians = []
    dates = []
    times = []
    images = []

    for key, value in concerts.concertsDict.items():
        dates.append(key)
        musicians.append(value.getMusician())
        times.append(value.getTime())
        images.append(value.getImage())

    #print("Concerts Dictionary: ", dates, musicians, times, images)

    return render_template('concerts.html', musicians = musicians, dates = dates, times = times, images = images, name = session.get('firstName'))

# displays the a concert's seats and their availability
@app.route("/seatview", methods=['GET','POST'])
def seatview():
    global SEATS

    date = request.args.get('date')
    session['date'] = date
    musician = request.args.get('musician')

    if session.get('date') is None:
        flash('Must select a concert to view seats','error')
        return redirect(url_for('concerts'))

    SEATS = loadSeats(SEATS, date)
    print("SEATS: ")
    pprint.pprint(SEATS)

    return render_template('seatview.html', reserved = RESERVED, available = EMPTY, seats = SEATS, musician = musician, date = date, name = session.get('firstName'))

# determines which row and seat was selected and allocates the data
@app.route("/seatSelect", methods=['GET','POST'])
def seatselect():

    if session.get('email') is None:
        flash('Must login to reserve a seat','error')
        return redirect(url_for('login'))

    global SEATS
    
    #SEATS = loadSeats(SEATS)
    row = request.args.get('row')
    seat = request.args.get('seat')
    date = request.args.get('date')
    price = request.args.get('price')
    seatNum = int(seat)

    if(row == "A"):
        user = SEATS[A_INDEX][seatNum].getUser()
        if user.getEmail() == "None":
            # SEATS[A_INDEX] = reserveSeat("A", SEATS[A_INDEX], seatNum, date)
            SEATS = reserveSeatOneFile(SEATS, A_INDEX, row, seatNum, date, price)
        else:
            flash('This seat is already reserved', 'error')
            return redirect(url_for('seatview'))
    if(row == "B"):
        user = SEATS[B_INDEX][seatNum].getUser()
        if user.getEmail() == "None":
            SEATS = reserveSeatOneFile(SEATS, B_INDEX, row, seatNum, date, price)
            # SEATS[B_INDEX] = reserveSeat("B", SEATS[B_INDEX], seatNum, date)
        else:
            flash('This seat is already reserved', 'error')
            return redirect(url_for('seatview'))
    if(row == "C"):
        user = SEATS[C_INDEX][seatNum].getUser()
        if user.getEmail() == "None":
            SEATS = reserveSeatOneFile(SEATS, C_INDEX, row, seatNum, date, price)
            # SEATS[C_INDEX] = reserveSeat("C", SEATS[C_INDEX], seatNum, date)
        else:
            flash('This seat is already reserved', 'error')
            return redirect(url_for('seatview'))
    if(row == "D"):
        user = SEATS[D_INDEX][seatNum].getUser()
        if user.getEmail() == "None":
            SEATS = reserveSeatOneFile(SEATS, D_INDEX, row, seatNum, date, price)
            # SEATS[D_INDEX] = reserveSeat("D", SEATS[D_INDEX], seatNum, date)
        else:
            flash('This seat is already reserved', 'error')
            return redirect(url_for('seatview'))
    if(row == "E"):
        user = SEATS[E_INDEX][seatNum].getUser()
        if user.getEmail() == "None":
            SEATS = reserveSeatOneFile(SEATS, E_INDEX, row, seatNum, date, price)
            # SEATS[E_INDEX] = reserveSeat("E", SEATS[E_INDEX], seatNum, date)
        else:
            flash('This seat is already reserved', 'error')
            return redirect(url_for('seatview'))

    return render_template('seatselect.html', name = session.get('firstName'), row = row, seat = seatNum + 1, date = date)

# transaction page for user to checkout
@app.route("/checkout", methods = ['GET','POST'])
def checkout():
    seat = ''
    date = ''

    transactionForm = TransactionForm()
    if transactionForm.validate_on_submit():
        creditCard = transactionForm.creditCard.data
        expirationDate = transactionForm.expirationDate.data
        cvv = transactionForm.cvv.data

        if creditCard is None | expirationDate is None | cvv is None:
            flash('Invalid credit card','error')
            return redirect(url_for('checkout'))

    return render_template('checkout.html', name = session.get('firstName'), seat = seat, dates = date)

# displays a user's current reservations and allows the ability to cancel a reservation
@app.route("/reservation", methods = ['GET','POST'])
def reservation():
    if session.get('email') is None: # a user must login to view their current reservations
        flash('Must login to see your reservation') # flashes error message for next page being directed to
        return redirect(url_for('login'))

    concerts = Concerts()
    seats = []
    dates = []

    # for loop to populate the seats and dates arrays for a user to see current reservations
    for key, value in concerts.concertsDict.items():
        file = "data/users/" + session.get('email') + "/" + key + ".txt"
        try:
            open(file)
            with open(file,"r") as f:
                line = f.readline()
                seats.append(line) # populates the seats array with reserved seats 
                dates.append(key) # populates the dates array with reserved concerts
                f.close()
        except IOError: # if user has no reservation for certain date, then skips
            pass

    return render_template('reservation.html', name = session.get('firstName'), seats = seats, dates = dates, datesLength = len(dates))

# confirmation page to cancel a reservation
@app.route("/cancelreservation", methods = ['GET', 'POST'])
def cancelreservation():
    dateCancel = request.args.get('temp') # takes in date selected to cancel the reservation
    confirmationForm = ConfirmationForm()
    if confirmationForm.validate_on_submit():
        if (session.get('password') == confirmationForm.password.data):   # a user must re-enter their password to confirm cancellation
            cancelAnyReservationForUser(dateCancel)
            flash('Reservation cancelled','info') # flashes confirmation message for next page being directed to
            return redirect(url_for('reservation'))
        else:
            flash('Wrong information inputted. Please try again to cancel the reservation.', 'error') # flashes error message for next page being directed to
            return redirect(url_for('cancelreservation'))
    return render_template('cancelreservation.html', confirmationForm = confirmationForm, name=session.get('firstName'))

# Stores a new user's first name, last name, email and password in a folder
def StoreUser(form):
    user = User(form.firstName.data, form.lastName.data, form.email.data, form.password.data)

    userFolder = "data/users/" + session.get('email')
    os.mkdir(userFolder)
    file = userFolder + "/info.txt"
    with open(file,"w+") as f:
        f.write(user.getFirstName())
        f.write(" ")
        f.write(user.getLastName())
        f.write(" ")
        f.write(user.getEmail())
        f.write(" ")
        f.write(user.getPassword())
        f.close()
    
    session['firstName'] = user.getFirstName()
    session['lastName'] = user.getLastName()
    session['email'] = user.getEmail()
    session['password'] = user.getPassword()

def getSessionUser():
    firstName = session.get('firstName')
    lastName = session.get('lastName')
    email = session.get('email')
    password = session.get('password')

    user = User(firstName, lastName, email, password)
    return user

# reserves a seat for a user
# takes in the row selected, the SEATS current values, the seat number selected and the current date
def reserveSeat(letter, row, seatNum, date):
    file = "data/concerts/" + date + "/" + letter + ".txt" # file's name based on date and row of the concert 
    # a user's first and last name is now stored in the current seat chosen
    row[seatNum] = session.get('email') 
    selectedSeat = letter + str(seatNum + 1) # gives the real value of the seat number a user chose
    # seatfile: gives the txt file that will be stored in a user's folder
    seatfile = "data/users/" + session.get('email') + "/" + session.get('date') + ".txt" 

    if session.get('seat') is None: # if a user has no current seats at that date, creates new file and writes to it
        session['seat'] = selectedSeat
        with open(seatfile,"w") as f:
            f.write(selectedSeat)
            f.close()
    else: # if a user already has seats reserved, concatenate new seat with previous seats
        session['seat'] += (" " + selectedSeat)
        with open(seatfile,"a") as f:
            f.write(" ")
            f.write(selectedSeat)
            f.close()
    
    # write new data into the txt file with 
    with open(file,"w") as f:
        for i, currentData in enumerate(row):
            print(currentData)
            if isinstance(currentData, str):
                f.write(currentData)
            else:
                user = currentData.getUser()
                f.write(user.getEmail())
            f.write(" ")
   
        f.close()

    return row

def reserveSeatOneFile(SEATS, letterIndex, row, seatNum, date, price):
    pprint.pprint(SEATS)
    file = "data/concerts/" + date + "/seats.txt"
    
    user = getSessionUser()
    seat = Seat(row, seatNum + 1, user, price, RESERVED)
    SEATS[letterIndex][seatNum] = seat
    
    with open(file,"w") as f:
        for rowsIndex, row in enumerate(SEATS):
            for seatsIndex, seat in enumerate(row):
                user = seat.getUser()
                f.write(user.getEmail())
                if seatsIndex < NUM_SEATS - 1:
                    f.write(",")
            if rowsIndex < NUM_ROWS - 1:
                f.write("\n")
        f.close()

    # seatFile = "data/users/" + session.get('email') + "/reservations/" + date + ".txt" 


    # if session.get('seat') is None: # if a user has no current seats at that date, creates new file and writes to it
    #     session['seat'] = selectedSeat
    #     with open(seatFile,"w") as f:
    #         f.write(selectedSeat)
    #         f.close()
    # else: # if a user already has seats reserved, concatenate new seat with previous seats
    #     session['seat'] += (" " + selectedSeat)
    #     with open(seatFile,"a") as f:
    #         f.write(" ")
    #         f.write(selectedSeat)
    #         f.close()
    
    # # write new data into the txt file with 
    # with open(file,"w") as f:
    #     for currentData in row:
    #         f.write(currentData)
    #         f.write(" ")
   
    #     f.close()

    return SEATS

def loadSeats(SEATS, date):
    seatsFile = "data/concerts/"+date+"/seats.txt"
    with open(seatsFile) as f:
        lines = f.read().splitlines()

        for i, line in enumerate(lines):
            SEATS[i] = line.split(',')
            # line.rsplit(',',1)
            # re.split(',|\n',line)

        f.close()

    price = 100
    seatLetter = 'A'

    for row in SEATS:
        seatNum = 1
        
        for seatIndex in range(0,NUM_SEATS):
            if row[seatIndex] == "None":
                seatLetter = 'N'
                seatNum = 0
                firstName = "None"
                lastName = "None"
                email = "None"
                password = "None"
                user = User(firstName, lastName, email, password)
                seat = Seat(seatLetter, seatNum, user, price, EMPTY)
                row[seatIndex] = seat
            else:
                userFile = "data/users/" + row[seatIndex] + "/" + "info.txt"

                try:
                    open(userFile)
                except IOError:
                    flash('User in seat.','error')
                    return redirect(url_for('concerts'))
                
                with open(userFile,"r") as f:
                    line = f.readline()
                    userDetails = line.split()
                    user = User(userDetails[FIRST_NAME_INDEX], userDetails[LAST_NAME_INDEX], userDetails[EMAIL_INDEX], userDetails[PASSWORD_INDEX])
                    f.close()

                seat = Seat(seatLetter, seatNum, user, price, RESERVED)
                row[seatIndex] = seat 
            seatNum += 1
        
        seatLetter = chr(ord(seatLetter) + 1)
        price -= 10

    # print(SEATS)

    return SEATS

# clears the user's name from the txt file that contains the concert's seats
# date: used to get the file under a user's name to determine what seats to cancel
def cancelAnyReservationForUser(date):
    global SEATS

    user = session.get('firstName')+session.get('lastName')            

    # checks each row to see if user has a seat reserved
    removeUser(user, date, "A", SEATS[A_INDEX])
    removeUser(user, date, "B", SEATS[B_INDEX])
    removeUser(user, date, "C", SEATS[C_INDEX])
    removeUser(user, date, "D", SEATS[D_INDEX])
    removeUser(user, date, "E", SEATS[E_INDEX])

    file = "data/users/" + session.get('email') + "/" + date + ".txt"
    # clears the user's file with the data stored of the seat they reserved
    with open(file,"w") as f:
        f.seek(0)
        f.truncate()
        f.close()
    os.remove(file)

    session.pop('seat', None)

# resets the seat in the row given back to "None" which signifies an empty seat
def removeUser(user, date, row, data):
    file = "data/concerts/" + date + "/" + row + ".txt" #open each row on that day
    with open(file,"r+") as f:
        line = f.readline()                           
        data = line.split(" ")  
        newData = data

        for i, seat in enumerate(data):
            if seat == user: 
                newData[i] = "None" # if name in file matches the user given, mark that seat as empty
            else:
                newData[i] = data[i] # do not touch previous name or empty seat, if not a match
        
        f.seek(0) # goes to first space in the txt file
        f.truncate() # clears file of all data
        # rewrites the data into the txt file

        for i, currentData in enumerate(newData):
            f.write(currentData)
            f.write(" ")
    
        f.close() 
