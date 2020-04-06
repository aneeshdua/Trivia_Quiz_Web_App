import os
from flask import Flask, request, abort, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import random

from models import setup_db, Question, Category

QUESTIONS_PER_PAGE = 10

# method to paginate questions
def paginate_questions(request, selection):
  page = request.args.get('page', 1, type=int)
  start = (page - 1) * QUESTIONS_PER_PAGE
  end = start + QUESTIONS_PER_PAGE

  questions = [question.format() for question in selection]
  current_questions = questions[start:end]

  return current_questions


def create_app(test_config=None):
  # create and configure the app
  app = Flask(__name__)
  setup_db(app)
  
  '''
  @TODO: Set up CORS. Allow '*' for origins. Delete the sample route after completing the TODOs
  '''
  #CORS(app)
  CORS(app, resources={'/': {'origins': '*'}})
  

  '''
  @TODO: Use the after_request decorator to set Access-Control-Allow
  '''
  @app.after_request
  def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers','Content-Type, Authorization,true')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PATCH,POST,DELETE,OPTIONS')
    return response


  '''
  @TODO: 
  Create an endpoint to handle GET requests 
  for all available categories.
  '''
  @app.route('/categories', methods=['GET'])
  def get_categories():
    categories = Category.query.all()
    categories_dict = {}
    for category in categories:
        categories_dict[category.id] = category.type

    # abort 404 if no categories found
    if (len(categories_dict) == 0):
        abort(404)

    return jsonify({
      'success': True,
      'categories': categories_dict
    })

  '''
  @TODO: 
  Create an endpoint to handle GET requests for questions, 
  including pagination (every 10 questions). 
  This endpoint should return a list of questions, 
  number of total questions, current category, categories. 

  TEST: At this point, when you start the application
  you should see questions and categories generated,
  ten questions per page and pagination at the bottom of the screen for three pages.
  Clicking on the page numbers should update the questions. 
  '''
  @app.route('/questions',methods=['GET'])
  def get_questions():
    selection = Question.query.all()
    total_questions = len(selection)
    current_questions = paginate_questions(request, selection)

    # get all categories and add to dict
    categories = Category.query.all()
    categories_dict = {}
    for category in categories:
        categories_dict[category.id] = category.type

    # abort 404 if no questions
    if (len(current_questions) == 0):
        abort(404)

    # return data to view
    return jsonify({
        'success': True,
        'questions': current_questions,
        'total_questions': total_questions,
        'categories': categories_dict
    })

  '''
  @TODO: 
  Create an endpoint to DELETE question using a question ID. 

  TEST: When you click the trash icon next to a question, the question will be removed.
  This removal will persist in the database and when you refresh the page. 
  '''
  @app.route('/questions/<int:id>',methods=['DELETE'])
  def delete_question(id):
    try:  
      question = Question.query.filter_by(id=id).one_or_none()

      # abort 404 if no question found
      if question is None:
          abort(404)

      # delete the question
      question.delete()

      # return success response
      return jsonify({
          'success': True,
          'deleted': id
      })

    except:
      # abort if problem deleting question
      abort(422)

  '''
  @TODO: 
  Create an endpoint to POST a new question, 
  which will require the question and answer text, 
  category, and difficulty score.

  TEST: When you submit a question on the "Add" tab, 
  the form will clear and the question will appear at the end of the last page
  of the questions list in the "List" tab.  
  '''

  '''
  @TODO: 
  Create a POST endpoint to get questions based on a search term. 
  It should return any questions for whom the search term 
  is a substring of the question. 

  TEST: Search by any phrase. The questions list will update to include 
  only question that include that string within their question. 
  Try using the word "title" to start. 
  '''

  @app.route('/questions', methods=['POST'])
  def new_question():
    body = request.get_json()

    # if search term is present
    if (body.get('searchTerm')):
        search_term = body.get('searchTerm')

        # query the database using search term
        selection = Question.query.filter(
            Question.question.ilike(f'%{search_term}%')).all()

        # 404 if no results found
        if (len(selection) == 0):
            abort(404)

        # paginate the results
        paginated = paginate_questions(request, selection)

        # return results
        return jsonify({
            'success': True,
            'questions': paginated,
            'total_questions': len(Question.query.all())
        })

    else:
      body = request.get_json()
      new_question = body.get('question', None)
      new_answer = body.get('answer', None)
      new_difficulty = body.get('difficulty', None)
      new_category = body.get('category', None)

      if ((new_question is None) or (new_answer is None)
                      or (new_difficulty is None) or (new_category is None)):
                  abort(422)

      try:
        question = Question(question=new_question, answer = new_answer, category = new_category,difficulty = new_difficulty)
        question.insert()

        selection = Question.query.order_by(Question.id).all()
        current_questions = paginate_questions(request, selection)

        # return data to view
        return jsonify({
            'success': True,
            'created': question.id,
            'question_created': question.question,
            'questions': current_questions,
            'total_questions': len(Question.query.all())
        })
      except:
          # abort unprocessable if exception
          abort(422)

  

  '''
  @TODO: 
  Create a GET endpoint to get questions based on category. 

  TEST: In the "List" tab / main screen, clicking on one of the 
  categories in the left column will cause only questions of that 
  category to be shown. 
  '''
  @app.route('/categories/<int:id>/questions', methods=['GET'])
  def get_categorized_questions(id):
    category = Category.query.filter_by(id=id).one_or_none()

    if (category is None):
      abort(400)

    # get the matching questions
    selection = Question.query.filter_by(category=category.id).all()
    paginated = paginate_questions(request, selection)

    return jsonify({
      'success': True,
      'questions': paginated,
      'total_questions': len(paginated),
      'current_category': category.type
    })

  '''
  @TODO: 
  Create a POST endpoint to get questions to play the quiz. 
  This endpoint should take category and previous question parameters 
  and return a random questions within the given category, 
  if provided, and that is not one of the previous questions. 

  TEST: In the "Play" tab, after a user selects "All" or a category,
  one question at a time is displayed, the user is allowed to answer
  and shown whether they were correct or not. 
  '''
  @app.route('/quizzes', methods=['POST'])
  def get_for_quiz():
    body = request.get_json()
    previous_questions = body.get('previous_questions',None)
    quiz_category = body.get('quiz_category', None)

    if (quiz_category['id'] == 0):
      questions = Question.query.all()
    else:
      questions = Question.query.filter_by(category=quiz_category['id']).all()

    total = len(questions)

    # picks a random question
    def get_random_question():
        return questions[random.randrange(0, len(questions), 1)]

    def check_in_previous(question):
      is_new = False
      for q in previous_questions:
          if (q == question.id):
              is_new = True

      return is_new

    question = get_random_question()

    # check if used, execute until unused question found
    while(check_in_previous(question)):
        question = get_random_question()

        # if all questions have been tried, return without question
        # necessary if category has <5 questions
        if (len(previous_questions) == total):
            return jsonify({
                'success': True
            })

    # return the question
    return jsonify({
        'success': True,
        'question': question.format()
    })      

  '''
  @TODO: 
  Create error handlers for all expected errors 
  including 404 and 422. 
  '''
  
  @app.errorhandler(404)
  def not_found(error):
    return jsonify({
        "success": False,
        "error": 404,
        "message": "resource not found"
      }), 404

  @app.errorhandler(422)
  def unprocessable(error):
      return jsonify({
          "success": False,
          "error": 422,
          "message": "unprocessable"
      }), 422

  @app.errorhandler(400)
  def bad_request(error):
      return jsonify({
          "success": False,
          "error": 400,
          "message": "bad request"
      }), 400

  return app

    