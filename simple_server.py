#!/usr/bin/env python3
"""
Complete Quiz Server - Students just visit the URL!
No need to open HTML files - everything served from server
"""
import asyncio
import json
from aiohttp import web

clients = {"students": set(), "teachers": set(), "quiz_ai": set()}
student_connections = {}
quiz_results = []
quiz_ai_ws = None

# The HTML page that students/teachers will see
HTML_PAGE = """
<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Quiz Portal</title>
<style>
    * { margin: 0; padding: 0; box-sizing: border-box; }
    body {
        font-family: Arial, sans-serif;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        min-height: 100vh;
        padding: 20px;
    }
    .container {
        max-width: 800px;
        margin: 50px auto;
        background: white;
        border-radius: 15px;
        box-shadow: 0 10px 40px rgba(0,0,0,0.3);
        overflow: hidden;
    }
    .header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 30px;
        text-align: center;
    }
    .header h1 { font-size: 32px; }
    .content { padding: 40px; }
    .hidden { display: none !important; }
    
    #login-screen { text-align: center; }
    #login-screen h2 { color: #333; margin-bottom: 30px; }
    
    input[type="text"] {
        width: 100%;
        padding: 15px;
        margin: 10px 0;
        border: 2px solid #ddd;
        border-radius: 8px;
        font-size: 16px;
    }
    input[type="text"]:focus {
        outline: none;
        border-color: #667eea;
    }
    
    .role-buttons { display: flex; gap: 15px; margin-top: 20px; }
    
    button {
        flex: 1;
        padding: 15px 30px;
        background: #667eea;
        border: none;
        color: white;
        font-size: 16px;
        font-weight: 600;
        cursor: pointer;
        border-radius: 8px;
        transition: all 0.3s;
    }
    button:hover {
        background: #5568d3;
        transform: translateY(-2px);
    }
    button.teacher-btn { background: #28a745; }
    button.teacher-btn:hover { background: #218838; }
    
    #student-area .progress-bar {
        width: 100%;
        height: 8px;
        background: #e0e0e0;
        border-radius: 10px;
        margin-bottom: 20px;
        overflow: hidden;
    }
    .progress-fill {
        height: 100%;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        transition: width 0.3s;
    }
    .question-counter {
        text-align: center;
        color: #667eea;
        font-weight: 600;
        margin-bottom: 15px;
    }
    #q-text {
        color: #333;
        font-size: 20px;
        margin: 20px 0;
        padding: 20px;
        background: #f8f9fa;
        border-radius: 10px;
    }
    .answer-btn {
        display: block;
        width: 100%;
        margin: 10px 0;
        padding: 15px;
        text-align: left;
        border-radius: 8px;
        background: #f8f9fa;
        border: 2px solid #e0e0e0;
        cursor: pointer;
        font-size: 16px;
    }
    .answer-btn:hover {
        background: white;
        border-color: #667eea;
        transform: translateX(5px);
    }
    
    .score-card {
        text-align: center;
        padding: 30px;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border-radius: 10px;
        margin-bottom: 20px;
    }
    .score-card .big-score {
        font-size: 48px;
        font-weight: 700;
        margin: 10px 0;
    }
    
    #teacher-area button { width: 100%; margin: 10px 0; }
    
    table {
        width: 100%;
        border-collapse: collapse;
        margin-top: 20px;
    }
    th, td {
        padding: 12px;
        text-align: center;
        border-bottom: 1px solid #ddd;
    }
    th {
        background: #667eea;
        color: white;
        font-weight: 600;
    }
    tr:hover { background: #f8f9fa; }
    
    .rank-badge {
        display: inline-block;
        width: 30px;
        height: 30px;
        line-height: 30px;
        border-radius: 50%;
        color: white;
        font-weight: 700;
    }
    .rank-1 { background: #ffd700; color: #333; }
    .rank-2 { background: #c0c0c0; color: #333; }
    .rank-3 { background: #cd7f32; }
    .rank-other { background: #667eea; }
    
    .status {
        position: fixed;
        top: 20px;
        right: 20px;
        padding: 10px 20px;
        border-radius: 20px;
        color: white;
        font-weight: 600;
        z-index: 1000;
    }
    .status.connected { background: #28a745; }
    .status.disconnected { background: #dc3545; }
</style>
</head>
<body>

<div class="container">
    <div class="header">
        <h1>🎓 Quiz Portal</h1>
        <p>Students take quizzes • Teachers view results</p>
    </div>

    <div class="content">
        <div id="login-screen">
            <h2>Welcome! Join as:</h2>
            <input type="text" id="user-name" placeholder="Enter your name" maxlength="50">
            <div class="role-buttons">
                <button onclick="joinAs('student')">👨‍🎓 Student</button>
                <button class="teacher-btn" onclick="joinAs('teacher')">👨‍🏫 Teacher</button>
            </div>
        </div>

        <div id="student-area" class="hidden">
            <div id="start-quiz-btn">
                <h2>Ready to start?</h2>
                <button onclick="startQuiz()">🚀 Start Quiz (30 Questions)</button>
            </div>

            <div id="quiz-questions" class="hidden">
                <div class="progress-bar">
                    <div class="progress-fill" id="progress"></div>
                </div>
                <div class="question-counter" id="counter"></div>
                <div id="q-text"></div>
                <div id="answers"></div>
            </div>

            <div id="student-results" class="hidden">
                <div class="score-card">
                    <h2>🎉 Quiz Complete!</h2>
                    <div class="big-score" id="student-score"></div>
                    <div id="student-percentage"></div>
                </div>
                <table>
                    <thead>
                        <tr><th>Q#</th><th>Your Answer</th><th>Correct</th><th>Result</th></tr>
                    </thead>
                    <tbody id="student-details"></tbody>
                </table>
            </div>
        </div>

        <div id="teacher-area" class="hidden">
            <h2>📊 Teacher Dashboard</h2>
            <button onclick="refreshResults()">🔄 Refresh Results</button>
            
            <div id="stats" style="display:none; margin: 20px 0; text-align: center;">
                <p><strong>Total Students:</strong> <span id="total">0</span></p>
                <p><strong>Average Score:</strong> <span id="average">0%</span></p>
            </div>

            <table id="results-table">
                <thead>
                    <tr><th>Rank</th><th>Student Name</th><th>Score</th><th>Percentage</th></tr>
                </thead>
                <tbody id="teacher-results">
                    <tr>
                        <td colspan="4" style="padding: 40px; color: #999;">
                            No results yet. Waiting for students to complete quizzes...
                        </td>
                    </tr>
                </tbody>
            </table>
        </div>
    </div>
</div>

<script>
let ws = null;
let userName = "";
let userRole = "";
let currentQ = 0;
let totalQ = 30;

// Auto-detect server (uses current page's host)
const SERVER = window.location.host;

function showStatus(msg, connected) {
    let status = document.createElement('div');
    status.className = `status ${connected ? 'connected' : 'disconnected'}`;
    status.textContent = msg;
    document.body.appendChild(status);
    setTimeout(() => status.remove(), 3000);
}

function joinAs(role) {
    userName = document.getElementById('user-name').value.trim();
    if (!userName) {
        alert('Please enter your name!');
        return;
    }

    userRole = role;
    ws = new WebSocket(`ws://${SERVER}/ws`);

    ws.onopen = () => {
        console.log('Connected');
        showStatus('✓ Connected', true);
        
        ws.send(JSON.stringify({
            type: "register",
            role: role,
            name: userName
        }));

        document.getElementById('login-screen').classList.add('hidden');
        
        if (role === 'student') {
            document.getElementById('student-area').classList.remove('hidden');
        } else {
            document.getElementById('teacher-area').classList.remove('hidden');
            setTimeout(() => refreshResults(), 500);
        }
    };

    ws.onmessage = (evt) => {
        let data = JSON.parse(evt.data);

        if (data.type === 'question') {
            currentQ++;
            showQuestion(data);
        }

        if (data.type === 'final_result') {
            showStudentResults(data.result);
        }

        if (data.type === 'results') {
            displayTeacherResults(data.data);
        }

        if (data.type === 'new_result' && userRole === 'teacher') {
            showStatus(`New result from ${data.result.name}!`, true);
            refreshResults();
        }
    };

    ws.onerror = () => {
        showStatus('✗ Connection failed', false);
        alert('Cannot connect to server!');
    };

    ws.onclose = () => {
        showStatus('✗ Disconnected', false);
    };
}

function startQuiz() {
    ws.send(JSON.stringify({
        type: "choose_quiz",
        quiz: "quizA"
    }));

    document.getElementById('start-quiz-btn').classList.add('hidden');
    document.getElementById('quiz-questions').classList.remove('hidden');
}

function showQuestion(q) {
    let progress = (currentQ / totalQ) * 100;
    document.getElementById('progress').style.width = progress + '%';
    document.getElementById('counter').textContent = `Question ${currentQ} of ${totalQ}`;
    document.getElementById('q-text').textContent = q.question;

    let answersDiv = document.getElementById('answers');
    answersDiv.innerHTML = '';

    ['A', 'B', 'C', 'D'].forEach(letter => {
        let btn = document.createElement('button');
        btn.className = 'answer-btn';
        btn.textContent = `${letter}. ${q[letter]}`;
        btn.onclick = () => sendAnswer(letter);
        answersDiv.appendChild(btn);
    });
}

function sendAnswer(letter) {
    let buttons = document.querySelectorAll('.answer-btn');
    buttons.forEach(btn => btn.disabled = true);

    ws.send(JSON.stringify({
        type: "answer",
        answer: letter
    }));
}

function showStudentResults(result) {
    document.getElementById('quiz-questions').classList.add('hidden');
    document.getElementById('student-results').classList.remove('hidden');

    document.getElementById('student-score').textContent = `${result.score}/${result.possible}`;
    document.getElementById('student-percentage').textContent = `${result.percentage}%`;

    let tbody = document.getElementById('student-details');
    tbody.innerHTML = '';

    result.details.forEach(row => {
        let tr = document.createElement('tr');
        tr.innerHTML = `
            <td><strong>${row.id}</strong></td>
            <td>${row.selected}</td>
            <td>${row.correct}</td>
            <td style="color: ${row.is_correct ? '#28a745' : '#dc3545'}">
                ${row.is_correct ? '✓ Correct' : '✗ Wrong'}
            </td>
        `;
        tbody.appendChild(tr);
    });
}

function refreshResults() {
    if (!ws) return;
    ws.send(JSON.stringify({ type: "show_results" }));
}

function displayTeacherResults(results) {
    if (!results || results.length === 0) return;

    document.getElementById('stats').style.display = 'block';
    document.getElementById('total').textContent = results.length;
    
    let avg = (results.reduce((sum, r) => sum + r.percentage, 0) / results.length).toFixed(1);
    document.getElementById('average').textContent = avg + '%';

    results.sort((a, b) => b.percentage - a.percentage);

    let tbody = document.getElementById('teacher-results');
    tbody.innerHTML = '';

    results.forEach((r, i) => {
        let rank = i + 1;
        let rankClass = rank === 1 ? 'rank-1' : rank === 2 ? 'rank-2' : rank === 3 ? 'rank-3' : 'rank-other';
        
        let tr = document.createElement('tr');
        tr.innerHTML = `
            <td><span class="rank-badge ${rankClass}">${rank}</span></td>
            <td><strong>${r.name}</strong></td>
            <td>${r.score}/${r.possible}</td>
            <td><strong>${r.percentage}%</strong></td>
        `;
        tbody.appendChild(tr);
    });
}

document.getElementById('user-name').addEventListener('keypress', (e) => {
    if (e.key === 'Enter') {
        document.querySelector('.role-buttons button').click();
    }
});
</script>

</body>
</html>
"""

