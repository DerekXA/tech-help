from flask import Flask, render_template, request, session, redirect, url_for, session, flash
from flask.helpers import url_for
from pymongo import MongoClient
from datetime import datetime
from bson.objectid import ObjectId
import os
import bcrypt

host = os.environ.get("DB_URL")
client = MongoClient(host=host)
db = client.buildmatch
users = db.users
posts = db.posts

app = Flask(__name__)
app.secret_key = '9a5c0aaf287745d3b21371fb097bb5a22e6da0e9c8fb3bc39e34474f2f400f57'

@app.route('/')
def index():
    session['email']=None
    return render_template('index.html')

@app.route('/', methods=['GET', 'POST'])
def login():
    message = ''
    post = posts.find()
    if request.method=='POST':
        form_name = request.form['form-name']
        if form_name == 'form1':
            email = request.form.get('email')
            email_found = users.find_one({'email': email})

            password1 = request.form.get('password1')
            password2 = request.form.get('password2')

            if email_found:
                message = 'There is already an account with this email'
                flash(f"There is already an account with this email")
                return render_template('index.html', message=message)
            elif password1 != password2:
                message = 'Passwords do not match, please re-enter passwords'
                flash(f"passwords do not match")
                return render_template('index.html', message=message)
            else:
                hashed = bcrypt.hashpw(password2.encode('utf-8'), bcrypt.gensalt())
                user = {
                    'email':request.form.get('email'),
                    'password':hashed,
                    'username':f'Anonymous'
                }
                
                users.insert_one(user)
                session['email']=request.form['email']
                user_obj= users.find_one({'email': session['email']})

                print(user_obj)
                return render_template('home.html', user=user_obj, posts=post)

        elif form_name == 'form2':
            email = request.form.get('email')
            password = request.form.get('password')

            email_found = users.find_one({'email': email})

            if email_found:
                email_val = email_found['email']
                password_check = email_found['password']
                if bcrypt.checkpw(password.encode('utf-8'), password_check):
                    session['email']=email_val
                    user_obj= users.find_one({'email': session['email']})
                    return render_template('home.html', user=user_obj, posts=post)
                else:
                    message = 'Incorrect password, try again'
                    flash(f'incorrect password')  
                    return render_template('index.html', message=message)
            else:
                message = 'email dose not match any account ,please create one'
                flash(f"no account with that email")
                return render_template('index.html', message=message)

@app.route('/logout')
def logout():
    session['email']=None
    return render_template('index.html')


@app.route('/home')
def home():
    user_obj= users.find_one({'email': session['email']})
    post=posts.find()
    print(post)
    return render_template('home.html', user=user_obj, posts=post)

@app.route('/<user_id>/home', methods=['POST'])
def post(user_id):
    now = datetime.now()
    dt_string = now.strftime("%d/%m/%Y %H:%M")
    user_obj= users.find_one({'email': session['email']})
    post = {
        'user_id':user_id,
        'created_at':dt_string,
        'content':request.form.get('content')
    }
    posts.insert_one(post)
    print(post)
    print(user_id)
    all_posts=posts.find()
    return redirect(url_for('home', user=user_obj, posts=all_posts))


@app.route('/<user_id>/posts')
def posts_index(user_id):
    posts_found = posts.find({'user_id': user_id})
    user_obj= users.find_one({'email': session['email']})
    return render_template('view-posts.html', posts=posts_found, user=user_obj)

@app.route('/<user_id>/posts/<post_id>/update', methods=['POST'])
def post_update(user_id, post_id):
    user_obj = users.find_one({'email': session['email']})
    now = datetime.now()
    dt_string = now.strftime("%d/%m/%Y %H:%M")
    updated_post = {
        'user_id':user_id,
        'created_at':dt_string,
        'content':request.form.get('content')
    }
    posts.update_one(
        {'_id': ObjectId(post_id)},
        {'$set':updated_post}
    )
    return redirect(url_for('posts_index', user_id=user_id))


@app.route('/<user_id>/posts/<post_id>/delete', methods=['POST'])
def post_delete(user_id, post_id):
    posts.delete_one({'_id':ObjectId(post_id)})
    return redirect(url_for('posts_index', user_id=user_id))

@app.route('/<user_id>/settings')
def user_settings(user_id):
    user_obj = users.find_one({'email': session['email']})
    print(user_id)
    return render_template('user-settings.html', user=user_obj)


@app.route('/<user_id>/settings/delete-account', methods=['POST'])
def user_delete(user_id):
    print(user_id)
    users.delete_one({'_id':ObjectId(user_id)})
    posts.remove({'user_id':user_id})
    session['email']=None
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True, port=7000)