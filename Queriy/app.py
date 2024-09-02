from flask import Flask, request,render_template, redirect,session
from flask_sqlalchemy import SQLAlchemy
import bcrypt
import google.generativeai as genai

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
db = SQLAlchemy(app)
app.secret_key = 'secret_key'

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))

    def __init__(self,email,password,name):
        self.name = name
        self.email = email
        self.password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    def check_password(self,password):
        return bcrypt.checkpw(password.encode('utf-8'),self.password.encode('utf-8'))

with app.app_context():
    db.create_all()


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register',methods=['GET','POST'])
def register():
    if request.method == 'POST':
        # handle request
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']

        new_user = User(name=name,email=email,password=password)
        db.session.add(new_user)
        db.session.commit()
        return redirect('/login')



    return render_template('register.html')

@app.route('/login',methods=['GET','POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        user = User.query.filter_by(email=email).first()
        
        if user and user.check_password(password):
            session['email'] = user.email
            return redirect('/dashboard')
        else:
            return render_template('login.html',error='Invalid user')

    return render_template('login.html')


@app.route('/dashboard')
def dashboard():
    if session['email']:
        return render_template('dashboard.html')
    
    return redirect('/login')

@app.route('/logout')
def logout():
    session.pop('email',None)
    return redirect('/login')

GOOGLE_API_KEY = "AIzaSyD61JmJfQBvy2qEOhQCwyIasE9j2qDnM9g"
genai.configure(api_key=GOOGLE_API_KEY)
model = genai.GenerativeModel('gemini-pro')

@app.route('/generate_sql_query', methods=['POST'])
def generate_sql_query():
    text_input = request.form['text_input']
    template = f"""
        Creating SQL Query using the below text:
        ```
        {text_input}
        ```
        SQL Query.
    """
    response = model.generate_content(template)
    sql_query = response.text.strip().lstrip("```sql").rstrip("```")
    expected_output = f"""
        expected response of this SQL query snippet:
        ```
        {sql_query}
        ```
        Provide sample tabular Response with no explanation:
    """
    eoutput = model.generate_content(expected_output)
    explanation = f"""
        Explain this SQL Query
        ```
        {sql_query}
        ```
        Please provide with simplest of explanation:
    """
    explanation = model.generate_content(explanation)
    return {'sql_query': sql_query, 'expected_output': eoutput.text, 'explanation': explanation.text}


if __name__ == '__main__':
    app.run(debug=True)
