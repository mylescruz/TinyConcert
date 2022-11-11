# Tiny Concert Project
# By Myles Cruz 
# Project originally created for class at St. Norbert College
#   CSCI 322: Programming Languages, Dr. Ben Geisler
# Created: December 4, 2020
# Last Modified: November 10, 2022

from flask import Flask, flash, render_template, session, redirect, url_for, request
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, EqualTo, Length, Regexp
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
row_A = []
row_B = []
row_C = []
row_D = []
row_E = []
seats = [row_A,row_B,row_C,row_D,row_E]

# global constants
NUM_CONCERTS = 9
NUM_ROWS = 5
NUM_SEATS = 10
A_INDEX = 0
B_INDEX = 1
C_INDEX = 2
D_INDEX = 3
E_INDEX = 4
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
    email = StringField('Email:', validators=[DataRequired(), Regexp(regex = "\w*\@\w*\.\w*",message = "Invalid email")])
    password = StringField('Password: ', validators=[DataRequired(), Length(min = 8, max = 25, message = "Must be at least 8 characters"), EqualTo('confirm', message = 'Passwords must match')])
    confirm = StringField('Repeat Password: ', validators=[DataRequired()])
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
class CheckoutForm(FlaskForm):
    creditCard = StringField('Credit Card Number: ', validators=[DataRequired(), Length(min = 16, max = 16, message = "Invalid credit card number")])
    expirationDate = StringField('Expiration Date (MM/YY): ', validators=[DataRequired(), Regexp(regex = "(0[1-9]|1[0-2])\/2[2-9]", message = "Invalid expiration date")])
    cvv = StringField('CVV: ', validators=[DataRequired(), Length(min = 3, max = 4, message = "Must be at least 3 digits")])
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
            f.close()

        givenEmail = loginForm.email.data
        givenPassword = loginForm.password.data

        if (givenEmail == userDetails[EMAIL_INDEX]) & (givenPassword == userDetails[PASSWORD_INDEX]):
            user = User(userDetails[FIRST_NAME_INDEX], userDetails[LAST_NAME_INDEX], userDetails[EMAIL_INDEX], userDetails[PASSWORD_INDEX])
    
            session['email'] = user.getEmail()
            session['password'] = user.getPassword()
            session['firstName'] = user.getFirstName()
            session['lastName'] = user.getLastName()
            flash('Logged in successfully!','info')

            if session.get('date') is None:
                return redirect(url_for('concerts'))
            else:
                return redirect(url_for('seatview', date = session.get('date'), musician = session.get('musician')))
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

    return render_template('concerts.html', musicians = musicians, dates = dates, times = times, images = images, numConcerts = NUM_CONCERTS, name = session.get('firstName'))

# displays the a concert's seats and their availability
@app.route("/seatview", methods=['GET','POST'])
def seatview():
    global seats

    date = request.args.get('date')
    session['date'] = date
    musician = request.args.get('musician')
    session['musician'] = musician

    if session.get('date') is None:
        flash('Must select a concert to view seats','error')
        return redirect(url_for('concerts'))

    seats = loadSeats(seats, date)

    rows = ["A","B","C","D","E"]
    # print("seats: ")
    # pprint.pprint(seats)

    return render_template('seatview.html', reserved = RESERVED, available = EMPTY, seats = seats, rows = rows, musician = musician, date = date, numRows = NUM_ROWS, numSeats = NUM_SEATS, name = session.get('firstName'))

# determines which row and seat was selected and allocates the data
@app.route("/seatSelect", methods=['GET','POST'])
def seatselect():
    concert = getSessionConcert()

    if session.get('email') is None:
        flash('Must login to reserve a seat','error')
        return redirect(url_for('login'))

    global seats
    
    row = request.args.get('row')
    number = request.args.get('seat')
    date = concert.getDate()
    musician = concert.getMusician()
    price = request.args.get('price')
    seatNum = int(number)
    selectedSeat = row + str(seatNum + 1)

    user = getSessionUser()
    seat = Seat(row, seatNum + 1, user, price, RESERVED)

    if row == "A":
        currentSeat = seats[A_INDEX][seatNum].getUser()
        if currentSeat.getEmail() == "None":
            seats[A_INDEX][seatNum] = seat
        else:
            flash('This seat is already reserved', 'error')
            return redirect(url_for('seatview', date = date, musician = concert.getMusician()))
    elif row == "B":
        currentSeat = seats[B_INDEX][seatNum].getUser()
        if currentSeat.getEmail() == "None":
            seats[B_INDEX][seatNum] = seat
        else:
            flash('This seat is already reserved', 'error')
            return redirect(url_for('seatview',date = date, musician = concert.getMusician()))
    elif row == "C":
        currentSeat = seats[C_INDEX][seatNum].getUser()
        if currentSeat.getEmail() == "None":
            seats[C_INDEX][seatNum] = seat
        else:
            flash('This seat is already reserved', 'error')
            return redirect(url_for('seatview',date = date, musician = concert.getMusician()))
    elif row == "D":
        currentSeat = seats[D_INDEX][seatNum].getUser()
        if currentSeat.getEmail() == "None":
            seats[D_INDEX][seatNum] = seat
        else:
            flash('This seat is already reserved', 'error')
            return redirect(url_for('seatview',date = date, musician = concert.getMusician()))
    elif row == "E":
        currentSeat = seats[E_INDEX][seatNum].getUser()
        if currentSeat.getEmail() == "None":
            seats[E_INDEX][seatNum] = seat
        else:
            flash('This seat is already reserved', 'error')
            return redirect(url_for('seatview',date = date, musician = concert.getMusician()))
    else:
        flash('Invalid seat chosen','error')
        return redirect(url_for('seatview',date = date, musician = concert.getMusician()))
        
    reserveSeatForConcert(seats, user, date)
    reserveSeatForUser(user, selectedSeat, date)

    return render_template('seatselect.html', musician = musician, date = date, selectedSeat = selectedSeat)

