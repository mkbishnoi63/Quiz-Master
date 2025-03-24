from flask import request, render_template, redirect, session, url_for, flash
from werkzeug.security import generate_password_hash, check_password_hash
from flask_restful import Api, Resource
from flask import current_app as app
import matplotlib.pyplot as plt
from datetime import datetime
from models.model import *

api = Api(app)

@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        this_user = user.query.filter_by(username=username).first()
        if this_user and check_password_hash(this_user.password, password):
            session['username'] = username
            if this_user.type == 'admin':
                subjects = Subject.query.order_by(Subject.id).all()
                chapters = Chapter.query.all()
                return render_template('admin_dash.html', username=username, subjects=subjects, chapters=chapters)
            else:
                data = Quiz.query.all()
                return render_template('user_dash.html', username=username, data=data)
        else:
            return render_template('exists.html', message = 'Invalid username or password', redirect = '/')
    return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        fullname = request.form['fullname']
        gender = request.form['gender']
        password = request.form['password']
        this_user = user.query.filter_by(username=username).first()
        this_user1 = user.query.filter_by(email=email).first()
        if this_user or this_user1:
            return render_template('exists.html', message = 'User already exist', redirect = '/register')
        else:
            new_user = user(username=username, email=email, fullname=fullname,
                             gender = gender, password = generate_password_hash(password), 
                             type = 'user')
            db.session.add(new_user)
            db.session.commit()
            return redirect('/')      
    return render_template('registration.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out successfully.', 'success')
    return redirect('/')


# ADMIN ROUTES START NOW


@app.route('/admin_dash')
def admindash():
    username = session['username']
    if 'username' not in session:
        return redirect('/')  
    subjects = Subject.query.order_by(Subject.id).all()
    chapters = Chapter.query.all()
    return render_template('admin_dash.html', username=username, subjects=subjects, chapters=chapters)


@app.route('/add/subject', methods=['GET', 'POST'])
def add_sub():
    if request.method == 'POST':
        name = request.form['sub_name']
        description = request.form['desc']
        sub = Subject.query.filter_by(name=name).first()
        if sub:
            return render_template('exists.html', message = 'subject already exist', redirect = '/admin_dash')
        else:
            new_sub = Subject(name=name, description=description)
            db.session.add(new_sub)
            db.session.commit()
            return redirect('/admin_dash')
    return render_template('add_subject.html')


@app.route('/add/chapter/<int:subject_id>', methods=['GET', 'POST'])
def add_chapter(subject_id):
    subject = Subject.query.get(subject_id)
    if request.method == 'POST':
        name = request.form['chap_name']
        description = request.form['desc']
        chap = Chapter.query.filter_by(name=name, subject_id=subject_id).first()
        if chap:
            return render_template('exists.html', message='Chapter already exists', redirect='/admin_dash')
        new_chap = Chapter(name=name, description=description, subject_id=subject_id)
        db.session.add(new_chap)
        db.session.commit()
        return redirect('/admin_dash')
    return render_template('add_chapter.html', subject=subject)


@app.route('/quiz')
def quiz_dash():
    username = session['username']
    quizzes = Quiz.query.order_by(Quiz.id).all() 
    question_dict = {quiz.id: [] for quiz in quizzes}
    questions = Question.query.all()
    for question in questions:
        if question.quiz_id in question_dict:
            question_dict[question.quiz_id].append(question)
    return render_template('admin_quiz.html', username=username, quizzes=quizzes, questions=questions)


@app.route('/add/quiz', methods=['GET', 'POST'])
def addquiz():
    if request.method == 'POST':
        chapter_id = request.form['chapter_id']
        date_of_quiz = datetime.strptime(request.form['date_of_quiz'], '%Y-%m-%dT%H:%M')
        time_duration = int(request.form['time_duration'])
        remarks = request.form['remarks']
        new_quiz = Quiz(chapter_id=chapter_id, date_of_quiz=date_of_quiz, time_duration=time_duration,remarks=remarks)
        db.session.add(new_quiz)
        db.session.commit()
        return redirect('/quiz')
    chapters = Chapter.query.all()
    return render_template('add_quiz.html', chapters=chapters)


