from flask import Flask, render_template, request, session, redirect
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from flask_mail import Mail
import json
import math

local_server = True
with open('config.json', 'r') as c:
    params_data = json.load(c)["params"]

app = Flask(__name__)
app.secret_key = params_data['secret-key']
app.config.update(
    MAIL_SERVER='smtp.gmail.com',
    MAIL_PORT='465',
    MAIL_USE_SSL=True,
    MAIL_USERNAME=params_data["gmail-user"],
    MAIL_PASSWORD=params_data["gmail-password"]
)
mail = Mail(app)

if (local_server):
    app.config['SQLALCHEMY_DATABASE_URI'] = params_data['local_uri']
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = params_data['prod_uri']

db = SQLAlchemy(app)


class Contacts(db.Model):
    sno = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    phone_num = db.Column(db.String(12), nullable=False)
    msg = db.Column(db.String(120), nullable=False)
    date = db.Column(db.String(12), nullable=False)
    email = db.Column(db.String(20), nullable=False)

class Posts(db.Model):
    sno = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(80), nullable=False)
    tagline = db.Column(db.String(120), nullable=False)
    slug = db.Column(db.String(21), nullable=False)
    content = db.Column(db.String(120), nullable=False)
    img_file = db.Column(db.String(12), nullable=False)
    date = db.Column(db.String(12), nullable=True)


@app.route("/", methods=['GET', 'POST'])
def home():
    posts = Posts.query.filter_by().all()
    last = math.ceil(len(posts)/int(params_data['no_of_posts']))
    page = request.args.get('page')
    if(not str(page).isnumeric()):
        page = 1
    page = int(page)
    posts = posts[(page-1)*int(params_data['no_of_posts']):(page-1)*int(params_data['no_of_posts']) + int(params_data['no_of_posts'])]

    if (page ==1):
        prev = "#"
        next = "/?page=" + str(page+1)
    elif(page==last):
        prev = "/?page=" + str(page-1)
        next = "#"
    else:
        prev = "/?page=" + str(page-1)
        next = "/?page=" + str(page+1)

    return render_template('index.html', posts=posts, params=params_data, prev=prev, next=next)

@app.route("/dashboard", methods=['GET', 'POST'])
def dashboard():
    if 'user' in  session and session['user'] == params_data['admin-user']:
        posts = Posts.query.all()
        return render_template('dashboard.html',params=params_data, posts=posts)

    if request.method == 'POST':
        username = request.form.get('uname')
        userpass = request.form.get('pass')
        if (username== params_data['admin-user'] and userpass == params_data['admin-password']):
            session['user'] = username
            posts = Posts.query.all()
            return render_template('dashboard.html', params=params_data, posts=posts)
        else:
            return render_template('login.html', params=params_data)


    else:
        return render_template('login.html', params=params_data)



@app.route("/about")
def about():
    return render_template('about.html', params=params_data)


@app.route("/post/<string:post_slug>", methods =['GET'])
def post_route(post_slug ):
    post = Posts.query.filter_by(slug=post_slug).first()
    return render_template('post.html', params=params_data, post_html=post)

@app.route("/logout")
def logout():
    session.pop("user")
    return redirect("/dashboard")


@app.route("/contact", methods=['GET', 'POST'])
def contacts():
    if (request.method == 'POST'):
        '''add entery to the database'''
        name = request.form.get('name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        message = request.form.get('message')
        entry = Contacts(name=name, phone_num=phone, msg=message, date=datetime.now(), email=email)
        db.session.add(entry)
        db.session.commit()
        mail.send_message('New Message from Blog' + name,
                          sender=params_data["gmail-user"],
                          recipients=[email] ,
                          body=message + "\n" + phone
                          )

    return render_template('contact.html', params=params_data)

@app.route("/edit/<string:sno>", methods= ['GET', 'POST'])
def edit(sno):
    if ('user' in session and session['user'] == params_data['admin-user']):
        if request.method == 'POST':
            box_title = request.form.get('Title')
            tline = request. form.get('tagline')
            slug = request.form.get('slug')
            content = request.form.get('Content')
            image = request.form.get('Image')

            if sno == '0':
                post = Posts(title = box_title, slug=slug, content = content, tagline=tline, img_file = image, date =datetime.now())
                db.session.add(post)
                db.session.commit()
            else:
                post = Posts.query.filter_by(sno=sno).first()
                post.title = box_title
                post.slug = slug
                post.content = content
                post.tagline = tline
                post.img_file = image
                post.date = datetime.now()
                db.session.commit()
                return redirect('/edit/'+sno)
        post = Posts.query.filter_by(sno=sno).first()
        return render_template('edit.html', params =params_data, post=post)

@app.route("/delete/<string:sno>", methods = ['GET', 'POST'])
def delete(sno):
    if ('user' in session and session['user'] == params_data['admin-user']):
        post = Posts.query.filter_by(sno=sno).first()
        db.session.delete(post)
        db.session.commit()
    return redirect('/dashboard')





app.run(debug=True)
