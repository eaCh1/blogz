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

    def __init__(self, title, body):
        self.title = title
        self.body = body
        #sself.owner = owner

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email= db.Column(db.String(30))
    password = db.Column(db.String(30))
    blogs = db.relationship('Blog', backref='user')

    def __init__(self, email, password):
        self.email = email
        self.password = password

@app.route('/')
def index():
    return redirect ('/blog')

@app.route('/blog')
def main_blog():
    #makes a mulidictionary with the parsed contents of the query String
    query_param = request.args.get('id')
    if query_param:
        #render individual blog post page, with list of posts
        posts = Blog.query.filter_by(id=query_param)
        return render_template("post.html",
                                posts=posts)
    else:
        #grab all posts in the database
        posts = Blog.query.all()
        #render main blog page
        return render_template('blog.html',
                                title="Post Things!",
                                posts=posts)

# @app.before_request
# def require_login():
#     allowed_routes = ['login', 'register']
#     if request.endpoint not in allowed_routes and 'email' not in session:
#         return redirect('/login')

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

@app.route('/register', methods=['POST', 'GET'])
def register():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        verify = request.form['verify']

        #validate user information using methods from usersignup

        existing_user = User.query.filter_by(email=email).first()
        if not existing_user:
            new_user = User(email, password)
            db.session.add(new_user)
            db.session.commit()
            session['email'] = email
            return redirect ('/')
        else:
            return flash("Duplicate user")
    return render_template('register.html')

@app.route('/newpost', methods=['POST', 'GET'])
def add_post():

    if request.method == 'POST':
        post_title = request.form['post-title']
        post_body = request.form['text-area']

        if not is_title_empty(post_title) and not is_body_empty(post_body):
            post = Blog(post_title, post_body)
            db.session.add(post)
            db.session.commit()

            post_id = str(post.id)
            owner_id = str(post.owner_id)
            return redirect('/blog?id=' + post_id + '&post_id=' + owner_id)
        else:
            if is_title_empty(post_title):
                flash("Please provide a title for your post")
            if is_body_empty(post_body):
                flash("Please provide some content for your post")
            return render_template("newpost.html",
                                    title="Try Again!",
                                    post_title=post_title,
                                    post_body=post_body)

    return render_template("newpost.html",
                            title="New Post!")

def is_title_empty(post_title):
    if post_title != "":
        return False
    return True
def is_body_empty(post_body):
    if post_body != "":
        return False
    return True

if __name__ == '__main__':
    app.run()