async def websocket_handler(request):
    ws = web.WebSocketResponse(heartbeat=30)
    await ws.prepare(request)
    
    role = None
    name = None
    
    try:
        async for msg in ws:
            if msg.type == web.WSMsgType.TEXT:
                data = json.loads(msg.data)
                msg_type = data.get("type")
                
                if msg_type == "register":
                    role = data.get("role")
                    name = data.get("name", "unknown")
                    
                    if role == "student":
                        clients["students"].add(ws)
                        student_connections[name] = ws
                        print(f"✓ Student '{name}' joined")
                        
                    elif role == "teacher":
                        clients["teachers"].add(ws)
                        print(f"✓ Teacher '{name}' joined")
                        
                    elif role == "quiz_ai":
                        clients["quiz_ai"].add(ws)
                        global quiz_ai_ws
                        quiz_ai_ws = ws
                        print(f"✓ AI connected")
                
                elif msg_type == "choose_quiz":
                    if role == "student" and quiz_ai_ws:
                        await quiz_ai_ws.send_json({
                            "type": "start_quiz",
                            "name": name,
                            "quiz": data.get("quiz")
                        })
                        print(f"→ Starting quiz for {name}")
                
                elif msg_type == "answer":
                    if role == "student" and quiz_ai_ws:
                        await quiz_ai_ws.send_json({
                            "type": "student_answer",
                            "name": name,
                            "answer": data.get("answer")
                        })
                
                elif msg_type == "question":
                    student_name = data.get("name")
                    student_ws = student_connections.get(student_name)
                    if student_ws:
                        await student_ws.send_json(data)
                
                elif msg_type == "final_result":
                    result = data.get("result")
                    if result:
                        quiz_results.append(result)
                        
                        student_name = result.get("name")
                        student_ws = student_connections.get(student_name)
                        if student_ws:
                            await student_ws.send_json(data)
                        
                        for teacher_ws in clients["teachers"]:
                            await teacher_ws.send_json({
                                "type": "new_result",
                                "result": result
                            })
                        print(f"✓ {student_name} completed: {result['score']}/{result['possible']}")
                
                elif msg_type == "show_results":
                    if role == "teacher":
                        await ws.send_json({
                            "type": "results",
                            "data": quiz_results
                        })
    
    finally:
        if role == "student" and name:
            student_connections.pop(name, None)
            print(f"✗ Student '{name}' left")
        elif role == "quiz_ai":
            quiz_ai_ws = None
            print(f"✗ AI disconnected")
    
    return ws

async def serve_page(request):
    """Serve the quiz portal page"""
    return web.Response(text=HTML_PAGE, content_type='text/html')

app = web.Application()
app.router.add_get('/', serve_page)  # Main page
app.router.add_get('/ws', websocket_handler)  # WebSocket

if __name__ == '__main__':
    print("="*60)
    print("🚀 Quiz Server Started!")
    print("="*60)
    print("Students & Teachers: http://localhost:5000")
    print("Network access: http://YOUR_IP:5000")
    print("="*60)
    print("\nWaiting for connections...")
    print("="*60)
    web.run_app(app, host='0.0.0.0', port=5000)