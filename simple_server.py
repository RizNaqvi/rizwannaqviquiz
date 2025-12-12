#!/usr/bin/env python3
"""
Rizwan Naqvi Quiz Platform - Complete Railway-Ready Server
Handles: Students, Teachers, Quiz AI, Admin Panel
"""
import asyncio
import json
import os
from aiohttp import web

# ==================== GLOBAL STATE ====================
clients = {"students": set(), "teachers": set(), "quiz_ai": set()}
student_connections = {}
quiz_results = []
quiz_ai_ws = None

# Store uploaded quizzes
uploaded_quizzes = {
    "General Knowledge": {"questions": 30, "uploaded": True}
}

# ==================== COMPLETE HTML (Your Full Portal) ====================
HTML_PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Rizwan Naqvi Quiz Portal</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
            padding: 20px;
        }
        .container {
            background: white;
            border-radius: 20px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            max-width: 900px;
            width: 100%;
            padding: 40px;
            position: relative;
        }
        .header {
            text-align: center;
            margin-bottom: 30px;
        }
        .header h1 {
            color: #667eea;
            font-size: 2.5em;
            margin-bottom: 10px;
        }
        .header p {
            color: #666;
            font-size: 1.1em;
        }
        .screen { display: none; }
        .screen.active { display: block; }
        .role-selection {
            display: flex;
            gap: 20px;
            justify-content: center;
            margin-top: 40px;
        }
        .role-btn {
            flex: 1;
            padding: 40px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            border-radius: 15px;
            font-size: 1.5em;
            cursor: pointer;
            transition: transform 0.2s, box-shadow 0.2s;
        }
        .role-btn:hover {
            transform: translateY(-5px);
            box-shadow: 0 10px 30px rgba(102, 126, 234, 0.4);
        }
        .name-input {
            width: 100%;
            padding: 15px;
            font-size: 1.2em;
            border: 2px solid #667eea;
            border-radius: 10px;
            margin: 20px 0;
        }
        .quiz-list {
            display: grid;
            gap: 15px;
            margin-top: 20px;
        }
        .quiz-card {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            border-radius: 15px;
            cursor: pointer;
            transition: transform 0.2s;
            text-align: center;
        }
        .quiz-card:hover {
            transform: translateY(-3px);
        }
        .quiz-card h3 {
            font-size: 1.5em;
            margin-bottom: 10px;
        }
        .question-box {
            background: #f8f9fa;
            padding: 30px;
            border-radius: 15px;
            margin: 20px 0;
        }
        .question-text {
            font-size: 1.3em;
            color: #333;
            margin-bottom: 20px;
            font-weight: 500;
        }
        .options {
            display: grid;
            gap: 15px;
        }
        .option-btn {
            padding: 20px;
            background: white;
            border: 2px solid #667eea;
            border-radius: 10px;
            font-size: 1.1em;
            cursor: pointer;
            text-align: left;
            transition: all 0.2s;
        }
        .option-btn:hover {
            background: #667eea;
            color: white;
            transform: translateX(5px);
        }
        .result-card {
            text-align: center;
            padding: 40px;
        }
        .result-card h2 {
            color: #667eea;
            font-size: 2.5em;
            margin-bottom: 20px;
        }
        .score-display {
            font-size: 3em;
            color: #764ba2;
            font-weight: bold;
            margin: 30px 0;
        }
        .leaderboard {
            margin-top: 30px;
        }
        .leaderboard table {
            width: 100%;
            border-collapse: collapse;
        }
        .leaderboard th {
            background: #667eea;
            color: white;
            padding: 15px;
            text-align: left;
        }
        .leaderboard td {
            padding: 12px;
            border-bottom: 1px solid #ddd;
        }
        .leaderboard tr:nth-child(even) {
            background: #f8f9fa;
        }
        .btn-primary {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            padding: 15px 40px;
            font-size: 1.1em;
            border-radius: 10px;
            cursor: pointer;
            margin: 10px;
            transition: transform 0.2s;
        }
        .btn-primary:hover {
            transform: translateY(-2px);
        }
        .status {
            text-align: center;
            padding: 10px;
            border-radius: 10px;
            margin: 10px 0;
            font-weight: 500;
        }
        .status.connected {
            background: #d4edda;
            color: #155724;
        }
        .status.disconnected {
            background: #f8d7da;
            color: #721c24;
        }
        #adminPanel {
            margin-top: 30px;
            padding: 20px;
            background: #f8f9fa;
            border-radius: 15px;
        }
        .upload-section {
            margin: 20px 0;
            padding: 20px;
            background: white;
            border-radius: 10px;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎓 Rizwan Naqvi Quiz Portal</h1>
            <p>General Knowledge • Computer Networks • Database • More coming!</p>
        </div>

        <!-- Login Screen -->
        <div id="loginScreen" class="screen active">
            <h2 style="text-align: center; margin-bottom: 20px;">Welcome!</h2>
            <div class="role-selection">
                <button class="role-btn" onclick="selectRole('student')">👨‍🎓 Student</button>
                <button class="role-btn" onclick="selectRole('teacher')">👨‍🏫 Teacher</button>
            </div>
        </div>

        <!-- Student Dashboard -->
        <div id="studentDashboard" class="screen">
            <div id="connectionStatus" class="status disconnected">Connecting...</div>
            <h2 id="welcomeMsg">Hello <span id="studentName"></span>!</h2>
            <div class="quiz-list" id="quizList">
                <div class="quiz-card" onclick="startQuiz('General Knowledge')">
                    <h3>📚 General Knowledge</h3>
                    <p>30 Questions</p>
                    <button class="btn-primary">Start Quiz</button>
                </div>
            </div>
        </div>

        <!-- Quiz Screen -->
        <div id="quizScreen" class="screen">
            <div class="question-box">
                <div class="question-text" id="questionText">Loading question...</div>
                <div class="options" id="optionsContainer"></div>
            </div>
        </div>

        <!-- Result Screen -->
        <div id="resultScreen" class="screen">
            <div class="result-card">
                <h2>🎉 Congratulations!</h2>
                <div class="score-display">
                    <span id="scoreDisplay">0/0</span>
                    <div style="font-size: 0.5em; color: #666;">
                        <span id="percentDisplay">0%</span> Correct
                    </div>
                </div>
                <button class="btn-primary" onclick="backToDashboard()">Take Another Quiz</button>
            </div>
        </div>

        <!-- Teacher Dashboard -->
        <div id="teacherDashboard" class="screen">
            <h2>📊 Live Leaderboard</h2>
            <button class="btn-primary" onclick="refreshResults()">🔄 Refresh</button>
            <div class="leaderboard">
                <table>
                    <thead>
                        <tr>
                            <th>Rank</th>
                            <th>Name</th>
                            <th>Score</th>
                            <th>%</th>
                        </tr>
                    </thead>
                    <tbody id="leaderboardBody">
                        <tr><td colspan="4" style="text-align: center;">No results yet...</td></tr>
                    </tbody>
                </table>
            </div>
            
            <div id="adminPanel">
                <h3>📤 Upload New Quiz</h3>
                <div class="upload-section">
                    <input type="text" id="quizTitle" placeholder="Quiz Title (e.g., Computer Networks)" class="name-input">
                    <input type="file" id="quizFile" accept=".json" style="margin: 10px 0;">
                    <button class="btn-primary" onclick="uploadQuiz()">Upload Quiz</button>
                </div>
            </div>
        </div>
    </div>

    <script>
        let ws = null;
        let currentRole = null;
        let studentName = "";
        let currentQuiz = "";

        function showScreen(screenId) {
            document.querySelectorAll('.screen').forEach(s => s.classList.remove('active'));
            document.getElementById(screenId).classList.add('active');
        }

        function selectRole(role) {
            currentRole = role;
            const name = prompt(role === 'student' ? 'Enter your name:' : 'Enter teacher name:');
            if (!name) return;
            
            studentName = name;
            connectWebSocket();
            
            if (role === 'student') {
                document.getElementById('studentName').textContent = name;
                showScreen('studentDashboard');
            } else {
                showScreen('teacherDashboard');
            }
        }

        function connectWebSocket() {
            const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            const wsUrl = `${protocol}//${window.location.host}/ws`;
            
            ws = new WebSocket(wsUrl);
            
            ws.onopen = () => {
                console.log('Connected to server');
                ws.send(JSON.stringify({
                    type: 'register',
                    role: currentRole,
                    name: studentName
                }));
                
                if (currentRole === 'student') {
                    document.getElementById('connectionStatus').textContent = '✅ Connected';
                    document.getElementById('connectionStatus').className = 'status connected';
                }
                
                if (currentRole === 'teacher') {
                    ws.send(JSON.stringify({ type: 'show_results' }));
                }
            };
            
            ws.onmessage = (event) => {
                const data = JSON.parse(event.data);
                handleMessage(data);
            };
            
            ws.onerror = () => {
                if (currentRole === 'student') {
                    document.getElementById('connectionStatus').textContent = '❌ Connection Error';
                    document.getElementById('connectionStatus').className = 'status disconnected';
                }
            };
        }

        function handleMessage(data) {
            if (data.type === 'question') {
                displayQuestion(data);
            } else if (data.type === 'final_result') {
                displayResult(data.result);
            } else if (data.type === 'results') {
                displayLeaderboard(data.data);
            } else if (data.type === 'new_result') {
                refreshResults();
            }
        }

        function startQuiz(quizName) {
            currentQuiz = quizName;
            showScreen('quizScreen');
            ws.send(JSON.stringify({
                type: 'choose_quiz',
                quiz: quizName
            }));
        }

        function displayQuestion(data) {
            document.getElementById('questionText').textContent = 
                `Question ${data.qnum}: ${data.question}`;
            
            const container = document.getElementById('optionsContainer');
            container.innerHTML = '';
            
            data.options.forEach(opt => {
                const btn = document.createElement('button');
                btn.className = 'option-btn';
                btn.textContent = opt;
                btn.onclick = () => submitAnswer(opt);
                container.appendChild(btn);
            });
        }

        function submitAnswer(answer) {
            ws.send(JSON.stringify({
                type: 'answer',
                answer: answer
            }));
        }

        function displayResult(result) {
            showScreen('resultScreen');
            document.getElementById('scoreDisplay').textContent = 
                `${result.correct}/${result.total}`;
            document.getElementById('percentDisplay').textContent = 
                `${result.percentage.toFixed(1)}%`;
        }

        function backToDashboard() {
            showScreen('studentDashboard');
        }

        function refreshResults() {
            if (ws && ws.readyState === WebSocket.OPEN) {
                ws.send(JSON.stringify({ type: 'show_results' }));
            }
        }

        function displayLeaderboard(results) {
            const tbody = document.getElementById('leaderboardBody');
            
            if (results.length === 0) {
                tbody.innerHTML = '<tr><td colspan="4" style="text-align: center;">No results yet...</td></tr>';
                return;
            }
            
            const sorted = [...results].sort((a, b) => b.percentage - a.percentage);
            
            tbody.innerHTML = sorted.map((r, i) => `
                <tr>
                    <td>${i + 1}</td>
                    <td>${r.name}</td>
                    <td>${r.correct}/${r.total}</td>
                    <td>${r.percentage.toFixed(1)}%</td>
                </tr>
            `).join('');
        }

        function uploadQuiz() {
            const title = document.getElementById('quizTitle').value;
            const file = document.getElementById('quizFile').files[0];
            
            if (!title || !file) {
                alert('Please provide quiz title and file');
                return;
            }
            
            const reader = new FileReader();
            reader.onload = (e) => {
                try {
                    const questions = JSON.parse(e.target.result);
                    ws.send(JSON.stringify({
                        type: 'upload_quiz',
                        title: title,
                        questions: questions
                    }));
                    alert('Quiz uploaded successfully!');
                } catch (err) {
                    alert('Invalid JSON file');
                }
            };
            reader.readAsText(file);
        }
    </script>
</body>
</html>"""

# ==================== ROUTE HANDLERS ====================

async def serve_home(request):
    """Serve the main HTML page"""
    return web.Response(text=HTML_PAGE, content_type='text/html')

async def serve_student(request):
    """Serve student.html"""
    with open('student.html', 'r', encoding='utf-8') as f:
        html_content = f.read()
    return web.Response(text=html_content, content_type='text/html')

async def serve_teacher(request):
    """Serve teacher.html"""
    with open('teacher.html', 'r', encoding='utf-8') as f:
        html_content = f.read()
    return web.Response(text=html_content, content_type='text/html')

async def websocket_handler(request):
    """Handle WebSocket connections for students, teachers, and quiz AI"""
    ws = web.WebSocketResponse()
    await ws.prepare(request)
    
    role = None
    name = None
    
    try:
        async for msg in ws:
            if msg.type == web.WSMsgType.TEXT:
                data = json.loads(msg.data)
                msg_type = data.get("type")
                
                # Registration
                if msg_type == "register":
                    role = data.get("role")
                    name = data.get("name", "Anonymous")
                    
                    if role == "student":
                        clients["students"].add(ws)
                        student_connections[name] = ws
                    elif role == "teacher":
                        clients["teachers"].add(ws)
                    elif role == "quiz_ai":
                        global quiz_ai_ws
                        quiz_ai_ws = ws
                        clients["quiz_ai"].add(ws)
                
                # Student chooses quiz
                elif msg_type == "choose_quiz" and role == "student" and quiz_ai_ws:
                    await quiz_ai_ws.send_json({
                        "type": "start_quiz",
                        "name": name,
                        "quiz": data["quiz"]
                    })
                
                # Student submits answer
                elif msg_type == "answer" and role == "student" and quiz_ai_ws:
                    await quiz_ai_ws.send_json({
                        "type": "student_answer",
                        "name": name,
                        "answer": data["answer"]
                    })
                
                # Quiz AI sends question to student
                elif msg_type == "question" and quiz_ai_ws:
                    student_ws = student_connections.get(data.get("name"))
                    if student_ws:
                        await student_ws.send_json(data)
                
                # Quiz AI sends final result
                elif msg_type == "final_result":
                    result = data.get("result")
                    quiz_results.append(result)
                    
                    # Send to student
                    student_ws = student_connections.get(result.get("name"))
                    if student_ws:
                        await student_ws.send_json(data)
                    
                    # Notify all teachers
                    for teacher_ws in clients["teachers"]:
                        await teacher_ws.send_json({
                            "type": "new_result",
                            "result": result
                        })
                
                # Teacher requests results
                elif msg_type == "show_results":
                    await ws.send_json({
                        "type": "results",
                        "data": quiz_results
                    })
                
                # Upload new quiz
                elif msg_type == "upload_quiz":
                    quiz_title = data.get("title")
                    questions = data.get("questions")
                    uploaded_quizzes[quiz_title] = {
                        "questions": len(questions),
                        "uploaded": True
                    }
                    # Notify quiz AI
                    if quiz_ai_ws:
                        await quiz_ai_ws.send_json({
                            "type": "new_quiz",
                            "title": quiz_title,
                            "questions": questions
                        })
            
            elif msg.type == web.WSMsgType.ERROR:
                print(f'WebSocket error: {ws.exception()}')
    
    finally:
        # Cleanup on disconnect
        if role == "student" and name in student_connections:
            student_connections.pop(name)
            clients["students"].discard(ws)
        elif role == "teacher":
            clients["teachers"].discard(ws)
        elif role == "quiz_ai":
            clients["quiz_ai"].discard(ws)
            if quiz_ai_ws == ws:
                quiz_ai_ws = None
    
    return ws

# ==================== APP INITIALIZATION ====================

def create_app():
    """Create and configure the web application"""
    app = web.Application()
    
    # Add routes
    app.router.add_get('/', serve_home)
    app.router.add_get('/student', serve_student)
    app.router.add_get('/teacher', serve_teacher)
    app.router.add_get('/ws', websocket_handler)
    
    return app

# ==================== MAIN ====================

if __name__ == '__main__':
    app = create_app()
    port = int(os.environ.get('PORT', 5000))
    
    print("=" * 60)
    print("🎓 RIZWAN NAQVI QUIZ PORTAL IS LIVE!")
    print("=" * 60)
    print(f"Server running on port {port}")
    print("Students and Teachers can now connect!")
    print("=" * 60)
    
    web.run_app(app, host='0.0.0.0', port=port)