@app.route('/add/question/<int:quiz_id>', methods=['GET', 'POST'])
def add_question(quiz_id):
    quiz = Quiz.query.get(quiz_id)
    if request.method == 'POST':
        question_text = request.form['question_text']
        option_1 = request.form['option_1']
        option_2 = request.form['option_2']
        option_3 = request.form['option_3']
        option_4 = request.form['option_4']
        correct_option = request.form['correct_option']
        marks = request.form['marks']
        ques = Question.query.filter_by(question_text=question_text).first()
        if ques:
            return render_template('exists.html', message='question already present', redirect = '/quiz')
        new_question = Question(quiz_id=quiz_id,question_text=question_text, option_1=option_1, option_2=option_2, option_3=option_3, option_4=option_4,correct_option=correct_option,marks=marks)
        db.session.add(new_question)
        db.session.commit()
        return redirect('/quiz')
    return render_template('add_question.html', quiz=quiz)


@app.route('/delete/chapter/<int:chapter_id>', methods=['GET','POST'])
def delete_chapter(chapter_id):
    chapter = Chapter.query.filter_by(id=chapter_id).first()
    quizzes = Quiz.query.filter_by(chapter_id=chapter.id).all()
    for quiz in quizzes:
        Question.query.filter_by(quiz_id=quiz.id).delete()
    Quiz.query.filter_by(chapter_id=chapter.id).delete()
    db.session.delete(chapter)
    db.session.commit()
    return redirect('/admin_dash')

@app.route('/edit/chapter/<int:chapter_id>', methods=['GET','POST'])
def editchapter(chapter_id):
    chapter = Chapter.query.filter_by(id=chapter_id).first()
    if request.method == 'POST':
        chapter.name = request.form['chap_name']
        chapter.description = request.form['desc']
        db.session.commit()
        return redirect('/admin_dash')
    return render_template('edit_chapter.html', chapter=chapter)


@app.route('/delete/question/<int:question_id>', methods=['GET','POST'])
def delete_question(question_id):
    question = Question.query.filter_by(id=question_id).first()
    if question:
        db.session.delete(question)
        db.session.commit()
    return redirect('/quiz')

@app.route('/edit/question/<int:question_id>', methods=['GET','POST'])
def editquestion(question_id):
    question = Question.query.filter_by(id=question_id).first()
    quiz = Quiz.query.filter_by(id = question.quiz_id).first()
    if request.method == 'POST':
        question.question_text = request.form['question_text']
        question.option_1 = request.form['option_1']
        question.option_2 = request.form['option_2']
        question.option_3 = request.form['option_3']
        question.option_4 = request.form['option_4']
        question.correct_option = request.form['correct_option']
        question.marks = request.form['marks']
        db.session.commit()
        return redirect('/quiz')
    return render_template('edit_question.html', question=question, quiz=quiz)


