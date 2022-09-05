import os
from unicodedata import category
from flask import Flask, request, abort, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import random

from models import setup_db, Question, Category

QUESTIONS_PER_PAGE = 10


def get_and_format_categories():
    selection = Category.query.order_by(Category.id).all()
    categories = {}

    for category in selection:
        formatted_category = category.format()
        categories[formatted_category["id"]] = formatted_category["type"]

    return categories


def paginate_questions(request, selection):
    page = request.args.get("page", 1, type=int)
    start = (page - 1) * QUESTIONS_PER_PAGE
    end = start + QUESTIONS_PER_PAGE

    questions = [question.format() for question in selection]
    current_questions = questions[start:end]

    return current_questions


def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__)
    setup_db(app)
    CORS(app)

    @app.after_request
    def after_request(response):
        response.headers.add(
            "Access-Control-Allow-Headers", "Content-Type,Authorization,true"
        )
        response.headers.add(
            "Access-Control-Allow-Methods", "GET,PUT,POST,DELETE,OPTIONS"
        )
        return response

    @app.route("/categories")
    def retrieve_categories():

        return jsonify(
            {
                "success": True,
                "categories": get_and_format_categories(),
                "total_categories": len(get_and_format_categories()),
            }
        )

    @app.route("/categories/<int:category_id>/questions")
    def retrieve_question_by_category(category_id):

        selection = (
            Question.query.filter(Question.category == category_id)
            .order_by(Question.id)
            .all()
        )

        current_questions = paginate_questions(request, selection)

        if len(current_questions) == 0:
            abort(404)

        return jsonify(
            {
                "success": True,
                "questions": current_questions,
                "total_questions": len(selection),
                "current_category": current_questions[0]["category"],
            }
        )

    @app.route("/questions")
    def retrieve_questions():
        selection = Question.query.order_by(Question.id).all()
        current_questions = paginate_questions(request, selection)

        if len(current_questions) == 0:
            abort(404)

        return jsonify(
            {
                "success": True,
                "questions": current_questions,
                "total_questions": len(selection),
                "categories": get_and_format_categories(),
                "current_category": current_questions[0]["category"],
            }
        )

    @app.route("/questions/<int:question_id>", methods=["DELETE"])
    def delete_question(question_id):
        try:
            question = Question.query.filter(Question.id == question_id).one_or_none()

            if question is None:
                abort(404)

            question.delete()
            selection = Question.query.order_by(Question.id).all()
            current_questions = paginate_questions(request, selection)

            return jsonify(
                {
                    "success": True,
                    "deleted": question_id,
                    "questions": current_questions,
                    "total_questions": len(selection),
                }
            )

        except:
            abort(422)

    @app.route("/questions", methods=["POST"])
    def create_or_search_question():
        body = request.get_json()

        new_question = body.get("question", None)
        answer = body.get("answer", None)
        difficulty = body.get("difficulty", None)
        category = body.get("category", None)
        search = body.get("searchTerm", None)

        try:
            if search:
                selection = Question.query.order_by(Question.id).filter(
                    Question.question.ilike("%{}%".format(search))
                )
                current_questions = paginate_questions(request, selection)

                return jsonify(
                    {
                        "success": True,
                        "questions": current_questions,
                        "total_questions": len(selection.all()),
                    }
                )

            else:
                question = Question(
                    question=new_question,
                    answer=answer,
                    difficulty=difficulty,
                    category=category,
                )
                question.insert()

                selection = Question.query.order_by(Question.id).all()
                current_questions = paginate_questions(request, selection)

                return jsonify(
                    {
                        "success": True,
                        "created": question.id,
                        "questions": current_questions,
                        "total_questions": len(Question.query.all()),
                    }
                )

        except:
            abort(422)

    @app.route("/quizzes", methods=["POST"])
    def create_quiz_questions():
        try:
            body = request.get_json()

            previous_questions = body.get("previous_questions", None)
            quiz_category = body.get("quiz_category", None)

            selection = Question.query.filter(~Question.id.in_(previous_questions))

            if "id" in quiz_category:
                category = quiz_category["id"]
                if category:
                    selection = selection.filter(Question.category == category)

            selection = selection.all()
            question = None

            if len(selection):
                question = random.choice(selection)

            return jsonify(
                {
                    "success": True,
                    "question": question.format() if question else question,
                }
            )

        except:
            abort(422)

    @app.errorhandler(404)
    def not_found(error):
        return (
            jsonify({"success": False, "error": 404, "message": "resource not found"}),
            404,
        )

    @app.errorhandler(422)
    def unprocessable(error):
        return (
            jsonify({"success": False, "error": 422, "message": "unprocessable"}),
            422,
        )

    @app.errorhandler(400)
    def bad_request(error):
        return jsonify({"success": False, "error": 400, "message": "bad request"}), 400

    @app.errorhandler(405)
    def method_not_allowed(error):
        return (
            jsonify({"success": False, "error": 405, "message": "method not allowed"}),
            405,
        )

    return app
