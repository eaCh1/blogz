from flask import Flask, request, redirect, render_template, flash, session
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.secret_key = "big_fish"
app.config['DEBUG'] = True
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://blogz:pizza@localhost:8889/blogz'
app.config['SQLALCHEMY_ECHO'] = True
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
db = SQLAlchemy(app)

class Blog(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120))
    body = db.Column(db.String(999))
    owner_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    def __init__(self, title, body, owner):
        self.title = title
        self.body = body
        self.owner = owner
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email= db.Column(db.String(30))
    password = db.Column(db.String(30))
    posts = db.relationship('Blog', backref='owner')

    def __init__(self, email, password):
        self.email = email
        self.password = password

#decorator, checks this before all HTTP requests
@app.before_request
def require_login():
    #if the request route is one of these functions (not html file)
    allowed_routes = ['login', 'main_blog', 'register', 'index', 'signup']
    #if the endpoint is not in the allowed routes and there is no email in the session
    if request.endpoint not in allowed_routes and 'email' not in session:
        #redirect to the login page because there's no user signed in
        return redirect('/login')
#base route
@app.route('/')
def index():
    #find all the users in the User table
    users = User.query.all()
    #display a list of all the currently registered users
    return render_template("index.html", title="Home", users=users)
#login route
@app.route('/login', methods=['POST', 'GET'])
def login():

    #if the HTTP request method is POST, process the information
    if request.method == 'POST':
        #grab email from the form
        email = request.form['email']
        #grab password from the form
        password = request.form['password']
        #search for users with that email, return the first result
        user = User.query.filter_by(email=email).first()
        #if there is a user present and the password provided
        #matches the password stored for the user
        if user and user.password == password:
            #add the email/username to the session under the key 'email'
            session['email'] = email
            #send a lil confirmation message
            flash("Welcome Back")
            #redirect to the new post page after successful login
            return redirect('/newpost')
        else:
            #if there's nothin in the user variable
            if not user:
                #there's no user in the database
                flash('User does not exist')
                return render_template('login.html', title="Login", email=email)
            #if the password provided does not match the user's
            if user.password != password:
                flash('User password incorrect')
                return render_template('login.html', title="Login", email=email)
    # display the login in page when the request is GET
    return render_template('login.html', title="Login")
#all posts route
@app.route('/blog')
def main_blog():
    #makes a mulidictionary with the parsed contents of the query String
    #searches for the request parameter next to the argument passed
    post_param = request.args.get('id')
    owner_param = request.args.get('user')

    #if either one of these variables is not empty
    if post_param or owner_param:
        if post_param:
            #render individual blog post page, with list of posts
            posts = Blog.query.filter_by(id=post_param).all()
            return render_template('post.html',
                                    title="It's a Post!",
                                    posts=posts)
        if owner_param:
            #reender the user page displaying all the users' posts
            #matching the ownder param to the owner id column in Blog table
            posts = Blog.query.filter_by(owner_id=owner_param).all()
            return render_template('user.html',
                                    title="Blog Posts!",
                                    posts=posts)
    # if neither one of the request parameters hold any value
    else:
        #grab all posts in the database
        posts = Blog.query.all()
        #render main blog page
        return render_template('blog.html',
                                title="All Posts",
                                posts=posts)
#register user route
@app.route('/register', methods=['POST', 'GET'])
def register():
    #if the request method is POST, process the information
    if request.method == 'POST':
        #grab the email from the form
        email = request.form['email']
        #grabe the password from the form
        password = request.form['password']
        #grab the password verfication form the form
        verify = request.form['verify']

        #utilize the validate_register() method to
        #check for errors, and display error messages
        #if the method returns TRUE...
        if validate_register(email, password, verify) == True:
            #...try to load an existing_user into the variable
            existing_user = User.query.filter_by(email=email).first()
            #if there is no existing_user in the database
            if not existing_user:
                new_user = User(email, password)
                db.session.add(new_user)
                db.session.commit()
                session['email'] = email
                flash('Welcome to the Club')
                return redirect ('/newpost')
            #if there is an existing_user in the database
            else:
                #display an error message
                flash("That username is already taken")
                #render the page again and do not keep the email in the field
                return render_template('register.html',
                                        title="Register!")
    #if the request method is GET, render the empty template
    return render_template('register.html',
                            title="Register!")