@app.route('/adm_summary')
def adminsummary():
    username = session['username']
    subjects = Subject.query.all()
    subject_scores = {}
    subject_attempts = {}

    total_attempts = 0
    for subject in subjects:
        quizzes = Quiz.query.join(Chapter).filter(Chapter.subject_id == subject.id).all()
        all_scores = []
        attempts_count = 0
        for quiz in quizzes:
            quiz_scores = Score.query.filter_by(quiz_id=quiz.id).all()
            attempts_count += len(quiz_scores)
            all_scores.extend([score.score for score in quiz_scores])
        subject_scores[subject.name] = max(all_scores) if all_scores else 0
        subject_attempts[subject.name] = attempts_count
        total_attempts += attempts_count

    # If no attempts by any user
    if total_attempts == 0:
        return render_template('admin_summary.html', username=username, bar_chart=None, pie_chart=None, message="No user has attempted any quiz yet.")

    # Generate bar chart
    plt.figure(figsize=(8, 4))
    plt.bar(subject_scores.keys(), subject_scores.values(), color='orange')
    plt.title('Subject wise top scores')
    plt.xlabel('Subjects')
    plt.ylabel('Top Score')
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig('static/admin_bar.png')
    plt.close()

    # Generate pie chart
    attempts_values = list(subject_attempts.values())
    attempts_labels = list(subject_attempts.keys())
    colors = plt.cm.tab20.colors

    plt.figure(figsize=(3, 3))
    plt.pie(attempts_values, labels=attempts_labels, autopct='%1.1f%%', startangle=90,
            wedgeprops=dict(width=0.4), colors=colors[:len(attempts_labels)])
    plt.title('Subjects wise quiz attempts')
    plt.tight_layout()
    plt.savefig('static/admin_pie.png')
    plt.close()

    return render_template('admin_summary.html', username=username, bar_chart='static/admin_bar.png', pie_chart='static/admin_pie.png', message=None)


@app.route('/search')
def search():
    username = session.get('username')
    query = request.args.get('query', '').lower()
    if not query:
        return redirect('/admin_dash')

    subjects = Subject.query.filter(Subject.name.ilike(f"%{query}%")).all()
    # Initialize lists
    chapters = []
    quizzes = []
    users = []

    # If subject found, get related chapters and quizzes
    if subjects:
        subject_ids = [subject.id for subject in subjects]
        chapters = Chapter.query.filter(Chapter.subject_id.in_(subject_ids)).all()
        
        # Now get quizzes from those chapters
        chapter_ids = [chapter.id for chapter in chapters]
        if chapter_ids:
            quizzes = Quiz.query.filter(Quiz.chapter_id.in_(chapter_ids)).all()
    else:
        # If no subject found, search chapters by name
        chapters = Chapter.query.filter(Chapter.name.ilike(f"%{query}%")).all()
        if chapters:
            chapter_ids = [chapter.id for chapter in chapters]
            quizzes = Quiz.query.filter(Quiz.chapter_id.in_(chapter_ids)).all()
        else:
            # If neither subjects nor chapters match, search quizzes by chapter name or quiz id
            quizzes = Quiz.query.join(Chapter).filter(
                 (Chapter.name.ilike(f"%{query}%")) | (Quiz.id.cast(db.String).ilike(f"%{query}%"))
            ).all()

    if query == "user":
        users = user.query.all()

    return render_template('result.html', username=username, subjects=subjects, chapters=chapters, quizzes=quizzes, 
                            search_query=query, users=users
                            )


# USER ROUTES START NOW


@app.route('/user_dash')
def userdash():
    username = session['username']
    data = Quiz.query.all()
    return render_template('user_dash.html', data=data, username=username)


@app.route('/quiz/view/<int:quiz_id>')
def viewquiz(quiz_id):
    quiz = Quiz.query.filter_by(id=quiz_id).first()
    return render_template('view_quiz.html', quiz=quiz)


from datetime import datetime, timedelta

