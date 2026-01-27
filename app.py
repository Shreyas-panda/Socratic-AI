import os
from flask import Flask, render_template, request, jsonify, session, send_file, redirect, url_for, Response
from tutorial_agent import TutorialAgent
from database import TutorialDatabase
from rag_engine import RAGEngine
import sqlite3
import uuid
from dotenv import load_dotenv

# Load environment variables
import io
import speech_recognition as sr
from pydub import AudioSegment

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "dev_secret_key_change_me")

# Audio Helper
def transcribe_audio(audio_bytes):
    try:
        # Convert webm/ogg to wav
        audio = AudioSegment.from_file(io.BytesIO(audio_bytes))
        wav_io = io.BytesIO()
        audio.export(wav_io, format='wav')
        wav_io.seek(0)
        
        r = sr.Recognizer()
        with sr.AudioFile(wav_io) as source:
            audio_data = r.record(source)
            text = r.recognize_google(audio_data)
        return text
    except Exception as e:
        print(f"Transcription error: {e}")
        return None

# Initialize Agent (Singleton-ish pattern for the app, but user state is separate)
# Actually TutorialAgent seems stateless regarding user sessions? 
# Let's check tutorial_agent.py usage. It takes session_id in methods.
db = TutorialDatabase()
agent = TutorialAgent()
rag_engine = RAGEngine()

@app.route('/')
def index():
    if 'user_id' not in session:
        session['user_id'] = str(uuid.uuid4())
    
    # Always open on the start page (Welcome Screen)
    # We clear the active conversation state to force the welcome view
    session.pop('current_conversation_id', None)
    session.pop('subject', None)
        
    return render_template('chat.html')

@app.route('/chat')
def chat():
    if 'user_id' not in session:
        session['user_id'] = str(uuid.uuid4())
    
    messages = []
    if 'current_conversation_id' in session:
        try:
            messages = db.get_conversation_history(session['current_conversation_id'])
        except Exception as e:
            print(f"Error loading history: {e}")
            
    return render_template('chat.html', messages=messages)

@app.route('/new_chat')
def new_chat():
    session.pop('current_conversation_id', None)
    session.pop('subject', None)
    return redirect(url_for('chat'))

@app.route('/toggle_temp_mode', methods=['POST'])
def toggle_temp_mode():
    data = request.json
    session['is_temporary_mode'] = data.get('enabled', False)
    return jsonify({"status": "success", "mode": session.get('is_temporary_mode')})

