import os
from flask import Flask, render_template, redirect, url_for, request, Response, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_security import Security, SQLAlchemyUserDatastore, UserMixin, RoleMixin, login_required, roles_required, current_user
from sqlalchemy import text
from flask_security.forms import LoginForm,RegisterForm, StringField, get_form_field_label, Required, PasswordField, password_required, BooleanField, SubmitField,email_required, email_validator,unique_user_email,password_length,EqualTo, _datastore,get_message,requires_confirmation,verify_and_update_password
"""from mutagen.mp3 import MP3
from mutagen.id3 import ID3"""
import time
import threading
import multiprocessing




# Create app
app = Flask(__name__)
app.config['DEBUG'] = True
app.config['SECRET_KEY'] = 'super-secret'
current_dir=os.path.abspath(os.path.dirname(__file__))
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///"+os.path.join(current_dir,"jazz.sqlite3")
app.config['SECURITY_REGISTERABLE']=True
app.config['SECURITY_PASSWORD_HASH']='bcrypt'
app.config['SECURITY_PASSWORD_SALT']='super-secret'
app.config['SECURITY_SEND_REGISTER_EMAIL']=False
UPLOAD_FOLDER = "static/audio/"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# Create database connection object
db = SQLAlchemy(app)

# Define models
roles_users = db.Table('roles_users',
        db.Column('user_id', db.Integer(), db.ForeignKey('user.id')),
        db.Column('role_id', db.Integer(), db.ForeignKey('role.id')))

class Role(db.Model, RoleMixin):
    __tablename__='role'
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(80), unique=True)
    description = db.Column(db.String(255))

class User(db.Model, UserMixin):
    __tablename__='user'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    email = db.Column(db.String(255), unique=True)
    password = db.Column(db.String(255))
    active = db.Column(db.Boolean())
    roles = db.relationship('Role', secondary=roles_users,
                            backref=db.backref('users', lazy='dynamic'))
    
class Song(db.Model):
    __tablename__='song'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    title = db.Column(db.String, nullable=False)
    singers = db.Column(db.String, nullable=False)
    date = db.Column(db.String, nullable=False)
    lyrics = db.Column(db.String(255))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    album_id = db.Column(db.Integer, db.ForeignKey('album.id'))

class Playlist(db.Model):
    __tablename__='playlist'
    id = db.Column(db.Integer, primary_key=True, autoincrement= True)
    name = db.Column(db.String)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

class playlist_song(db.Model):
    __tablename__='playlist_song'
    playlist_id= db.Column(db.Integer, db.ForeignKey('playlist.id'), primary_key=True )
    song_id= db.Column(db.Integer, db.ForeignKey('song.id'), primary_key=True )

class Album(db.Model):
    __tablename__='album'
    id = db.Column(db.Integer, primary_key=True, autoincrement= True)
    name = db.Column(db.String, nullable= False)
    genre = db.Column(db.String)
    artist = db.Column(db.String)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

class album_song(db.Model):
    __tablename__='album_song'
    album_id=db.Column(db.Integer, db.ForeignKey('album.id'), primary_key=True)
    song_id=db.Column(db.Integer, db.ForeignKey('song.id'), primary_key=True)

class ExtendedLoginForm(LoginForm):
    email = StringField(get_form_field_label('email'),
                        validators=[Required(message='EMAIL_NOT_PROVIDED')],render_kw={'type':'email','class':'form-control','id':'inputEmail3'})
    password = PasswordField(get_form_field_label('password'),
                             validators=[password_required],render_kw={'type':"password",'class':"form-control",'id':"inputPassword3"})
    remember = BooleanField(get_form_field_label('remember_me'),render_kw={'class':"form-check-input",'type':"checkbox",'id':"gridCheck1"})
    submit = SubmitField(get_form_field_label('login'),render_kw={'class':"btn btn-outline-success",'style':'font-family:Raleway;font-weight:bolder;font-size:larger'})
    def validate(self,extra_validators=None):
        if not super(LoginForm, self).validate():
            return False

        self.user = _datastore.get_user(self.email.data)

        if self.user is None:
            self.email.errors.append(get_message('USER_DOES_NOT_EXIST')[0])
            return False
        if not self.user.password:
            self.password.errors.append(get_message('PASSWORD_NOT_SET')[0])
            return False
        if not verify_and_update_password(self.password.data, self.user):
            self.password.errors.append(get_message('INVALID_PASSWORD')[0])
            return False
        if requires_confirmation(self.user):
            self.email.errors.append(get_message('CONFIRMATION_REQUIRED')[0])
            return False
        if not self.user.is_active:
            self.email.errors.append(get_message('DISABLED_ACCOUNT')[0])
            return False
        return True