# transaction page for user to checkout
@app.route("/checkout", methods = ['GET','POST'])
def checkout():
    concert = getSessionConcert()
    row = request.args.get('row')
    number = request.args.get('seat')
    date = concert.getDate()
    musician = concert.getMusician()
    price = request.args.get('price')
    seatNum = int(number)
    selectedSeat = row + str(seatNum + 1)

    checkoutForm = CheckoutForm()
    if checkoutForm.validate_on_submit():
        creditCard = checkoutForm.creditCard.data
        expirationDate = checkoutForm.expirationDate.data
        cvv = checkoutForm.cvv.data

        if creditCard is None or expirationDate is None or cvv is None:
            flash('Invalid credit card','error')
            return redirect(url_for('checkout'))
        else:
            return redirect(url_for('seatselect', row = row, seat = seatNum, price = price))

    return render_template('checkout.html', name = session.get('firstName'), checkoutForm = checkoutForm, musician = musician, seat = selectedSeat, date = date, price = price)

# displays a user's current reservations and allows the ability to cancel a reservation
@app.route("/reservation", methods = ['GET','POST'])
def reservation():
    user = getSessionUser()

    if user.getEmail() is None: # a user must login to view their current reservations
        flash('Must login to see your reservation') # flashes error message for next page being directed to
        return redirect(url_for('login'))

    concerts = Concerts()
    musicians = []
    dates = []
    reservedSeats = []

    for key, value in concerts.concertsDict.items():
        dateFile = "data/users/" + user.getEmail() + "/reservations/" + key + ".txt" 
        isDate = os.path.isfile(dateFile)
        if isDate:
            dates.append(key)
            musicians.append(value.getMusician())
            try: 
                with open(dateFile,"r") as f:
                    line = f.readline()
                    reservedSeats.append(line)
                    f.close()
            except IOError: 
                flash('Internal error when retrieving seats. Please try again.','error')
                return redirect(url_for('reservations'))

    return render_template('reservation.html', name = session.get('firstName'), reservedSeats = reservedSeats, dates = dates, musicians = musicians, numReservations = len(dates))

# confirmation page to cancel a reservation
@app.route("/cancelreservation", methods = ['GET', 'POST'])
def cancelreservation():
    cancelDate = request.args.get('date') # takes in date selected to cancel the reservation
    confirmationForm = ConfirmationForm()
    if confirmationForm.validate_on_submit():
        if (session.get('password') == confirmationForm.password.data):   # a user must re-enter their password to confirm cancellation
            cancelUserReservation(cancelDate)
            flash('Reservation cancelled','info') # flashes confirmation message for next page being directed to
            return redirect(url_for('reservation'))
        else:
            flash('Wrong information inputted. Please try again to cancel the reservation.', 'error') # flashes error message for next page being directed to
            return redirect(url_for('cancelreservation'))
    return render_template('cancelreservation.html', confirmationForm = confirmationForm, name=session.get('firstName'))

# Stores a new user's first name, last name, email and password in a folder
def StoreUser(form):
    user = User(form.firstName.data, form.lastName.data, form.email.data, form.password.data)
    session['firstName'] = user.getFirstName()
    session['lastName'] = user.getLastName()
    session['email'] = user.getEmail()
    session['password'] = user.getPassword()

    userFolder = "data/users/" + user.getEmail()
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

    os.mkdir(userFolder + "/reservations")

# returns the current user logged in
def getSessionUser():
    firstName = session.get('firstName')
    lastName = session.get('lastName')
    email = session.get('email')
    password = session.get('password')

    user = User(firstName, lastName, email, password)
    return user

