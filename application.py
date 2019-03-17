import os
import datetime
import pandas as pd
import pandas_datareader.data as web
import numpy as np
import requests
import urllib.parse

from cs50 import SQL
from flask import Flask, flash, jsonify, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash
from helpers import apology, login_required, lookup, usd, lookup_2, graph

# Configure application | from cs50 source code
app = Flask(__name__)

# Ensure templates are auto-reloaded | from cs50 source code
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Ensure responses aren't cached | from cs50 source code
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


# Custom filter | from cs50 source code
app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies) | from cs50 source code
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database | from cs50 source code
db = SQL("sqlite:///finance.db")

# Portfolio page
@app.route("/index")
@login_required
def index():
    stock = db.execute("SELECT stock, quantity FROM transaction_history WHERE id=:id", id=session["user_id"])
    shares = db.execute("SELECT quantity FROM transaction_history WHERE id=:id", id=session["user_id"])
    stocklist = set([])
    data = []
    for dictionary in stock:
        stocklist.add(dictionary["stock"])
    for element in stocklist:
        cur_price = lookup(element)["price"]
        total_qnt = (db.execute("SELECT SUM(quantity) AS quantity FROM transaction_history WHERE id=:id AND stock = :element",
                                id=session["user_id"], element=element))[0]["quantity"]
        if total_qnt == 0:
            continue
        total_spend_pairs = (db.execute("SELECT price, quantity FROM transaction_history WHERE id=:id AND stock = :element",
                                id=session["user_id"], element=element))
        invested_amt = []
        for element_2 in total_spend_pairs:
            invested_amt.append(element_2["price"] * element_2["quantity"])
        invested_value = sum(invested_amt)
        percent_return = "{0:.2f}".format((invested_value - (cur_price * total_qnt))*100/invested_value)
        dic = lookup(element)
        bufferlist = [element, dic["name"], total_qnt, dic["price"], dic["price"]*total_qnt, percent_return]
        data.append(bufferlist)
    grandsumlist = []
    for element in data:
        grandsumlist.append(element[4])
    cash = float("{0:.2f}".format((db.execute("SELECT cash FROM users WHERE id= :id", id=session["user_id"]))[0]["cash"]))
    grandsum = cash+float("{0:.2f}".format(sum(grandsumlist)))
    return render_template("index.html", data=data, cash=cash, grandsum=grandsum)

# Stock stocksearch page
@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    if request.method == "POST":
        try:
            symbol = request.form.get("symbol")
        except TypeError:
            return apology("Please input a valid symbol")
        if not symbol:
            return apology("Please input a valid symbol")
        return redirect("/stockinfo?symbol="+symbol)
    if request.method == "GET":
        return render_template("buy.html")

# stock purchase function
@app.route("/stockbuy", methods=["POST"])
@login_required
def stockbuy():
    try:
        shares = int(request.form.get("shares"))
    except ValueError:
        return apology("Please input a valid number of shares")
    try:
        symbol = request.form.get("symbol")
        price = lookup(symbol)["price"]
    except TypeError:
        return apology("Please input a valid symbol")
    if not symbol:
        return apology("Please input a valid symbol")
    if shares < 0:
        return apology("Please input a valid number of shares")
    cash = (db.execute("SELECT cash FROM users WHERE id= :id", id=session["user_id"]))[0]["cash"]
    cash -= shares * price
    if cash < 0:
        return apology("Insufficient Balance. Transaction Aborted.")
    db.execute("Update users SET cash = :cash WHERE id= :id", id=session["user_id"], cash=cash)
    db.execute("INSERT INTO transaction_history (id, stock, price, quantity, time) VALUES (:id, :stock, :price, :quantity, :time)",
              id=session["user_id"], stock=symbol, price=price, quantity=shares, time=datetime.datetime.now())
    return redirect("/index")

# check database for the username
@app.route("/check")
def check():
    """Return true if username available, else false, in JSON format"""
    username = request.args.get("username")
    rows = db.execute("SELECT * FROM users WHERE username= :username", username=username)
    if len(rows) > 0 or len(username) < 1:
        return jsonify(False)
    return jsonify(True)

# show transaction history
@app.route("/history")
@login_required
def history():
    """Show history of transactions"""
    data = db.execute("SELECT stock, price, quantity, time FROM transaction_history WHERE id= :id", id=session["user_id"])
    return render_template("history.html", data=data)

#| from cs50 source code
@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""
    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = :username",
                          username=request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/buy")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("home.html")

# | from cs50 source code
@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


# registration function
@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("register-password")
        confirmation = request.form.get("confirmation")
        print (username, password, confirmation)
        rows = db.execute("SELECT * FROM users WHERE username= :username", username=username)
        if not username or not password or not confirmation:
            return apology("Please fill all the fields")
        if len(rows) > 0:
            return apology("This username already exists")
        if not (password == confirmation):
            return apology("Password and confirmation do not match")
        hash = generate_password_hash(password)
        db.execute("INSERT INTO users (username,hash) VALUES (:username, :hash)", username=username, hash=hash)
        return redirect("/buy")
    if request.method == "GET":
        return render_template("register.html")