class ExtendedRegisterForm(RegisterForm):
    email = StringField(
        get_form_field_label('email'),
        validators=[email_required, email_validator, unique_user_email],render_kw={'type':'email','class':'form-control','id':'inputEmail3'})
    password = PasswordField(
        get_form_field_label('password'),
        validators=[password_required, password_length],render_kw={'type':"password",'class':"form-control",'id':"inputPassword3"})
    password_confirm = PasswordField(
        get_form_field_label('retype_password'),
        validators=[EqualTo('password', message='RETYPE_PASSWORD_MISMATCH'),
                    password_required],render_kw={'type':"password",'class':"form-control",'id':"inputPassword3"})
    submit = SubmitField(get_form_field_label('register'),render_kw={'class':"btn btn-outline-success",'style':'font-family:Raleway;font-weight:bolder;font-size:larger'})


# Setup Flask-Security
user_datastore = SQLAlchemyUserDatastore(db, User, Role)
security = Security(app, user_datastore, login_form=ExtendedLoginForm, register_form=ExtendedRegisterForm)



# Views
@app.route('/')
def home():
    query=text('select * from song')
    songs=db.session.execute(query).fetchall()[:9]
    query=text('select * from album')
    albums=db.session.execute(query).fetchall()[:9]
    if current_user.is_authenticated:
        query=text('select * from playlist where user_id={}'.format(current_user.id))
        playlists=db.session.execute(query).fetchall()
        return render_template('index.html',songs=songs, playlists=playlists, albums=albums)
    else:
        return render_template('index.html',songs=songs, albums=albums)


@app.route('/watch/<int:id>',methods=['GET','POST'])
@login_required

def watch(id):
    if request.method=='GET':
        query=text('select * from song where id={}'.format(id))
        song=db.session.execute(query).fetchone()

        
        query=text('select * from song where id!={}'.format(id))
        songs=db.session.execute(query).fetchall()

        # songs.insert(0,song)

        # next_song=songs[0].id
        # print(next_song)

        query=text('select * from playlist where user_id={}'.format(current_user.id))
        playlists=db.session.execute(query).fetchall()

        # duration=5

        # time.sleep(duration)

        # song_path=str("static/audio/"+song.title+'.mp3')

        # extract duration of time
        # Specify the path to your MP3 file
        # mp3_file_path = song_path

        # Create an MP3 object to read the file
        # audio = MP3(mp3_file_path)

        # duration = audio.info.length  # Duration in seconds
        # print("Duration (seconds):", duration)       


        # for song in songs:
        # play(song, songs, playlists)
                    
        template= render_template("play_playlist.html",song=song,song_name=str(song.title+'.mp3'),all_songs=songs,playlists=playlists)
        response=Response(template)
        # yield response
        return response
        


# def wait_for_time(duration_in_seconds,song_id):
#     try:
#         duration_in_seconds = float(duration_in_seconds)
#         if duration_in_seconds <= 0:
#             return "Input must be a positive number of seconds."

#         print(f"Waiting for {duration_in_seconds} seconds...")
#         time.sleep(duration_in_seconds)
#         return 
#     except ValueError:
#         return "Invalid input. Please provide a valid number of seconds."

@app.route('/creator',methods=['GET','POST'])
@login_required

def creator():
    if request.method=='GET':
        query=text("select * from roles_users where user_id={}".format(current_user.id))
        result=db.session.execute(query).fetchall()
        if result==[]:
            return render_template("register_as_creator.html")
        else:
            query=text('select * from song where user_id={}'.format(current_user.id))
            songs=db.session.execute(query).fetchall()
            query=text('select * from album where user_id={}'.format(current_user.id))
            albums=db.session.execute(query).fetchall()
            return render_template('creator_page.html',songs=songs,albums=albums)
        
    elif request.method=='POST':
        query=text('insert into roles_users values({},{})'.format(current_user.id,2))
        db.session.execute(query)
        db.session.commit()
        return redirect(url_for('creator'))

