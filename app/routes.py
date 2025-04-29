from flask import render_template, redirect, url_for, request
from app import app, db
from app.models import Movie, User
from flask import jsonify
from flask import flash
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash



@app.route("/")
@login_required
def index():
    filter_type = request.args.get('filter')
    sort = request.args.get('sort')

    query = Movie.query

    if filter_type == 'watched':
        query = query.filter_by(watched=True)
    elif filter_type == 'unwatched':
        query = query.filter_by(watched=False)

    if sort == 'title':
        query = query.order_by(Movie.title)
    elif sort == 'watched':
        query = query.order_by(Movie.watched.desc())

    movies = Movie.query.filter_by(user_id=current_user.id).all()
    return render_template("index.html", movies=movies)

@app.route("/add", methods=["GET", "POST"])
@login_required
def add():
    if request.method == "POST":
        title = request.form["title"]
        description = request.form.get("description")
        genre = request.form.get("genre")
        type_ = request.form.get("type")

        # Basic validation for type and genre
        if not genre or not type_:
            flash("❗ Please select both Genre and Type!")
            return render_template("add.html", 
                                title=title, 
                                description=description,
                                selected_genre=genre, 
                                selected_type=type_)

        new_movie = Movie(
            title=title,
            description=description,
            genre=genre,
            type=type_,
            user_id=current_user.id
        )
        db.session.add(new_movie)
        db.session.commit()
        flash("🎬 Movie/Show added successfully!")
        return redirect(url_for("index"))

    return render_template("add.html")


@app.route("/watched/<int:movie_id>")
@login_required
def watched(movie_id):
    movie = Movie.query.get_or_404(movie_id)
    movie.watched = True
    db.session.commit()
    flash("🎬 Movie marked as watched! Don't forget to rate it!")
    return redirect(url_for("index"))

@app.route("/delete/<int:movie_id>")
@login_required
def delete(movie_id):
    movie = Movie.query.get_or_404(movie_id)
    db.session.delete(movie)
    db.session.commit()
    return redirect(url_for("index"))

@app.route("/edit/<int:movie_id>", methods=["GET", "POST"])
@login_required
def edit(movie_id):
    movie = Movie.query.get_or_404(movie_id)
    if request.method == "POST":
        movie.title = request.form["title"]
        movie.description = request.form.get("description")
        movie.genre = request.form.get("genre")
        movie.rating = request.form.get("rating", type=int)
        db.session.commit()
        return redirect(url_for("index"))
    return render_template("edit.html", movie=movie)

@app.route("/rate/<int:movie_id>/<int:rating>", methods=["POST"])
@login_required
def rate(movie_id, rating):
    movie = Movie.query.get_or_404(movie_id)
    movie.rating = rating
    db.session.commit()
    return ('', 204)  # Empty response but successful


@app.route("/get_rating/<int:movie_id>")
def get_rating(movie_id):
    movie = Movie.query.get_or_404(movie_id)
    return jsonify({'rating': movie.rating})

@app.route("/stats")
def stats():
    movies = Movie.query.all()
    total_movies = len(movies)
    watched_movies = len([m for m in movies if m.watched])
    unwatched_movies = total_movies - watched_movies
    avg_rating = round(sum(m.rating for m in movies if m.rating > 0) / max(1, len([m for m in movies if m.rating > 0])), 2)

    # Count genres
    genre_count = {}
    for movie in movies:
        if movie.genre:
            genre_count[movie.genre] = genre_count.get(movie.genre, 0) + 1

    return render_template("stats.html",
                            total_movies=total_movies,
                            watched_movies=watched_movies,
                            unwatched_movies=unwatched_movies,
                            avg_rating=avg_rating,
                            genre_count=genre_count)

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash("❗ Username already exists. Please choose another.")
            return redirect(url_for('register'))
        hashed_password = generate_password_hash(password)
        new_user = User(username=username, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        flash("✅ Registration successful! Please log in.")
        return redirect(url_for('login'))
    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            flash("✅ Logged in successfully!")
            return redirect(url_for('index'))
        else:
            flash("❗ Invalid username or password.")
            return redirect(url_for('login'))
    return render_template("login.html")

@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("✅ Logged out successfully!")
    return redirect(url_for('login'))