# stock selling function
@app.route("/sell", methods=["POST"])
@login_required
def sell():
    """Sell shares of stock"""
    cash = (db.execute("SELECT cash FROM users WHERE id= :id", id=session["user_id"]))[0]["cash"]
    stock = db.execute("SELECT stock FROM transaction_history WHERE id=:id", id=session["user_id"])
    stocklist = set([])
    for dictionary in stock:
        stocklist.add(dictionary["stock"])
    if request.method == "GET":
        return render_template("sell.html", data=stocklist)
    if request.method == "POST":
        shares = int(request.form.get("shares"))
        try:
            symbol = request.form.get("symbol")
        except ValueError:
            return apology("Please input a valid number of shares")
        total_qnt = (db.execute("SELECT SUM(quantity) AS quantity FROM transaction_history WHERE id=:id AND stock = :symbol",
                                id=session["user_id"], symbol=symbol))[0]["quantity"]
        if type(total_qnt) == None:
            return apology("Too many shares, please input a valid amount")
        if shares > total_qnt:
            return apology("Too many shares, please input a valid amount")
        if not shares or shares < 0 or not symbol:
            return apology("Please input valid number of shares and a valid symbol")
        price = lookup(symbol)["price"]
        db.execute("Update users SET cash = :cash WHERE id= :id", id=session["user_id"], cash=cash+shares*(price))
        db.execute("INSERT INTO transaction_history (id, stock, price, quantity, time) VALUES (:id, :stock, :price, :quantity, :time)",
                   id=session["user_id"], stock=symbol, price=price, quantity=-shares, time=datetime.datetime.now())
        return redirect("/index")

# | from cs50 source code
def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return apology(e.name, e.code)


# Listen for errors | from cs50 source code
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)

# stockinfo page
@app.route("/stockinfo", methods=["GET", "POST"])
@login_required
def stockinfo():
    symbol = request.args.get("symbol")
    financials = [  f"https://www.nasdaq.com/symbol/{urllib.parse.quote_plus(symbol)}/financials?query=income-statement",
                        f"https://www.nasdaq.com/symbol/{urllib.parse.quote_plus(symbol)}/financials?query=balance-sheet",
                        f"https://www.nasdaq.com/symbol/{urllib.parse.quote_plus(symbol)}/financials?query=cash-flow",
                        f"https://www.nasdaq.com/symbol/{urllib.parse.quote_plus(symbol)}/financials?query=ratios"]
    graphic = graph(symbol)
    if graphic == apology("Please input a valid symbol."):
        return apology("Please input a valid symbol.")
    if request.method == "GET":
        profile = lookup_2(symbol)
        return render_template("stockinfo.html", profile=profile, symbol = symbol, financials = financials, graphic = graphic)
    if request.method == "POST":

        return redirect ("/index")

# homepage
@app.route("/home", methods=["GET", "POST"])
@login_required
def home():
    if request.method == "GET":
        return render_template("home.html")

# password change page
@app.route("/changepass", methods=["GET", "POST"])
@login_required
def changepass():
    if request.method == "POST":
        if not (check_password_hash(db.execute("SELECT hash FROM users WHERE id = :id", id=session["user_id"])[0]["hash"], request.form.get("oldpassword"))):
            flash (" The old password you inputted does not match with our database. Please retry later.")
            return redirect("/buy");
        db.execute("UPDATE users SET hash = :hash WHERE id = :id",
                              hash=generate_password_hash(request.form.get("newpassword")), id=session["user_id"])
        flash ("Your password has been succesfully changed!")
        return redirect("/buy")
    if request.method == "GET":
        return render_template("changepass.html")

# cash transfer page
@app.route("/transfer", methods=["GET", "POST"])
@login_required
def transfer():
    if request.method == "POST":
        username = request.form.get("username")
        user_dict = db.execute("SELECT username FROM users")
        user_list = []
        for element in user_dict:
            user_list.append(element["username"])
        if not (username in user_list):
            flash("ERROR:Such a user does not exist. Please input a valid username and retry later.")
            return redirect("/buy")
        try:
            cash=float(request.form.get("amount"))
        except TypeError:
            flash ("ERROR: Transfer amount needs to be numeric")
            return redirect("/buy")
        if cash > (db.execute("SELECT cash FROM users WHERE id= :id", id=session["user_id"]))[0]["cash"]:
            flash ("ERROR: Insufficient balance for this operation.")
            return redirect("/buy")
        try:
            db.execute("UPDATE users SET cash=cash + :cash  WHERE username= :username", cash=cash, username=username)
        except:
            flash("ERROR: Such a user does not exist")
            return redirect("/buy")
        db.execute("UPDATE users SET cash=cash - :cash  WHERE id= :id", cash=cash, id=session["user_id"])
        flash ("SUCCESS: The specified amount was succesfully transferred!")
        return redirect("/buy")
    if request.method == "GET":
        return render_template("transfer.html")

# return home when first loading
@app.route("/", methods=["GET"])
def direct():
    return redirect ("/home")