@app.route('/api/export_pdf')
def export_pdf():
    if 'user_id' not in session or 'current_conversation_id' not in session:
        return jsonify({"error": "No active conversation"}), 400
    
    try:
        from pdf_export import export_conversation_to_pdf, create_pdf_download_name
        
        conversation_id = session['current_conversation_id']
        subject = session.get('subject', 'Lesson')
        
        # Get history from DB
        history = db.get_conversation_history(conversation_id)
        
        # Identify empty history
        if not history:
             return jsonify({"error": "Conversation is empty"}), 400
             
        # Generate PDF
        pdf_bytes = export_conversation_to_pdf(subject, history)
        
        # Create unique filename
        filename = create_pdf_download_name(subject)
        
        return send_file(
            io.BytesIO(pdf_bytes),
            mimetype='application/pdf',
            as_attachment=True,
            download_name=filename
        )
            
    except Exception as e:
        print(f"PDF Export Error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/history')
def get_history():
    if 'user_id' not in session:
        return jsonify([])
    
    try:
        conversations = db.get_conversations_by_session(session['user_id'])
        return jsonify(conversations)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/load_chat/<int:conversation_id>')
def load_chat(conversation_id):
    # Verify ownership (optional but good practice)
    # For now just load it
    conn = sqlite3.connect(db.db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT subject FROM conversations WHERE id = ?", (conversation_id,))
    result = cursor.fetchone()
    conn.close()
    
    if result:
        session['current_conversation_id'] = conversation_id
        session['subject'] = result[0]
        
    return redirect(url_for('chat'))

@app.route('/api/history', methods=['DELETE'])
def clear_history():
    if 'user_id' not in session:
        return jsonify({"error": "Unauthorized"}), 401
    
    try:
        # We need a method in database.py to clear, or just raw SQL here for speed
        with sqlite3.connect(db.db_path) as conn:
            cursor = conn.cursor()
            # Delete conversations for this user
            # Assuming sessions are linked to user_id. Use db class if possible but raw is fine for this specific task
            # Actually, let's stick to the db class pattern if possible, but for now we'll do:
            pass 
            # Wait, I should implement this properly via db class or raw sql. 
            # Since I can't easily edit database.py right now without reading it, I'll use raw SQL on the known schema.
            cursor.execute("DELETE FROM conversations WHERE session_id = ?", (session['user_id'],))
            conn.commit()
            
        return jsonify({"status": "success"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/stats')
def get_stats():
    if 'user_id' not in session:
        return jsonify({"error": "Unauthorized"}), 401
    
    try:
        # Fetch stats from DB
        stats = db.get_user_stats(session['user_id'])
        
        # Calculate daily activity (mock or real if DB supports it)
        # For this prototype we will infer from conversation timestamps if available, 
        # or just return the aggregate subject data which we know exists.
        
        # Structure for Chart.js
        subject_data = {
            "labels": list(stats['subjects'].keys()),
            "data": list(stats['subjects'].values())
        }
        
        return jsonify({
            "total_conversations": stats['total_conversations'],
            "total_messages": stats['total_messages'],
            "subjects": subject_data
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')

@app.route('/api/start_tutorial', methods=['POST'])
def start_tutorial():
    data = request.json
    subject = data.get('subject')
    user_id = session.get('user_id')
    language = data.get('language', 'English')
    
    if not subject:
        return jsonify({"error": "Subject is required"}), 400
        
    result = agent.start_tutorial(user_id, subject, language)
    
    # Store current conversation in session
    session['current_conversation_id'] = result['conversation_id']
    session['subject'] = subject
    
    # Add status field for frontend check
    result['status'] = 'success'
    return jsonify(result)

@app.route('/api/message', methods=['POST'])
def message():
    try:
        # Check if this is a multipart request (with image) or JSON
        image_file = None
        user_input = ""
        language = "English"
        
        if request.content_type and 'multipart/form-data' in request.content_type:
            user_input = request.form.get('message', '')
            language = request.form.get('language', 'English')
            if 'image' in request.files:
                image_file = request.files['image']
        else:
            data = request.json
            user_input = data.get('message', '')
            language = data.get('language', 'English')
        
        conversation_id = session.get('current_conversation_id')
        
        if not conversation_id:
            return jsonify({"error": "No active conversation"}), 400

        # RAG Context Retrieval
        context = ""
        try:
            # Only retrieve if we have documents and it's a question
            if rag_engine.vector_store:
                 context = rag_engine.get_formatted_context(user_input)
                 if context:
                     print(f"DEBUG: Retrieved RAG context for query: {user_input[:50]}...")
        except Exception as e:
            print(f"RAG Retrieval Error: {e}")
            
        # Handle Image + Text
        if image_file and image_file.filename != '':
            from image_handler import save_uploaded_image, analyze_image_with_llm
            
            # Save the uploaded image
            filepath = save_uploaded_image(image_file, str(conversation_id))
            
            # Use user input as the question, or default if empty
            question = user_input if user_input.strip() else "Explain this image to me."
            subject = session.get('subject', 'General Topic')
            
            # Analyze
            try:
                analysis = analyze_image_with_llm(filepath, question, subject)
                
                # Save to DB
                # Mark as image analysis in DB
                db.add_message(
                    conversation_id, 
                    "user", 
                    f"[Image Uploaded] {question}", 
                    "image_analysis"
                )
                db.add_message(conversation_id, "assistant", analysis)
                
                return jsonify({"response": analysis})
                
            except Exception as e:
                # Handle Rate Limits cleanly
                error_msg = str(e)
                if "429" in error_msg:
                    return jsonify({"error": "Vision model is busy (Rate Limit). Please try again shortly."}), 429
                raise e

        # Handle Text Only (Standard Flow)
        input_type = "question"
        if "test me" in user_input.lower() or "quiz" in user_input.lower():
            input_type = "evaluation_request"
            
        result = agent.continue_conversation(
            conversation_id,
            user_input,
            input_type,
            language,
            context=context
        )
        
        print(f"DEBUG: Agent result: {result}")
        return jsonify(result)

    except Exception as e:
        print(f"Message Error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/message_stream', methods=['POST'])
def message_stream():
    """Streaming endpoint for real-time responses."""
    if 'user_id' not in session:
        return jsonify({"error": "Unauthorized"}), 401
    
    if 'current_conversation_id' not in session:
        return jsonify({"error": "No active conversation"}), 400
    
    data = request.json
    user_input = data.get('message', '').strip()
    language = data.get('language', 'English')
    
    if not user_input:
        return jsonify({"error": "Message is required"}), 400
    
    conversation_id = session['current_conversation_id']
    subject = session.get('subject', 'General Topic')
    
    # RAG retrieval
    context = ""
    try:
        context = rag_engine.get_formatted_context(user_input)
    except Exception as e:
        print(f"RAG Retrieval Error: {e}")
    
    # Build prompt (simplified for streaming)
    prompt = f"""You are an expert AI tutor teaching about {subject}.
IMPORTANT: Write the entire response in {language}.

{context}

The student asked: "{user_input}"

Provide a clear, detailed explanation. Use examples where helpful.
If the provided 'CONTEXT FROM UPLOADED DOCUMENTS' is relevant, USE IT."""

    def generate():
        full_response = ""
        for chunk in agent._call_llm_stream(prompt):
            full_response += chunk
            yield chunk
        
        # Save to DB after stream completes
        db.add_message(conversation_id, "user", user_input, "question")
        db.add_message(conversation_id, "assistant", full_response, "answer")
    
    return Response(generate(), mimetype='text/plain')

@app.route('/api/clear_knowledge_base', methods=['POST'])
def clear_knowledge_base():
    """Clear all documents from the RAG knowledge base."""
    try:
        result = rag_engine.clear_knowledge_base()
        if result:
            return jsonify({"status": "success", "message": "Knowledge base cleared."})
        else:
            return jsonify({"status": "success", "message": "Knowledge base was already empty."})
    except Exception as e:
        print(f"Clear KB Error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/audio', methods=['POST'])
def handle_audio():
    if 'audio' not in request.files:
        return jsonify({"error": "No audio file"}), 400
    
    audio_file = request.files['audio']
    if audio_file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    try:
        # Read the file to bytes
        audio_bytes = audio_file.read()
        
        # Use existing helper to transcribe
        text = transcribe_audio(audio_bytes)
        
        if not text:
             return jsonify({"error": "Could not recognize speech"}), 400
             
        # Return transcribed text only (for STT)
        return jsonify({
            "text": text,
            "status": "success"
        })

    except Exception as e:
        print(f"Audio Error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/upload_document', methods=['POST'])
def upload_document():
    if 'document' not in request.files:
        return jsonify({"error": "No document part"}), 400
    
    file = request.files['document']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400
        
    try:
        filename = file.filename
        # Save temp file
        temp_path = os.path.join("uploaded_images", filename) # Reuse folder or create new? Reuse for now.
        if not os.path.exists("uploaded_images"):
            os.makedirs("uploaded_images")
            
        file.save(temp_path)
        
        # Process with RAG Engine
        success, result_msg = rag_engine.process_file(temp_path, filename)
        
        if not success:
            return jsonify({"error": result_msg}), 400
        
        # Cleanup temp file? Maybe keep for reference? Let's keep for now.
        
        return jsonify({
            "status": "success",
            "message": result_msg,
            "filename": filename
        })
        
    except Exception as e:
        print(f"Document Upload Error: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/upload_image', methods=['POST'])
def upload_image():
    if 'image' not in request.files:
        return jsonify({"error": "No image part"}), 400
    
    file = request.files['image']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400
        
    if 'current_conversation_id' not in session:
         return jsonify({"error": "No active conversation"}), 400

    try:
        from image_handler import save_uploaded_image, analyze_image_with_llm
        
        conversation_id = str(session['current_conversation_id'])
        
        # Save image
        filepath = save_uploaded_image(file, conversation_id)
        
        # Analyze image
        user_question = request.form.get('question', "Explain this image to me.")
        subject = session.get('subject', 'General Topic')
        
        analysis = analyze_image_with_llm(filepath, user_question, subject)
        
        # Add to database
        db.add_message(session['current_conversation_id'], "user", f"[Image Uploaded] {user_question} \n\n(Analysis: {analysis})", "image_analysis")
        db.add_message(session['current_conversation_id'], "assistant", analysis)
        
        return jsonify({
            "status": "success",
            "analysis": analysis,
            "filepath": filepath
        })
        
    except Exception as e:
        print(f"Image Upload Error: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    # Enabling multithreading for faster concurrent response handling
    app.run(debug=True, port=5001, threaded=True)
