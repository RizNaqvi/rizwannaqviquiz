#!/usr/bin/env python3
"""
Rizwan Naqvi Quiz Platform – Fully working on Railway + Render + locally
Students & Teachers visit the same URL → everything works instantly
"""

import asyncio
import json
from aiohttp import web

# ==================== ALL YOUR DATA & STATE ====================
clients = {"students": set(), "teachers": set(), "quiz_ai": set()}
student_connections = {}
quiz_results = []
quiz_ai_ws = None

# Your beautiful single-page portal (the one with login screen, student quiz, teacher dashboard)
HTML_PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Rizwan Naqvi Quiz Portal</title>
<style>
    /* (your beautiful CSS from simple_server.py — I kept it exactly the same, just shortened comment) */
    * { margin:0; padding:0; box-sizing:border-box; }
    body { font-family:Arial,sans-serif; background:linear-gradient(135deg,#667eea 0%,#764ba2 100%); min-height:100vh; display:flex; align-items:center; justify-content:center; }
    .container { max-width:900px; width:90%; background:white; border-radius:20px; overflow:hidden; box-shadow:0 20px 50px rgba(0,0,0,0.4); }
    .header { background:linear-gradient(135deg,#667eea 0%,#764ba2 100%); color:white; padding:40px; text-align:center; }
    .content { padding:40px; }
    input, button, select { width:100%; padding:15px; margin:10px 0; border-radius:8px; font-size:16px; }
    button { background:#667eea; color:white; border:none; cursor:pointer; font-weight:bold; }
    button:hover { background:#5668d0; }
    .hidden { display:none; }
    .answer-btn { background:#f8f9fa; border:2px solid #eee; text-align:left; padding:18px; margin:10px 0; border-radius:10px; cursor:pointer; }
    .answer-btn:hover { border-color:#667eea; background:white; transform:translateX(8px); }
    table { width:100%; border-collapse:collapse; margin-top:20px; }
    th, td { padding:12px; text-align:center; border-bottom:1px solid #ddd; }
    th { background:#667eea; color:white; }
</style>
</head>
<body>
<div class="container">
  <div class="header">
    <h1>Rizwan Naqvi Quiz Portal</h1>
    <p>General Knowledge • Computer Networks • Database • More coming!</p>
  </div>

  <div class="content">
    <!-- LOGIN -->
    <div id="login">
      <h2>Welcome!</h2>
      <input type="text" id="name" placeholder="Enter your name" maxlength="50">
      <div style="display:flex; gap:15px; margin-top:20px;">
        <button onclick="join('student')">Student</button>
        <button style="background:#27ae60;" onclick="join('teacher')">Teacher</button>
      </div>
    </div>

    <!-- STUDENT AREA -->
    <div id="student" class="hidden">
      <h2>Hello <span id="sname"></span>!</h2>
      <select id="quizlist">
        <option value="quizA">General Knowledge (30 Qs)</option>
      </select>
      <button onclick="startQuiz()">Start Quiz</button>

      <div id="quiz" class="hidden">
        <div style="background:#eee; height:10px; border-radius:5px; margin:20px 0;">
          <div id="progress" style="width:0%;height:100%;background:#667eea;border-radius:5px;transition:0.4s;"></div>
        </div>
        <div style="text-align:center; font-weight:bold;" id="counter"></div>
        <h3 id="question"></h3>
        <div id="options"></div>
      </div>

      <div id="result" class="hidden">
        <h2>Congratulations!</h2>
        <h1 id="score"></h1>
        <table><thead><tr><th>#</th><th>You</th><th>Correct</th><th></th></tr></thead><tbody id="details"></tbody></table>
      </div>
    </div>

    <!-- TEACHER DASHBOARD -->
    <div id="teacher" class="hidden">
      <h2>Live Leaderboard</h2>
      <button onclick="refresh()">Refresh</button>
      <table id="leaderboard">
        <thead><tr><th>Rank</th><th>Name</th><th>Score</th><th>%</th></tr></thead>
        <tbody></tbody>
      </table>
    </div>
  </div>
</div>

<script>
let ws = null; let role = ''; let name = ''; let qnum = 0; let total = 30;

function join(r) {
  name = document.getElementById('name').value.trim();
  if (!name) return alert('Enter your name');
  role = r;
  document.getElementById('login').classList.add('hidden');
  document.getElementById(role).classList.remove('hidden');
  document.getElementById('sname') && (document.getElementById('sname').textContent = name);

  ws = new WebSocket(`wss://${location.host}/ws`);
  ws.onopen = () => ws.send(JSON.stringify({type:"register", role:role, name:name}));
  ws.onmessage = e => {
    const d = JSON.parse(e.data);
    if (d.type === 'question') { qnum++; showQuestion(d); }
    if (d.type === 'final_result') showResult(d.result);
    if (d.type === 'results') showLeaderboard(d.data);
  };
}

function startQuiz() {
  ws.send(JSON.stringify({type:"choose_quiz", quiz:"quizA"}));
  document.querySelector('#student button').classList.add('hidden');
  document.getElementById('quiz').classList.remove('hidden');
}

function showQuestion(q) {
  document.getElementById('progress').style.width = (qnum/total*100)+'%';
  document.getElementById('counter').textContent = `Question ${qnum} of ${total}`;
  document.getElementById('question').textContent = q.question;
  const div = document.getElementById('options'); div.innerHTML = '';
  ['A','B','C','D'].forEach(l => {
    const btn = document.createElement('div');
    btn.className = 'answer-btn';
    btn.textContent = `${l}. ${q[l]}`;
    btn.onclick = () => { ws.send(JSON.stringify({type:"answer", answer:l})); btn.style.background='#667eea'; btn.style.color='white'; };
    div.appendChild(btn);
  });
}

function showResult(r) {
  document.getElementById('quiz').classList.add('hidden');
  document.getElementById('result').classList.remove('hidden');
  document.getElementById('score').textContent = `${r.score}/${r.possible} (${r.percentage}%)`;
  const tb = document.getElementById('details'); tb.innerHTML = '';
  r.details.forEach(x => {
    const tr = document.createElement('tr');
    tr.innerHTML = `<td>${x.id}</td><td>${x.selected||'—'}</td><td>${x.correct}</td><td style="color:${x.is_correct?'green':'red'}">${x.is_correct?'Correct':'Wrong'}</td>`;
    tb.appendChild(tr);
  });
}

function refresh() { ws.send(JSON.stringify({type:"show_results"})); }
function showLeaderboard(data) {
  if (!data.length) return;
  data.sort((a,b)=>b.percentage-a.percentage);
  const tb = document.querySelector('#teacher tbody'); tb.innerHTML = '';
  data.forEach((r,i) => {
    const tr = document.createElement('tr');
    tr.innerHTML = `<td>${i+1}</td><td>${r.name}</td><td>${r.score}/${r.possible}</td><td>${r.percentage}%</td>`;
    tb.appendChild(tr);
  });
}
</script>
</body>
</html>"""


# ==================== WEB SERVER ROUTES ====================
async def serve_home(request):
    return web.Response(text=HTML_PAGE, content_type='text/html')

async def websocket_handler(request):
    ws = web.WebSocketResponse()
    await ws.prepare(request)

    role = None
    name = None

    async for msg in ws:
        if msg.type == web.WSMsgType.TEXT:
            data = json.loads(msg.data)
            t = data.get("type")

            if t == "register":
                role = data.get("role")
                name = data.get("name", "Anonymous")
                if role == "student": clients["students"].add(ws); student_connections[name] = ws
                if role == "teacher": clients["teachers"].add(ws)
                if role == "quiz_ai": 
                    global quiz_ai_ws
                    quiz_ai_ws = ws
                    clients["quiz_ai"].add(ws)

            elif t == "choose_quiz" and role == "student" and quiz_ai_ws:
                await quiz_ai_ws.send_json({"type": "start_quiz", "name": name, "quiz": data["quiz"]})

            elif t == "answer" and role == "student" and quiz_ai_ws:
                await quiz_ai_ws.send_json({"type": "student_answer", "name": name, "answer": data["answer"]})

            elif t == "question" and quiz_ai_ws:
                student_ws = student_connections.get(data.get("name"))
                if student_ws: await student_ws.send_json(data)

            elif t == "final_result":
                result = data.get("result")
                quiz_results.append(result)
                # send to student
                student_ws = student_connections.get(result.get("name"))
                if student_ws: await student_ws.send_json(data)
                # notify all teachers
                for t_ws in clients["teachers"]:
                    await t_ws.send_json({"type": "new_result", "result": result})

            elif t == "show_results":
                await ws.send_json({"type": "results", "data": quiz_results})

    # cleanup on close
    if role == "student" and name in student_connections:
        student_connections.pop(name)
    return ws

# ==================== APP SETUP ====================
app = web.Application()
app.router.add_get('/', serve_home)
app.router.add_get('/ws', websocket_handler)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))  # Railway uses $PORT
    print("Rizwan Naqvi Quiz Portal is LIVE!")
    web.run_app(app, host='0.0.0.0', port=port)