@app.route('/quiz/start/<int:quiz_id>', methods=['GET', 'POST'])
def startquiz(quiz_id):
    quiz = Quiz.query.filter_by(id=quiz_id).first_or_404()
    username = session.get('username')
    existing_score = Score.query.filter_by(quiz_id=quiz_id, username=username).first()
    if existing_score:
        return render_template('exists.html', message='You have already attempted this quiz', redirect='/user_dash')

    # Start time handling
    if not session.get(f'quiz_start_time_{quiz_id}'):
        session[f'quiz_start_time_{quiz_id}'] = datetime.now().isoformat()
    start_time = datetime.fromisoformat(session[f'quiz_start_time_{quiz_id}'])
    elapsed_time = (datetime.now() - start_time).total_seconds()
    time_left = quiz.time_duration * 60 - elapsed_time

    if time_left <= 0:
        # Time is up! Submit the quiz automatically
        user_responses = UserResponse.query.filter_by(quiz_id=quiz_id, username=username).all()
        question_map = {q.id: q for q in Question.query.filter_by(quiz_id=quiz.id).all()}
        total_score = sum(
            question_map[response.question_id].marks
            for response in user_responses
            if str(response.selected_option) == str(question_map[response.question_id].correct_option)
        )
        total_questions = len(question_map)
        attempted_questions = len(user_responses)
        new_score = Score(quiz_id=quiz_id, username=username, score=total_score,
                          total_questions=total_questions, attempted_questions=attempted_questions)
        db.session.add(new_score)
        db.session.commit()
        session.pop(f'quiz_start_time_{quiz_id}', None)
        return redirect('/user_dash')

    questions = Question.query.filter_by(quiz_id=quiz.id).all()

    saved_responses = {resp.question_id: str(resp.selected_option)
                       for resp in UserResponse.query.filter_by(quiz_id=quiz_id, username=username).all()}

    current_question_index = int(request.args.get('question_index', 0))
    current_question = questions[current_question_index] if questions else None

    if request.method == 'POST':
        question_id = request.form.get('question_id')
        selected_option = request.form.get('selected_option')

        if question_id and selected_option:
            response = UserResponse.query.filter_by(
                quiz_id=quiz_id, username=username, question_id=question_id
            ).first()
            if response:
                response.selected_option = selected_option
            else:
                new_response = UserResponse(quiz_id=quiz_id, username=username,
                                            question_id=question_id, selected_option=selected_option)
                db.session.add(new_response)
            db.session.commit()

        if 'save_next' in request.form:
            next_index = current_question_index + 1
            if next_index < len(questions):
                return redirect(url_for('startquiz', quiz_id=quiz_id, question_index=next_index))
            else:
                return redirect(url_for('startquiz', quiz_id=quiz_id, question_index=len(questions)-1))

        if 'previous' in request.form:
            return redirect(url_for('startquiz', quiz_id=quiz_id, question_index=current_question_index - 1))

        if 'submit_quiz' in request.form:
            # same scoring logic here
            user_responses = UserResponse.query.filter_by(quiz_id=quiz_id, username=username).all()
            question_map = {q.id: q for q in questions}
            total_score = sum(
                question_map[response.question_id].marks
                for response in user_responses
                if str(response.selected_option) == str(question_map[response.question_id].correct_option)
            )
            total_questions = len(questions)
            attempted_questions = len(user_responses)
            new_score = Score(quiz_id=quiz_id, username=username, score=total_score,
                              total_questions=total_questions, attempted_questions=attempted_questions)
            db.session.add(new_score)
            db.session.commit()
            session.pop(f'quiz_start_time_{quiz_id}', None)
            return redirect('/user_dash')

    minutes_left = int(time_left // 60)
    seconds_left = int(time_left % 60)

    return render_template('start_quiz.html', quiz=quiz, questions=questions, saved_responses=saved_responses,
                           current_question=current_question, current_question_index=current_question_index,
                           id=quiz.id, minutes_left=minutes_left, seconds_left=seconds_left)


@app.route('/quiz/exit/<int:quiz_id>')
def exit_quiz(quiz_id):
    username = session.get('username')
    UserResponse.query.filter_by(quiz_id=quiz_id, username=username).delete()
    db.session.commit()
    return redirect('/user_dash')


@app.route('/score', methods=['GET'])
def score():
    username = session['username']
    data = Score.query.all()
    return render_template('quiz_score.html', data=data, username=username)


@app.route('/summary', methods=['GET'])
def usersummary():
    username = session['username']
    user_scores = Score.query.filter_by(username=username).all()

    # If no scores found, show message
    if not user_scores:
        return render_template('user_summary.html', username=username, image=None, message="Currently, you have not attempted any quiz.")

    subject_attempts = {}
    for score in user_scores:
        quiz = Quiz.query.get(score.quiz_id)
        if quiz:
            chapter = Chapter.query.get(quiz.chapter_id)
            if chapter:
                subject = Subject.query.get(chapter.subject_id)
                if subject:
                    subject_attempts[subject.name] = subject_attempts.get(subject.name, 0) + 1

    # Generate Bar Chart if attempts found
    if subject_attempts:
        subjects = list(subject_attempts.keys())
        attempts = list(subject_attempts.values())
        plt.figure(figsize=(8, 5))
        plt.bar(subjects, attempts, color='skyblue', width=0.4)
        plt.xlabel("Subjects")
        plt.ylabel("Quizzes Attempted")
        plt.title(f"{username}'s Quiz Summary")
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.savefig('static/bar.png')
        plt.clf()

        return render_template('user_summary.html', username=username, image='static/bar.png', message=None)
    else:
        return render_template('user_summary.html', username=username, image=None, message="Currently, you have not attempted any quiz.")


@app.route('/user_search')
def user_search():
    search_query = request.args.get('query', '').strip()
    username = session.get('username')
    chapters = Chapter.query.filter(Chapter.name.ilike(f"%{search_query}%")).all()

    quizzes = Quiz.query.join(Chapter).filter(
        Chapter.name.ilike(f"%{search_query}%") | 
        Quiz.id.ilike(f"%{search_query}%")
    ).all()

    quiz_ids = [quiz.id for quiz in quizzes]
    scores = Score.query.filter(
        Score.username == username,
        (Score.quiz_id.in_(quiz_ids)) |
        (Score.quiz_id.ilike(f"%{search_query}%")) |
        (Score.score.ilike(f"%{search_query}%"))
    ).all()

    return render_template( 'user_result.html', search_query=search_query, chapters=chapters,  quizzes=quizzes, 
        scores=scores, username=username
    )


# APIs START NOW
# APIs for only deleting a subject and updating a quiz because these are the only operations that are not possible
# at the frontend.

class DeleteSubject(Resource):
    def delete(self, subject_id):
        subject = Subject.query.get(subject_id)
        if not subject:
            return {'message': 'Subject not found'}, 404

        # Delete related chapters and quizzes before deleting subject
        for chapter in subject.chapters:
            for quiz in chapter.quizzes:
                for question in quiz.questions:
                    db.session.delete(question)
                for score in quiz.scores:
                    db.session.delete(score)
                db.session.delete(quiz)
            db.session.delete(chapter)

        db.session.delete(subject)
        db.session.commit()
        return {'message': 'Subject and related data deleted successfully'}, 200


class UpdateQuiz(Resource):
    def put(self, quiz_id):
        quiz = Quiz.query.get(quiz_id)
        if not quiz:
            return {'message': 'Quiz not found'}, 404

        data = request.get_json()
        if 'date_of_quiz' in data:
            try:
                quiz.date_of_quiz = datetime.strptime(data['date_of_quiz'], "%Y-%m-%d %H:%M")
            except ValueError:
                return {'message': 'Invalid date format. Use YYYY-MM-DD HH:MM'}, 400
        if 'time_duration' in data:
            quiz.time_duration = data['time_duration']
        if 'remarks' in data:
            quiz.remarks = data['remarks']

        db.session.commit()
        return {'message': 'Quiz updated successfully'}, 200

class DeleteUser(Resource):
    def delete(self, username):
        user_to_delete = user.query.filter_by(username=username).first()
        if not user_to_delete:
            return {'message': 'User not found'}, 404

        UserResponse.query.filter_by(username=username).delete()
        Score.query.filter_by(username=username).delete()
        db.session.delete(user_to_delete)
        db.session.commit()
        return {'message': f'User {username} and related data deleted successfully'}, 200


api.add_resource(DeleteSubject, '/subject/<int:subject_id>')
api.add_resource(UpdateQuiz, '/quiz/<int:quiz_id>')
api.add_resource(DeleteUser, '/delete_user/<string:username>')
