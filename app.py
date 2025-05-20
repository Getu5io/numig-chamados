from flask import Flask, render_template, request, redirect, session
import sqlite3
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'chave_simples'

USUARIOS = {
    "admin": "1234"
}

def init_db():
    with sqlite3.connect("erros.db") as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS erros (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                data_chamado TEXT,
                solicitante TEXT,
                setor TEXT,
                categoria TEXT,
                ferramenta TEXT,
                descricao TEXT,
                solucao TEXT,
                responsavel TEXT,
                data_conclusao TEXT,
                status TEXT,
                observacoes TEXT
            )
        """)

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        usuario = request.form["usuario"]
        senha = request.form["senha"]
        if usuario in USUARIOS and USUARIOS[usuario] == senha:
            session["usuario"] = usuario
            return redirect("/chamados")
        else:
            return render_template("login.html", erro="Usuário ou senha inválidos.")
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.pop("usuario", None)
    return redirect("/login")

@app.route("/", methods=["GET", "POST"])
def index():
    if "usuario" not in session:
        return redirect("/login")
    if request.method == "POST":
        solicitante = request.form["solicitante"]
        setor = request.form["setor"]
        categoria = request.form["categoria"]
        ferramenta = request.form["ferramenta"]
        descricao = request.form["descricao"]
        data_chamado = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        status = "Aberto"
        with sqlite3.connect("erros.db") as conn:
            conn.execute("""
                INSERT INTO erros 
                (data_chamado, solicitante, setor, categoria, ferramenta, descricao, status)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (data_chamado, solicitante, setor, categoria, ferramenta, descricao, status))
        return redirect("/chamados")
    return render_template("index.html")

@app.route("/chamados", methods=["GET", "POST"])
def chamados():
    if "usuario" not in session:
        return redirect("/login")

    filtro_status = request.args.get("filtro_status", "")
    filtro_setor = request.args.get("filtro_setor", "")

    query = "SELECT * FROM erros WHERE 1=1"
    params = []

    if filtro_status:
        query += " AND status=?"
        params.append(filtro_status)
    if filtro_setor:
        query += " AND setor LIKE ?"
        params.append(f"%{filtro_setor}%")

    with sqlite3.connect("erros.db") as conn:
        cursor = conn.cursor()
        if request.method == "POST":
            chamado_id = request.form["id"]
            solucao = request.form["solucao"]
            responsavel = request.form["responsavel"]
            data_conclusao = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            status = request.form["status"]
            observacoes = request.form["observacoes"]
            cursor.execute("""
                UPDATE erros
                SET solucao=?, responsavel=?, data_conclusao=?, status=?, observacoes=?
                WHERE id=?
            """, (solucao, responsavel, data_conclusao, status, observacoes, chamado_id))
            conn.commit()
            return redirect("/chamados")

        cursor.execute(query, params)
        chamados = cursor.fetchall()

        cursor.execute("SELECT COUNT(*) FROM erros")
        total = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM erros WHERE status='Aberto'")
        abertos = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM erros WHERE status='Concluído'")
        concluidos = cursor.fetchone()[0]

    return render_template("chamados.html", chamados=chamados, total=total, abertos=abertos, concluidos=concluidos)

if __name__ == "__main__":
    init_db()
    app.run(debug=True, host="0.0.0.0")