#new post entry
@app.route('/newpost', methods=['POST', 'GET'])
def new_post():
    # grab the owner of the post, whomever is currently logged in
    owner = User.query.filter_by(email=session['email']).first()
    # if a POST request comes through the page
    if request.method == 'POST':
        #grab the content of the title field
        post_title = request.form['post-title']
        #grab the content of the post
        post_body = request.form['text-area']

        #helper method to check if the title is empty
        def is_title_empty(post_title):
            if post_title != "":
                return False
            return True
        #helper mthod to check if the body is empty
        def is_body_empty(post_body):
            if post_body != "":
                return False
            return True

        #if there is content in both the title and the body of the form
        if not is_title_empty(post_title) and not is_body_empty(post_body):
            #user Blog constructor to create a new post
            post = Blog(post_title, post_body, owner)
            #add the post to the db session
            db.session.add(post)
            #commit the session, send to db
            db.session.commit()

            #extract post id
            post_id = str(post.id)
            #extract owner id
            user = str(post.owner_id)
            #redirect to the posts unique Url
            return redirect('/blog?id=' + post_id + '&user=' + user)
        #if there is not content in either the title or the body
        else:
            #if the title is empty
            if is_title_empty(post_title):
                #display error
                flash("Please provide a title for your post")
            #if the body is empty
            if is_body_empty(post_body):
                #display error
                flash("Please provide some content for your post")
            #return the page again, maintainint whatever content was provided
            return render_template("newpost.html",
                                    title="Try Again!",
                                    post_title=post_title,
                                    post_body=post_body)
    # return the blank template if there is NO post request
    return render_template("newpost.html",
                            title="New Post!")
#logout route
@app.route('/logout', methods=['GET'])
def logout():
    #drop the email from the session
    del session['email']
    #redirect to the all posts page
    return redirect('/blog')

#helper method to validify the user offered information
#arguments passed are the user provided email password and passworf confirmation
def validate_register(email, password, verify):
    #stack of helper methods to check for validification or is empty
    def is_valid_email(email):
        #check to see if the email is longer than 3 characters
        if len(email) >= 3:
            #check to see if the email has a domain address
            if "@" in email and "." in email:
                #check to see if there is a space in email is empty
                if not " " in email:
                    #if it passess all those checks, return True
                    return True
        flash("That's not a valid email")
        return False
    def is_valid_password(password):
        #see if it's longer than 3 characters
        if len(password) >= 3:
            #and is not empty
            if not " " in password:
                return True
        flash("That's not a valid password")
        return False
    def is_empty_email(email):
        if email != "":
            return True
        flash("That's not a valid email")
        return False
    def is_empty_password(password):
        if password != "":
            return True
        flash("That's not a valid password")
        return False
    def is_empty_verify(verify):
        if verify != "":
            return True
        flash("At least try to match the passwords")
        return False
    def do_passwords_match(password, verify):
        #see if the passwords match
        if password == verify:
            return True
        flash("Passwords don't match")
        return False

    #check to see if the email and the password are valid
    if not is_valid_email(email) or not is_valid_password(password):
        return render_template('register.html')
    #check to see if the email password or verify are empty
    if not is_empty_email(email) or not is_empty_password(password) or not is_empty_verify(verify):
        return render_template('register.html')

    #if the passwords match
    if do_passwords_match(password, verify):
        #return the method! as True!!
        return True
    #if they do match, render the template again
    else:
        return render_template("register.html")

if __name__ == '__main__':
    app.run()