# returns the current concert selected
def getSessionConcert():
    date = session.get('date')
    musician = session.get('musician')
    time = session.get('time')
    image = session.get('image')

    concert = Concert(date, musician, time, image)
    return concert

# load seats for a concerts
def loadSeats(seats, date):
    seatsFile = "data/concerts/"+date+"/seats.txt"
    with open(seatsFile) as f:
        lines = f.read().splitlines()

        for i, line in enumerate(lines):
            seats[i] = line.split(',')

        f.close()

    price = 100
    seatLetter = 'A'

    for row in seats:
        seatNum = 1
        
        for seatIndex, seat in enumerate(row):
            if seat == "None":
                seatLetter = 'N'
                seatNum = 0
                firstName = "None"
                lastName = "None"
                email = "None"
                password = "None"
                user = User(firstName, lastName, email, password)
                userSeat = Seat(seatLetter, seatNum, user, price, EMPTY)
                row[seatIndex] = userSeat
            else:
                userFile = "data/users/" + seat + "/" + "info.txt"

                try:
                    open(userFile)
                except IOError:
                    flash('Internal error when loading seats. Please try again.','error')
                    return redirect(url_for('concerts'))
                
                with open(userFile,"r") as f:
                    line = f.readline()
                    userDetails = line.split()
                    user = User(userDetails[FIRST_NAME_INDEX], userDetails[LAST_NAME_INDEX], userDetails[EMAIL_INDEX], userDetails[PASSWORD_INDEX])
                    f.close()

                userSeat = Seat(seatLetter, seatNum, user, price, RESERVED)
                row[seatIndex] = userSeat 
            seatNum += 1
        
        seatLetter = chr(ord(seatLetter) + 1)
        price -= 10

    # pprint.pprint(seats)

    return seats


# reserve the seat in the concert's file
def reserveSeatForConcert(seats, user, date):
    # pprint.pprint(seats)
    seatsFile = "data/concerts/" + date + "/seats.txt"
    
    with open(seatsFile,"w") as f:
        for rowsIndex, row in enumerate(seats):
            for seatsIndex, seat in enumerate(row):
                user = seat.getUser()
                f.write(user.getEmail())
                if seatsIndex < NUM_SEATS - 1:
                    f.write(",")
            if rowsIndex < NUM_ROWS - 1:
                f.write("\n")
        f.close()

# reserve the seat in the user's file
def reserveSeatForUser(user, selectedSeat, date):
    userFile = "data/users/" + user.getEmail() + "/reservations/" + date + ".txt" 
    isUser = os.path.isfile(userFile)  

    if isUser:
        with open(userFile,"a") as f:
            f.write(",")
            f.write(selectedSeat)
            f.close()
    else:
        with open(userFile,"w") as f:
            f.write(selectedSeat)
            f.close()

def cancelUserReservation(date):
    print("In cancelUserReservation")
    global seats

    seats = loadSeats(seats, date)

    user = getSessionUser()
    seats = removeUserInConcerts(seats, user, date)

    # pprint.pprint(seats)
    file = "data/concerts/" + date + "/seats.txt"
    with open(file,"w") as f:
        for rowsIndex, row in enumerate(seats):
            for seatsIndex, seat in enumerate(row):
                currentUser = seat.getUser()
                f.write(currentUser.getEmail())
                if seatsIndex < NUM_SEATS - 1:
                    f.write(",")
            if rowsIndex < NUM_ROWS - 1:
                f.write("\n")
        f.close()

    userFile = "data/users/" + user.getEmail() + "/reservations/" + date + ".txt"
    # clears the user's userFile with the data stored of the seat they reserved
    with open(userFile,"w") as f:
        f.seek(0)
        f.truncate()
        f.close()
    os.remove(userFile)

def removeUserInConcerts(seats, user, date):
    print("in removeUserInConcerts")
    file = "data/concerts/" + date + "/seats.txt"

    print("User session email: ", user.getEmail())

    with open(file, "r") as f:
        rows = f.read().splitlines()

        for i, row in enumerate(rows):
            rows[i] = row.split(',')

        f.close()

        price = 100
        seatLetter = 'A'
        for rowIndex, row in enumerate(rows):
            seatNum = 1
            for seatIndex, seat in enumerate(row):
                if seat == user.getEmail():
                    firstName = "None"
                    lastName = "None"
                    email = "None"
                    password = "None"
                    noUser = User(firstName, lastName, email, password)
                    userSeat = Seat(seatLetter, seatNum, noUser, price, EMPTY)
                    seats[rowIndex][seatIndex] = userSeat
                seatNum += 1
            price -= 10
            seatLetter = chr(ord(seatLetter) + 1) 

        f.close()
    
    return seats