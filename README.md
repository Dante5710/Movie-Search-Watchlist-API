Movie Search & Watchlist API 
A robust Flask-based backend application that allows users to search for movies,
view details merged from multiple external APIs, and manage a personalized, secure watchlist.

Key FeaturesIntelligent API Chaining: 
Seamlessly merges movie data from the OMDB API with official trailers fetched via the YouTube Data API v3 in a single endpoint.Secure Authentication: Implements JWT (JSON Web Tokens) for secure user sessions and password hashing with Werkzeug for data protection.Relational Data Management: Utilizes PostgreSQL to store user-specific watchlists with complete CRUD (Create, Read, Update, Delete) capabilities.Stats Dashboard: Advanced SQLAlchemy aggregation provides users with real-time analytics, including average IMDB ratings and their most-watched genres.Soft Delete & Trash System: Implements a professional-grade "soft delete" logic, allowing users to trash movies and restore them later instead of permanent removal.

Technical StackLanguage: Python 3.xFramework: FlaskDatabase: PostgreSQLORM: Flask-SQLAlchemyMigrations: Flask-MigrateAuthentication: Flask-JWT-Extended

Configure Environment VariablesCreate a .env file in the root directory and add your credentials:Code snippetDATABASE_URL=postgresql://username:password@localhost:5432/movie_api_db

JWT_SECRET_KEY=your_random_permanent_secret_key
OMDB_API_KEY=your_omdb_key
YOUTUBE_API_KEY=your_youtube_key



