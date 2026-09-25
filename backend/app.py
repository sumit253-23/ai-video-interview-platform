from flask import Flask
from flask_cors import CORS

from config import Config
from extensions import db, jwt
from routes.auth import auth_bp
from routes.resume import resume_bp
from models.interview import Interview

from models.interview_answer import InterviewAnswer
from models.interview_question import InterviewQuestion
# Import models
from models.user import User
from models.resume_analysis import ResumeAnalysis
from models.job_match import JobMatch
from routes.question import question_bp
from routes.recording import recording_bp
from routes.job_matching import job_matching_bp


def create_app():
    app = Flask(__name__)

    # Configuration
    app.config.from_object(Config)

    # Initialize extensions
    db.init_app(app)
    jwt.init_app(app)

    # Enable CORS
    CORS(app)
    app.register_blueprint(auth_bp)
    app.register_blueprint(resume_bp) 
    app.register_blueprint(question_bp)
    app.register_blueprint(recording_bp)
    app.register_blueprint(job_matching_bp)
     
    @app.route("/")
    def home():
        return {
            "status": "success",
            "message": "AI Video Interview Platform Backend is running"
        }

    @app.route("/db-test")
    def db_test():
        try:
            db.session.execute(db.text("SELECT 1"))

            return {
                "status": "success",
                "message": "PostgreSQL connected successfully"
            }

        except Exception as e:
            return {
                "status": "error",
                "message": str(e)
            }, 500

    return app


# Create Flask application
app = create_app()


# Create database tables
with app.app_context():
    db.create_all()
    print("Database tables created successfully")


if __name__ == "__main__":
    app.run(debug=True)