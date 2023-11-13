from flask import Flask, render_template, redirect, url_for, request
from flask_bootstrap import Bootstrap5
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired
import requests



app = Flask(__name__)
app.config['SECRET_KEY'] = ''
Bootstrap5(app)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///movie-collection.db'
db = SQLAlchemy()
db.init_app(app)


class Edit(FlaskForm):
    new_rating = StringField('Your Rating out of 10 e.g. 7.5',validators=[DataRequired()])
    new_review = StringField('Your Review')
    submit = SubmitField('Done')

class Add(FlaskForm):
    movie_name = StringField("Movie Title",validators=[DataRequired()])
    submit = SubmitField('Add Movie')

class Movie(db.Model):
    id = db.Column(db.Integer,primary_key=True)
    title = db.Column(db.String(250), unique=True, nullable=False)
    year = db.Column(db.String(250), nullable=False)
    description = db.Column(db.String(1000), nullable=False)
    rating = db.Column(db.Float, nullable=True)
    ranking = db.Column(db.Integer, nullable=True)
    review = db.Column(db.String(250), nullable=True)
    img_url = db.Column(db.String(250), nullable=False)


with app.app_context():
    db.create_all()

@app.route("/")
def home():
    movie_list = db.session.execute(db.select(Movie).order_by(Movie.rating)).scalars()
    id_list = []

    final_list = []

    for movie in movie_list:
        id_list.append(int(movie.id))


    list_sorted = id_list[::-1]

    for movie in list_sorted:
        movie_dets = db.get_or_404(Movie,movie)
        movie_dets.ranking = (list_sorted.index(movie) + 1)
        db.session.commit()
    final_list = db.session.execute(db.select(Movie).order_by(Movie.ranking)).scalars()
    return render_template("index.html", movies=final_list)

@app.route("/edit",methods=['GET','POST'])
def edit():
    # movie_list = Movie.query.all()
    form = Edit()
    # if request.method == 'POST':
    movie_id = request.args.get('movie_id')
    movie_to_update = db.get_or_404(Movie, movie_id)
    # print(movie_to_update)
    if form.validate_on_submit():
        movie_to_update.rating = float(form.new_rating.data)
        movie_to_update.review = form.new_review.data
        db.session.commit()
        return redirect(url_for('home'))
    return render_template("edit.html", form=form, movie=movie_to_update)

@app.route("/delete", methods=['GET', 'POST'])
def delete():
    movie_id = request.args.get('movie_id')
    movie_to_del = db.get_or_404(Movie,movie_id)
    db.session.delete(movie_to_del)
    db.session.commit()
    return redirect(url_for('home'))


@app.route("/add", methods=['POST', 'GET'])
def add():
    add_form = Add()
    if add_form.validate_on_submit():
        movie_name = str(add_form.movie_name.data)
        string = movie_name.replace(' ','%20')

        movie_url = f'https://api.themoviedb.org/3/search/movie?query={string}&include_adult=false'
        headers = {
            "accept": "application/json",
            "Authorization": "Bearer eyJhbGciOiJIUzI1NiJ9.eyJhdWQiOiIxMjc4OWQ0Y2ZlZWFkMWI5N2ZkNWNjZTA3MGQ0YjQ3NyIsInN1YiI6IjY1MjMwODNmYjNmNmY1MDBlMjk2NzQ3MiIsInNjb3BlcyI6WyJhcGlfcmVhZCJdLCJ2ZXJzaW9uIjoxfQ.qY-nI5wdkatrj37ZK_GUFalKvoPBX8stFC1XHrQ2RWc"
        }
        response = requests.get(movie_url, headers=headers)
        response_data = response.json()
        movie_data = response_data["results"]
        #
        movie_list = []
        movie_img_url = "https://image.tmdb.org/t/p/w500"

        for movie in movie_data:
            details = {
                'id': f"{movie['id']}",
                'title': f"{movie['original_title']}",
                'year': movie['release_date'][:4],
                'description': movie['overview'],
                'url': f"{movie_img_url}{movie['backdrop_path']}"
            }
            movie_list.append(details)

        return render_template('select.html',movie_list=movie_list)
    return render_template("add.html",form=add_form)


@app.route("/select", methods=['GET', 'POST'])
def select():

    new_movie = Movie(
        title=request.args.get('title'),
        img_url=request.args.get('url'),
        year=request.args.get('year'),
        description=request.args.get('description')
    )
    db.session.add(new_movie)
    db.session.commit()
    return redirect(url_for('edit',movie_id=new_movie.id))



if __name__ == '__main__':
    app.run(debug=True)