@app.route('/upload_song',methods=['GET','POST'])
@login_required
@roles_required('creator')

def upload_song():
    if request.method=='GET':
        return render_template('song.html')
    elif request.method=='POST':
        title=request.form['title']
        singers=request.form['singers']
        date=request.form['date']
        lyrics=request.form['lyrics']
        file=request.files['audio']

        if file.filename == "":
            return "No selected file"


        file.filename=str(title+'.mp3')
        # Ensure the target directory exists
        if not os.path.exists(app.config["UPLOAD_FOLDER"]):
            os.makedirs(app.config["UPLOAD_FOLDER"])

        # Save the uploaded file to the specified directory
        file.save(os.path.join(app.config["UPLOAD_FOLDER"], file.filename))
        song=Song(title=title, singers=singers, date=date, lyrics=lyrics, user_id=current_user.id)
        db.session.add(song)

        db.session.commit()
        return redirect(url_for('creator'))
    

@app.route('/show_all')

def show_all():
    return render_template('show_all.html')

@app.route('/create_playlist',methods=['GET','POST'])

def create_playlist():
    if request.method=="GET":
        query=text('select * from song')
        songs=db.session.execute(query).fetchall()
        return render_template('playlist.html',songs=songs)
    
    elif request.method=='POST':
        songs=[]
        name=request.form['name']
        songs=request.form.getlist('songs')  
        # songs=map(int, songs)
        # print(list(songs))
        playlist=Playlist(name=name, user_id=current_user.id)
        db.session.add(playlist)
        db.session.commit()
        query=text('select * from playlist where name="{}" and user_id={}'.format((name),current_user.id))
        playlist=db.session.execute(query).fetchone()

        for i in songs:

            add_to_playlist(playlist.id,i)
        # query=text('insert into playlist values({},{})'.format(current_user.id,2))
        # db.session.execute(query)
        # db.session.commit() 

        return redirect(url_for('home'))

@app.route('/playlist/edit/<int:playlist_id>',methods=['GET','POST'])

def playlist(playlist_id):
    if request.method=='GET':
        query=text('select * from playlist where id={}'.format(playlist_id))
        playlist=db.session.execute(query).fetchone()

        query=text('select * from playlist_song,song where playlist_song.song_id=song.id and playlist_song.playlist_id={}'.format(playlist_id))
        songs=db.session.execute(query)

        return render_template('playlist.html',playlist=playlist, songs=songs)
    
    elif request.method=='POST':
        name=request.form['name']
        query=text('update playlist set name="{}" where id={}'.format(name,playlist_id))
        db.session.execute(query)
        db.session.commit()
        return redirect(url_for('home'))
    
    
    
@app.route('/playlist/delete/<int:playlist_id>')

def delete_playlist(playlist_id):
    
    query=text('delete from playlist_song where playlist_id={}'.format(playlist_id))
    db.session.execute(query)

    query=text('delete from playlist where id={}'.format(playlist_id))
    db.session.execute(query)
    db.session.commit()
    return redirect(url_for('home'))

@app.route('/delete_from_playlist/<int:playlist_id>/<int:song_id>')

def delete_from_playlist(playlist_id,song_id):
    query = text('delete from playlist_song where playlist_id={} and song_id={}'.format(playlist_id,song_id))
    db.session.execute(query)
    db.session.commit()

    return redirect(url_for('playlist',playlist_id=playlist_id))





# @app.route('/playlist/add_song/<int:playlist_id>/<int:song_id>')
def add_to_playlist(playlist_id, song_id):
    # add to playlist
    print('playlist_id : ',playlist_id,'song_id : ',song_id)
    query=text('select * from playlist_song where playlist_id={} and song_id={}'.format(playlist_id,song_id))
    result=db.session.execute(query).fetchall()
    print('result : ',result)
    if result==[]:
        print(playlist_id,song_id)
        song= playlist_song(playlist_id=playlist_id,song_id=song_id)
        db.session.add(song)
        db.session.commit()
    return
    # return redirect(url_for('home'))
 
