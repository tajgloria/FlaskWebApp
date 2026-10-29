from flask import Blueprint, render_template, request, jsonify, current_app, flash
from openai import OpenAI
from dotenv import load_dotenv
import os
from flask_login import login_required, current_user
from .models import Note
from . import db
import json

load_dotenv()

views = Blueprint('views', __name__)

api_key = os.getenv("OPENAI_API_KEY")
ai_client = OpenAI(api_key=api_key) if api_key else None

@views.route('/', methods=['GET', 'POST'])
@login_required
def home():
    if request.method == 'POST':
        note = request.form.get("note")

        if len(note) < 1:
            flash('Please enter a note.', category='error')
        else:
            new_note=Note(data=note, user_id=current_user.id)
            db.session.add(new_note)
            db.session.commit()
            flash('Note Added!', category='success')

    return render_template("home.html", user=current_user)

@views.route('/delete-note', methods=['POST'])
@login_required
def delete_note():
    note = json.loads(request.data)
    noteID = note['noteId']
    note = Note.query.get(noteID)
    if note:
        if note.user_id == current_user.id:
            db.session.delete(note)
            db.session.commit()
            return jsonify({})

@views.route('/chat', methods=['POST'])
def chat():
    if ai_client is None:
        return jsonify({
            "reply": "The AI assistant is not configured. Please check the API key."
        }), 500

    data = request.get_json(silent=True) or {}
    message = data.get("message", "").strip()

    if not message:
        return jsonify({"reply": "Please enter a message."}), 400

    if len(message) > 4000:
        return jsonify({"reply": "Please shorten your message."}), 400

    try:
        response = ai_client.responses.create(
            model="gpt-5.5",
            instructions=(
                "You are Juanbot a Nonprofit assistant "
                "Help visitors with volunteering, community events, "
                "and getting involved in their community. "
                "Be friendly and helpful. Never invent details "
                "about specific events or organizations."
            ),
            input=message
        )

        return jsonify({"reply": response.output_text})

    except Exception:
        current_app.logger.exception("AI chatbot error")
        return jsonify({
            "reply": "Sorry, the AI assistant is temporarily unavailable."
        }), 502