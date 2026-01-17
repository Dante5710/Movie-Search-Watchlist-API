import os
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv
from models import db, MovieTask, User
import requests
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from flask_migrate import Migrate
from sqlalchemy import func
from datetime import datetime

load_dotenv()
app = Flask(__name__)


app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY')
jwt = JWTManager(app)

db.init_app(app)
migrate = Migrate(app, db)
with app.app_context():
    db.create_all()

OMDB_API_KEY = os.getenv('OMDB_API_KEY')
YOUTUBE_API_KEY = os.getenv('YOUTUBE_API_KEY')

@app.route('/register', methods = ['POST'])
def register():
    data = request.json
    if User.query.filter_by(username = data['username']).first():
        return jsonify({"message" : "User already exists"}), 400
    
    new_user = User(username = data['username'])
    new_user.set_password(data['password'])

    db.session.add(new_user)
    db.session.commit()

    return jsonify({"message" : "User created successfully"}), 201


@app.route('/login', methods = ["POST"])
def login():
    data = request.json
    username = data.get('username')
    password = data.get('password')

    user = User.query.filter_by(username = username).first()

    if user and user.check_password(password):
        access_token = create_access_token(identity = str(user.id))

        return jsonify({"access_token" : access_token}), 200
    return jsonify({"message" : "Invalid username or password"}), 401



@app.route('/search', methods = ['GET'])
@jwt_required()
def movie_search():
    title = request.args.get('title')
    if not title:
        return jsonify({"message": "Error title is required"}), 400
    
    url = f"http://www.omdbapi.com/?t={title}&apikey={OMDB_API_KEY}"
    response = requests.get(url).json()


    if response.get('Response') == 'False':
        return jsonify({'error': 'Movie not found'}), 404
    
    youtube_url =  "https://www.googleapis.com/youtube/v3/search"
    params = {
        'part' : 'snippet',
        'q' : f"{response.get('Title')} official trailer",
        'type' : 'Video',
        'maxResults' : 1,
        'key' : YOUTUBE_API_KEY
    }
    yt_res = requests.get(youtube_url, params=params).json()

    video_id = yt_res['items'][0]['id']['videoId'] if yt_res.get('items') else ""
    trailer_link = f"https://www.youtube.com/watch?v={video_id}" if video_id else ""
    return jsonify({
        'title' : response.get('Title'),
        'year' : response.get("Year"),
        'plot' : response.get('Plot'),
        'genre' : response.get('Genre'),
        'poster_url' : response.get('Poster'),
        'trailer_link' : trailer_link,
        'imdb_rating' : response.get('imdbRating')
    })


@app.route('/tasks', methods = ['POST'])
@jwt_required()
def add_movie_task():
    current_user_id = get_jwt_identity()
    data = request.json
    
    new_task = MovieTask(
        title = data['title'],
        year = data.get('year'),
        plot = data.get('plot'),
        imdb_rating = data.get('imdb_rating'),
        poster_url = data.get('poster_url'),
        category = data.get('category', 'General'),
        user_id = current_user_id,
        status = 'pending',
        trailer_link = data.get('trailer_link')
    )

    db.session.add(new_task)
    db.session.commit()
    return jsonify(new_task.to_dict()), 201


@app.route('/tasks', methods = ["GET"])
@jwt_required()
def get_tasks():
    current_user_id = get_jwt_identity()
    status_filter = request.args.get('status')
    category_filter = request.args.get('category')
    sort_by = request.args.get('sort')

    query = MovieTask.query.filter_by(user_id = current_user_id, deleted_at = None)

    if status_filter:
        query = query.filter_by(status = status_filter)
    if category_filter:
        query = query.filter_by(category = category_filter)

    if sort_by == 'year':
        query = query.order_by(MovieTask.year.desc())
    else:
        query = query.order_by(MovieTask.id.desc())

    tasks = query.all()
    return jsonify([task.to_dict() for task in tasks])


@app.route('/tasks/<int:id>/restore', methods = ["POST"])
@jwt_required()
def restore_task(id):
    current_user_id = get_jwt_identity()

    task = MovieTask.query.filter_by(id = id, user_id = current_user_id).first_or_404()

    if task.deleted_at is None:
        return jsonify({"message" : "Movie is already active"}), 400
    
    task.deleted_at = None
    db.session.commit()

    return jsonify({"message" : "Movie successfully restored to your watchlist!"}), 200


@app.route('/tasks/trash', methods = ['GET'])
@jwt_required()
def get_trash():
    current_user_id = get_jwt_identity()

    deleted_tasks = MovieTask.query.filter(
        MovieTask.user_id == current_user_id,
        MovieTask.deleted_at != None
    ).all()

    return jsonify([task.to_dict() for task in deleted_tasks])


@app.route('/tasks/<int:id>/permanent', methods = ['DELETE'])
@jwt_required()
def permanent_delete(id):
    current_user_id = get_jwt_identity()

    task = MovieTask.query.filter_by(id = id, user_id = current_user_id).first_or_404()

    db.session.delete(task)
    db.session.commit()

    return jsonify({"message" : "Movie is permanently deleted from the database."}), 200



@app.route('/tasks/stats', methods=['GET'])
@jwt_required()
def get_movie_stats():
    current_user_id = get_jwt_identity()

    total_movies = MovieTask.query.filter_by(user_id=current_user_id, deleted_at=None).count()

    watched_count = MovieTask.query.filter_by(user_id=current_user_id, status='watched', deleted_at=None).count()

    pending_count = MovieTask.query.filter_by(user_id=current_user_id, status='pending', deleted_at=None).count()

    # Average Rating Calculation
    avg_rating = db.session.query(func.avg(func.cast(MovieTask.imdb_rating, db.Float))).filter(
        MovieTask.user_id == current_user_id,
        MovieTask.imdb_rating != None,
        MovieTask.deleted_at == None
    ).scalar()

    # Genre Aggregation
    top_genre_query = db.session.query(
        MovieTask.category, func.count(MovieTask.category).label('qty')
    ).filter(
        MovieTask.user_id == current_user_id,
        MovieTask.deleted_at == None
    ).group_by(MovieTask.category).order_by(db.desc('qty')).first()

    top_genre = top_genre_query[0] if top_genre_query else "N/A"

    return jsonify({
        "total_saved": total_movies,
        "breakdown": {
            "watched": watched_count,
            "pending": pending_count
        },
        "average_imdb_score": round(avg_rating, 2) if avg_rating else 0,
        "favourite_genre": top_genre
    }), 200




@app.route('/tasks/<int:id>', methods = ["PUT"])
@jwt_required()
def update_task(id):
    current_user_id = get_jwt_identity()

    task = MovieTask.query.filter_by(id = id, user_id = current_user_id).first_or_404()

    data = request.json

    task.status = data.get('status', task.status)
    task.category  = data.get('category', task.category)

    db.session.commit()
    return jsonify(task.to_dict())

@app.route('/tasks/<int:id>', methods = ["DELETE"])
@jwt_required()
def delete_task(id):
    current_user_identity = get_jwt_identity()
    task = MovieTask.query.filter_by(id = id, user_id = current_user_identity).first_or_404()
    task.deleted_at = datetime.utcnow()
    db.session.commit()
    db.session.commit()

    return jsonify({"message": "Task deleted successfully!"})

if __name__ == '__main__':
    app.run(debug = True)