@app.route('/play_playlist/<int:playlist_id>/<int:song_id>')

def play_playlist(playlist_id,song_id):
    if request.method=='GET':
        query=text('select * from song where id={}'.format(song_id))
        song=db.session.execute(query).fetchone()

        # playlists={}

        query=text('select * from playlist where user_id={} and playlist.id!={}'.format(current_user.id,playlist_id))
        playlists=db.session.execute(query).fetchall()

        # print(playlists)
        # for playlist in playlists:


        query=text('select * from playlist where id={}'.format(playlist_id))
        playlist=db.session.execute(query).fetchone()

        query=text('select * from playlist_song,song where playlist_song.song_id=song.id and playlist_song.playlist_id={} and song_id!={}'.format(playlist_id,song_id))
        songs=db.session.execute(query)

        query=text('select * from song where id!={}'.format(song_id))
        all_songs=db.session.execute(query).fetchall()

        return render_template('play_playlist.html',playlist=playlist,song_name=str(song.title+'.mp3'),songs=songs,song=song,all_songs=all_songs,playlists=playlists)

@app.route('/album/create',methods=['GET','POST'])

@login_required
@roles_required('creator')

def create_album():
    if request.method=='GET':
        query=text('select * from song where user_id={}'.format(current_user.id))
        songs=db.session.execute(query).fetchall()
        return render_template('album.html',songs=songs)
    
    elif request.method=='POST':
        name=request.form['name']
        genre=request.form['genre']
        artist=request.form['artist']
        songs=request.form.getlist('songs')

        album=Album(name=name, genre=genre, artist=artist, user_id=current_user.id)

        db.session.add(album)
        db.session.commit()

        query=text('select * from album where name="{}" and genre="{}" and artist="{}" and user_id={}'.format(name, genre, artist, current_user.id))
        album=db.session.execute(query).fetchone()

        for song_id in songs:
            add_to_album(song_id,album.id)

        
        return redirect(url_for('creator'))
    
def add_to_album(song_id, album_id):
    song=album_song(album_id=album_id, song_id=song_id)
    db.session.add(song)
    db.session.commit()
    return 


    
    
@app.route('/album/edit/<int:album_id>',methods=['GET','POST'])
@login_required
@roles_required('creator')

def edit_album(album_id):
    if request.method=='GET':
        query=text('select * from album where id={}'.format(album_id))
        album=db.session.execute(query).fetchone()

        query=text('select * from album, album_song, song where album.id=album_song.album_id and album_song.song_id=song.id and album.user_id={} and album_song.album_id={}'.format(current_user.id,album_id))
        album_songs=db.session.execute(query).fetchall()

        query=text('select * from song where user_id={} and song.id not in (select song_id from album_song where album_id={})'.format(current_user.id,album_id))
        songs=db.session.execute(query).fetchall()
        

        return render_template('album.html',album=album, album_songs=album_songs, songs=songs)
    
    elif request.method=='POST':
        name=request.form['name']
        genre=request.form['genre']
        artist=request.form['artist']

        # print(name, genre, artist)
        songs=request.form.getlist('songs')

        for song_id in songs:
            add_to_album(song_id, album_id)
        # print(songs)

        query=text('update album set name="{}", genre="{}", artist="{}" where id={}'.format(name, genre, artist, album_id))
        db.session.execute(query)
        db.session.commit()
        return redirect (url_for('edit_album',album_id=album_id))
    
@app.route('/album/delete_song/<int:album_id>/<int:song_id>')

def delete_from_album(song_id,album_id):
    query=text('delete from album_song where song_id={} and album_id={}'.format(song_id,album_id))
    db.session.execute(query)
    db.session.commit()
    return redirect(url_for('edit_album',album_id=album_id))

@app.route('/album/delete/<int:album_id>')

def delete_album(album_id):
    query=text('delete from album_song where album_id={}'.format(album_id))
    db.session.execute(query)
    query=text('delete from album where id={}'.format(album_id))
    db.session.execute(query)
    db.session.commit()
    return redirect('/creator')

if __name__ == '__main__':
    app.run()

