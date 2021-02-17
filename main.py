from flask import Flask, redirect, render_template, session, flash, request, g, url_for
from flask_sqlalchemy import *
from datetime import datetime, date

app = Flask(__name__)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SECRET_KEY'] = 'thesecretkey'
db = SQLAlchemy(app)

class credentials(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    firstname = db.Column(db.String, nullable=False)
    lastname = db.Column(db.String, nullable=False)
    email = db.Column(db.String, nullable=False)
    username = db.Column(db.String, nullable=False)
    password = db.Column(db.String, nullable=False)

class Posts(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    postername = db.Column(db.String, nullable=False)
    posterusername = db.Column(db.String, nullable=False)
    title = db.Column(db.String, nullable=False)
    content = db.Column(db.String, nullable=False)
    datecreated = db.Column(db.String, nullable=False)

class Comments(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    postid = db.Column(db.Integer, nullable=False)
    postername = db.Column(db.String, nullable=False)
    posterusername = db.Column(db.String, nullable=False)
    content = db.Column(db.String, nullable=False)
    datecreated = db.Column(db.String, nullable=False)


@app.before_request
def before_request():
    g.user = None

    if 'user_id' in session:
        user = [x for x in credentials.query.all() if x.id == session['user_id']][0]
        g.user = user



#home page
@app.route('/', methods=['GET', 'POST'])
def home():
    posts = Posts.query.all()
    posts.reverse()
    return render_template('home.html', posts=posts)


#signup page
@app.route('/signup', methods=['POST', 'GET'])
def signup():
    if request.method == 'POST':
        firstname = request.form['firstname']
        lastname = request.form['lastname']
        email = request.form['email']
        username = request.form['username']
        password = request.form['password']
        g = [x for x in credentials.query.all() if x.username == username]
        if g: # username taken
            flash('Username taken')
            return redirect(url_for('signup'))
        if [x for x in credentials.query.all() if x.email == email]: # username taken
            flash('Email taken')
            return redirect(url_for('signup'))
        else:
            try:
                db.session.add(credentials(firstname = firstname, lastname=lastname, email=email,username=username, password=password))
                db.session.commit()
                return redirect(url_for('login'))
            except: #register completely unsuccesful
                flash('Username taken') 
                return redirect(url_for('signup'))

        
    else:
        return render_template('signup.html')


#login page
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        session.pop('user_id', None)
        username = request.form['username']
        password = request.form['password']
        
        try:
            user = [x for x in credentials.query.all() if x.username == username][0]
            if user and user.password == password:
                session['user_id'] = user.id
                return redirect(url_for('home'))
            else: #if credentials are incorrect
                flash('Please enter the correct username and password')
                return redirect(url_for('login'))
        except: 
            flash('Please enter the correct username and password')
            return redirect(url_for('login'))
            

    return render_template('login.html')

#logout page
@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('home'))

#new post page
@app.route('/newpost', methods=['GET', 'POST'])
def newpost():
    if not g.user:
        return redirect(url_for('login'))
    
    if request.method == 'POST': #if post
        postername = request.form['postername']
        posterusername = request.form['posterusername']
        title = request.form['title']
        content = request.form['content']
        try:
            db.session.add(Posts(postername = postername, posterusername=posterusername,title = title, content = content, datecreated = date.today() ))
            db.session.commit()
            return redirect(url_for('home'))
            
        except:
            flash('Error posting')
            return redirect(url_for('newpost'))

    else: 
        return render_template('newpost.html')

#individual posts page
@app.route('/<string:username>/<int:id>')
def post(username,id):
    comments = Comments.query.filter_by(postid=id).all()
    comments.reverse()
    return render_template('post.html', info = Posts.query.filter_by(id=id).first(), comments=comments)

#deleting post
@app.route('/deletepost/<int:id>')
def deletepost(id):
    if not g.user:
        return redirect(url_for('home'))
    try:
        post_to_delete = Posts.query.get_or_404(id)
        comments = Comments.query.filter_by(postid=id).all()


        db.session.delete(post_to_delete)
        for comment in comments:
            db.session.delete(comment)
        db.session.commit()
        flash('Post succesfully deleted.')
        return redirect(url_for('home'))
    except:
        flash('There was an issue deleting the post.')
        return redirect(url_for('home'))

#editing post
@app.route('/editpost/<int:id>', methods=['GET','POST'])
def editpost(id):
    if not g.user:
        return redirect(url_for('home'))
    post_to_edit = Posts.query.get_or_404(id)
    if request.method == 'POST':
        post_to_edit.title = request.form['title']
        post_to_edit.content = request.form['content']
        try:
            db.session.commit()
            flash('Post succesfully edited.')
            return redirect(url_for('post', username=g.user.username,id=id))
        except:
            flash('There was an issue editing the post.')
            return redirect(url_for('post', username=g.user.username,id=id))

    else:
        return render_template('editpost.html', info = Posts.query.filter_by(id=id).first())

#new comment
@app.route('/comment/<int:id>', methods=['GET', 'POST'])
def comment(id):
    if not g.user:
        return redirect(url_for('login'))
    if request.method == 'POST':
        postid = id
        postername = request.form['postername']
        content = request.form['content']

        db.session.add(Comments(postid = postid, postername=postername, posterusername=g.user.username,content=content, datecreated=date.today() ))
        db.session.commit()
        return redirect(url_for('post', username=g.user.username,id=id))
    else: #GET
        return render_template('newcomment.html')

#deleting comments
@app.route('/deletecomment/<int:postid>/<int:id>')
def deletecomment(id,postid):
    if not g.user:
        return redirect(url_for('home'))
    try:
        comment_to_delete = Comments.query.get_or_404(id)
        db.session.delete(comment_to_delete)
        db.session.commit()
        flash('Comment succesfully deleted.')
        return redirect(url_for('post',username=g.user.username,id=postid))
    except:
        flash('There was an issue deleting the post.')
        return redirect(url_for('post',username=g.user.username,id=postid))

#editing comments
@app.route('/editcomment/<int:postid>/<int:id>', methods=['GET','POST'])
def editcomment(postid,id):
    if not g.user:
        return redirect(url_for('home'))
    comment_to_edit = Comments.query.get_or_404(id)
    if request.method == 'POST':
        comment_to_edit.content = request.form['content']
        try:
            db.session.commit()
            flash('Comment succesfully edited.')
            return redirect(url_for('post', username=g.user.username,id=postid))
        except:
            flash('There was an issue editing the comment.')
            return redirect(url_for('home'))

    else:
        return render_template('editcomment.html', info = Comments.query.filter_by(id=id).first())
    


if __name__ == '__main__':
    app.run(debug=True)
