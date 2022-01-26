from flask import Flask, request, redirect, render_template, flash, session, jsonify
from flask_debugtoolbar import DebugToolbarExtension
from forms import AddUserForm, FeedbackForm, LoginForm
from models import db, connect_db, Feedback, User

app = Flask(__name__)
app.config['SECRET_KEY'] = 'brockisgood'
debug = DebugToolbarExtension(app)
app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = False
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql:///feedback'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ECHO'] = True

connect_db(app)
# db.drop_all()
db.create_all()

@app.route("/")
def redirect_to_register_user():
    '''Redirects person to registration form'''

    return redirect("/register")


@app.route("/register", methods=["GET", "POST"])
def register_user():
    '''Returns registration form'''

    if "username" in session:
        return redirect(f"/users/{session['username']}")

    form = AddUserForm()

    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        email = form.email.data
        first_name = form.first_name.data
        last_name = form.last_name.data

        user = User.register(username, password, email, first_name, last_name)

        db.session.commit()
        session["username"] = user.username

        return redirect(f"/users/{user.username}")

    else:
        return render_template("users/register.html", form=form)


@app.route("/login", methods=["GET", "POST"])
def login_user():
    '''provide login form and authenticate if the username and password are correct'''

    if "username" in session:
        return redirect(f"/users/{session['username']}")
    
    form = LoginForm()

    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data

        user = User.authenticate(username, password)
        if user:
            session["username"] = user.username
            return redirect(f"/users/{user.username}")
        else:
            flash("Invalid username/password")
            return render_template("users/login.html", form=form)
    
    return render_template("users/login.html", form=form)


@app.route("/logout")
def logout():
    '''logs user out of session'''

    session.pop("username")
    return redirect('/login')


@app.route("/users/<username>")
def user_portal(username):
    '''show page with each post'''

    if "username" not in session or username != session['username']:
        return redirect("/login")
    
    user = User.query.get(username)

    return render_template('users/show.html', user=user)


@app.route("/users/<username>/delete", methods=["POST"])
def delete_user(username):
    '''delete user and return to register page'''

    if "username" not in session or username != session['username']:
        flash("You are not logged in!")
        return redirect("/login")
    
    user = User.query.get(username)
    db.session.delete(user)
    db.session.commit()
    session.pop("username")

    return redirect("/login")


@app.route("/users/<username>/feedback/new", methods=["GET", "POST"])
def new_feedback(username):
    '''Provide a form for creating new feedback for a specific user'''

    if "username" not in session or username != session['username']:
        flash("You are not logged in! Please login first.")
        return redirect("/login")
    
    form = FeedbackForm()

    if form.validate_on_submit():
        title = form.title.data
        content = form.content.data

        feedback = Feedback(title=title, content=content, username=username)

        db.session.add(feedback)
        db.session.commit()

        return redirect(f"/users/{feedback.username}")

    else:
        return render_template("feedback/new.html", form=form)


@app.route("/feedback/<int:feedback_id>/edit", methods=["GET", "POST"])
def edit_feedback(feedback_id):
    '''fill in the content areas and allow the user to edit it further'''

    feedback = Feedback.query.get(feedback_id)

    if "username" not in session or feedback.username != session['username']:
        flash("You are not logged in! Please login first.")
        return redirect("/login")
    
    form = FeedbackForm(title=feedback.title, content=feedback.content)

    if form.validate_on_submit():
        feedback.title = form.title.data
        feedback.content = form.content.data

        db.session.commit()

        return redirect(f"/users/{feedback.username}")
    
    return render_template("feedback/edit.html", form=form, feedback=feedback)


@app.route("/feedback/<int:feedback_id>/delete", methods=["POST"])
def delete_feedback(feedback_id):
    '''delete feedback from database'''

    feedback = Feedback.query.get(feedback_id)

    if "username" not in session or feedback.username != session['username']:
        flash("You are not logged in! Please login first.")
        return redirect("/login")

    db.session.delete(feedback)
    db.session.commit()

    return redirect(f"/users/{feedback.username}")