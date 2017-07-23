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

@app.before_request
def require_login():
    allowed_routes = ['login', 'main_blog', 'register', 'index', 'signup']
    if request.endpoint not in allowed_routes and 'email' not in session:
        return redirect('/login')

@app.route('/')
def index():
    users = User.query.all()
    return render_template("index.html", users=users)

@app.route('/login', methods=['POST', 'GET'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = User.query.filter_by(email=email).first()
        if user and user.password == password:
            session['email'] = email
            flash("Welcome Back")
            return redirect('/newpost')
        else:
            if not user:
                flash('User does not exist')
                return render_template('login.html', email=email)
            if user.password != password:
                flash('User password incorrect')
                return render_template('login.html', email=email)

    return render_template('login.html')

@app.route('/blog')
def main_blog():
    #makes a mulidictionary with the parsed contents of the query String
    post_param = request.args.get('id')
    owner_param = request.args.get('user')

    if post_param or owner_param:
        if post_param:
            #render individual blog post page, with list of posts
            posts = Blog.query.filter_by(id=post_param).all()
            return render_template('post.html',
                                    posts=posts)
        if owner_param:
            posts = Blog.query.filter_by(owner_id=owner_param).all()
            return render_template('user.html',
                                    posts=posts)
    else:
        #grab all posts in the database
        posts = Blog.query.all()
        #render main blog page
        return render_template('blog.html',
                                title="Post Things!",
                                posts=posts)

@app.route('/register', methods=['POST', 'GET'])
def register():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        verify = request.form['verify']

        if validate_register(email, password, verify) == True:
            existing_user = User.query.filter_by(email=email).first()

            if not existing_user:
                new_user = User(email, password)
                db.session.add(new_user)
                db.session.commit()
                session['email'] = email
                flash('Welcome to the Club')
                return redirect ('/newpost')
            else:
                flash("That username is already taken")
                return render_template('register.html')

    return render_template('register.html')

@app.route('/newpost', methods=['POST', 'GET'])
def new_post():
    # grab the owner of the post, whomever is currently logged in
    owner = User.query.filter_by(email=session['email']).first()
    # if a POST request comes through the page
    if request.method == 'POST':
        post_title = request.form['post-title']
        post_body = request.form['text-area']

        def is_title_empty(post_title):
            if post_title != "":
                return False
            return True
        def is_body_empty(post_body):
            if post_body != "":
                return False
            return True

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
            return redirect('/blog?id=' + post_id + '&user=' + user)
        else:
            if is_title_empty(post_title):
                flash("Please provide a title for your post")
            if is_body_empty(post_body):
                flash("Please provide some content for your post")
            return render_template("newpost.html",
                                    title="Try Again!",
                                    post_title=post_title,
                                    post_body=post_body)
    # return the blank template if there is NO post request
    return render_template("newpost.html",
                            title="New Post!")

@app.route('/logout', methods=['GET'])
def logout():
    del session['email']
    return redirect('/blog')

def validate_register(email, password, verify):

    def is_valid_email(email):
        if len(email) >= 3:
            if "@" in email and "." in email:
                if not " " in email:
                    return True
        flash("That's not a valid email")
        return False
    def is_valid_password(password):
        if len(password) >= 3:
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
        if password == verify:
            return True
        flash("Passwords don't match")
        return False

    if not is_valid_email(email) or not is_valid_password(password):
        return render_template('register.html')

    if not is_empty_email(email) or not is_empty_password(password) or not is_empty_verify(verify):
        return render_template('register.html')

    if do_passwords_match(password, verify):
        return True
    else:
        return render_template("register.html")

if __name__ == '__main__':
    app.run()
