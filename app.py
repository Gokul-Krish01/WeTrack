from flask import Flask, render_template, request, redirect, url_for, session, send_file
import os
import csv
from datetime import datetime, timedelta
import google.generativeai as genai
import random
from dotenv import load_dotenv
import gspread
from oauth2client.service_account import ServiceAccountCredentials

load_dotenv()

app = Flask(__name__)
app.secret_key = os.urandom(24)

# Configure Gemini AI
genai.configure(api_key=os.getenv("AIzaSyCw0eHDx4FWvaa-rtx66M-vD-FcP-8apDo"))
model = genai.GenerativeModel("gemini-1.5-pro")

# Google Sheets setup
MOTIVATIONAL_QUOTES = [
    "The best way to predict the future is to create it.",
    "Success is not final, failure is not fatal: It is the courage to continue that counts.",
    "It does not matter how slowly you go as long as you do not stop.",
    "Believe in yourself and all that you are.",
    "You are never too old to set another goal or to dream a new dream.",
    "Success is the sum of small efforts, repeated day in and day out."
]
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
client = gspread.authorize(creds)
sheet = client.open_by_key('1rjNNOT19PBga_l-tS0LqUu2_2ZkiI3N50P-1xMqdOSw').sheet1

# Motivational quotes

# Routes
@app.route('/')
def home():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = request.form['username']
        if user in ['Krish', 'Shamy']:
            session['user'] = user
            return redirect(url_for('dashboard'))
        else:
            return render_template('login.html', error="Invalid user.")
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        return redirect(url_for('login'))
    
    # Fetch data from Google Sheets
    data = sheet.get_all_records()  # or sheet.get_all_values()

    # Print the fetched data for debugging
    print(data)

    today = datetime.today().strftime("%Y-%m-%d")
    start_of_week = (datetime.today() - timedelta(days=datetime.today().weekday())).strftime("%Y-%m-%d")
    
    # Initialize the summary and totals dictionaries
    summary = {"Krish": 0.0, "Shamy": 0.0}
    totals = {"Krish": 0.0, "Shamy": 0.0}

    for row in data:
        try:
            user = row['user']  # Adjust based on actual key
            hours = float(row['hours'])  # Adjust based on actual key
            date = row['date']  # Adjust based on actual key

            # Check if the current row has the expected data
            print(f"User: {user}, Hours: {hours}, Date: {date}")
            
            # Summarize hours for today's date
            if date == today and user in summary:
                summary[user] += hours
            
            # Summarize weekly hours
            if start_of_week <= date <= today and user in totals:
                totals[user] += hours
        except KeyError as e:
            print(f"KeyError: {e} in row {row}")  # Handle any missing columns or incorrect names
    
    print(f"Summary: {summary}")
    print(f"Totals: {totals}")

    # In your Python code, update:
    return render_template('dashboard.html', summary=list(summary.items()), totals=list(totals.items()), user=session['user'])

@app.route('/log', methods=['GET', 'POST'])
def log():
    if 'user' not in session:
        return redirect(url_for('login'))
    if request.method == 'POST':
        task = request.form['task']
        hours = request.form['hours']
        try:
            hours = float(hours)
            sheet.append_row([session['user'], datetime.now().strftime("%Y-%m-%d"), task, hours])
            message = "Progress logged successfully!"
        except ValueError:
            message = "Please enter a valid number for hours."
        return render_template('log.html', message=message)
    return render_template('log.html')


@app.route('/ai', methods=['GET', 'POST'])
def ai():
    if 'user' not in session:
        return redirect(url_for('login'))  # Redirect to login if not authenticated

    suggestion = ""  # Initialize suggestion as an empty string
    random_quote = random.choice(MOTIVATIONAL_QUOTES)  # Pick a random quote from the list
    
    if request.method == 'POST':
        task = request.form['task']  # Get task from the form submission
        
        # Create a prompt for the AI model based on the task
        prompt = f"Provide productivity improvement tips for the task: '{task}'"
        
        try:
            # Generate response using the model
            response = model.generate_content(prompt)
            suggestion = response.text  # Set the suggestion text to the response
        except Exception as e:
            suggestion = f"Error fetching suggestion: {str(e)}"  # Provide error message in case of failure

    # Pass both the suggestion and random quote to the template
    return render_template('ai.html', suggestion=suggestion, quote=random_quote)

@app.route('/export')
def export():
    if 'user' not in session:
        return redirect(url_for('login'))
    data = sheet.get_all_values()
    filename = "progress_export.csv"
    with open(filename, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerows(data)
    return send_file(filename, as_attachment=True)

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
