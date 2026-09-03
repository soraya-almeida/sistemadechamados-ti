from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    session,
    flash
)

from database import conectar, criar_tabelas

from functools import wraps


app = Flask(__name__)

# Chave usada para proteger a sessão
app.secret_key = "chave-secreta-sistema-ti"


# Cria as tabelas
criar_tabelas()


# =====================================================
# PROTEÇÃO DE LOGIN
# =====================================================

def login_obrigatorio(func):

    @wraps(func)
    def verificar_login(*args, **kwargs):

        if "usuario_id" not in session:

            return redirect(
                url_for("login")
            )

        return func(*args, **kwargs)

    return verificar_login


# =====================================================
# LOGIN
# =====================================================

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form["email"]

        senha = request.form["senha"]


        conn = conectar()

        usuario = conn.execute("""
            SELECT *
            FROM usuarios
            WHERE email = ?
            AND senha = ?
        """, (
            email,
            senha
        )).fetchone()

        conn.close()


        if usuario:

            session["usuario_id"] = usuario["id"]

            session["usuario_nome"] = usuario["nome"]

            session["usuario_tipo"] = usuario["tipo"]


            return redirect(
                url_for("index")
            )


        return render_template(
            "login.html",
            erro="E-mail ou senha incorretos."
        )


    return render_template("login.html")


# =====================================================
# LOGOUT
# =====================================================

@app.route("/logout")
def logout():

    session.clear()

    return redirect(
        url_for("login")
    )


# =====================================================
# CADASTRO
# =====================================================

@app.route("/cadastro", methods=["GET", "POST"])
def cadastro():
    if request.method == "POST":
        nome = request.form.get("nome", "").strip()
        email = request.form.get("email", "").strip().lower()
        senha = request.form.get("senha", "")
        if not nome or not email or not senha:
            return render_template("cadastro.html", erro="Preencha todos os campos.")
        conn = conectar()
        try:
            conn.execute("INSERT INTO usuarios (nome, email, senha, tipo) VALUES (?, ?, ?, 'usuario')", (nome, email, senha))
            conn.commit()
        except Exception:
            conn.close()
            return render_template("cadastro.html", erro="Este e-mail já está cadastrado.")
        conn.close()
        return redirect(url_for("login"))
    return render_template("cadastro.html")



# =====================================================
# PÁGINA PRINCIPAL
# =====================================================

@app.route("/")
@login_obrigatorio
def index():

    pesquisa = request.args.get(
        "pesquisa",
        ""
    )

    status = request.args.get(
        "status",
        ""
    )

    prioridade = request.args.get(
        "prioridade",
        ""
    )


    usuario_id = session["usuario_id"]

    tipo_usuario = session["usuario_tipo"]


    conn = conectar()


    query = """
        SELECT *
        FROM chamados
        WHERE 1=1
    """


    parametros = []


    # Usuário comum vê apenas seus chamados
    if tipo_usuario == "usuario":

        query += """
            AND usuario_id = ?
        """

        parametros.append(
            usuario_id
        )


    # Pesquisa
    if pesquisa:

        query += """
            AND (
                nome LIKE ?
                OR titulo LIKE ?
                OR descricao LIKE ?
            )
        """

        termo = f"%{pesquisa}%"


        parametros.extend([
            termo,
            termo,
            termo
        ])


    # Status
    if status:

        query += """
            AND status = ?
        """

        parametros.append(
            status
        )


    # Prioridade
    if prioridade:

        query += """
            AND prioridade = ?
        """

        parametros.append(
            prioridade
        )


    query += """
        ORDER BY id DESC
    """


    chamados = conn.execute(
        query,
        parametros
    ).fetchall()


    # =================================================
    # CONTADORES
    # =================================================

    if tipo_usuario == "usuario":

        filtro_usuario = """
            AND usuario_id = ?
        """

        parametro_usuario = [
            usuario_id
        ]

    else:

        filtro_usuario = ""

        parametro_usuario = []


    total = conn.execute(
        f"""
        SELECT COUNT(*)
        FROM chamados
        WHERE 1=1
        {filtro_usuario}
        """,
        parametro_usuario
    ).fetchone()[0]


    abertos = conn.execute(
        f"""
        SELECT COUNT(*)
        FROM chamados
        WHERE status = 'Aberto'
        {filtro_usuario}
        """,
        parametro_usuario
    ).fetchone()[0]


    andamento = conn.execute(
        f"""
        SELECT COUNT(*)
        FROM chamados
        WHERE status = 'Em andamento'
        {filtro_usuario}
        """,
        parametro_usuario
    ).fetchone()[0]


    resolvidos = conn.execute(
        f"""
        SELECT COUNT(*)
        FROM chamados
        WHERE status = 'Resolvido'
        {filtro_usuario}
        """,
        parametro_usuario
    ).fetchone()[0]


    conn.close()


    return render_template(
        "index.html",

        chamados=chamados,

        total=total,

        abertos=abertos,

        andamento=andamento,

        resolvidos=resolvidos,

        pesquisa=pesquisa,

        status=status,

        prioridade=prioridade
    )


# =====================================================
# CRIAR CHAMADO
# =====================================================

@app.route("/novo-chamado", methods=["POST"])
@login_obrigatorio
def novo_chamado():
    usuario_id = session["usuario_id"]
    setor = request.form.get("setor", "").strip()
    titulo = request.form.get("titulo", "").strip()
    descricao = request.form.get("descricao", "").strip()
    prioridade = request.form.get("prioridade", "").strip()
    if not setor or not titulo or not descricao or prioridade not in ["Baixa", "Média", "Alta", "Urgente"]:
        flash("Preencha corretamente todos os campos do chamado.", "erro")
        return redirect(url_for("index"))
    conn=conectar()
    usuario=conn.execute("SELECT * FROM usuarios WHERE id=?",(usuario_id,)).fetchone()
    if not usuario:
        conn.close(); session.clear(); return redirect(url_for("login"))
    cur=conn.execute("INSERT INTO chamados (usuario_id,nome,email,setor,titulo,descricao,prioridade) VALUES (?,?,?,?,?,?,?)",(usuario_id,usuario["nome"],usuario["email"],setor,titulo,descricao,prioridade))
    chamado_id=cur.lastrowid
    conn.execute("INSERT INTO historico (chamado_id,usuario_id,acao) VALUES (?,?,?)",(chamado_id,usuario_id,"Chamado criado pelo solicitante"))
    conn.commit(); conn.close()
    flash(f"Chamado #{chamado_id} aberto com sucesso.","sucesso")
    return redirect(url_for("visualizar_chamado",id=chamado_id))



# =====================================================
# VISUALIZAR CHAMADO
# =====================================================

@app.route("/chamado/<int:id>")
@login_obrigatorio
def visualizar_chamado(id):
    conn=conectar()
    chamado=conn.execute("SELECT chamados.*, usuarios.nome AS tecnico_nome FROM chamados LEFT JOIN usuarios ON chamados.tecnico_id=usuarios.id WHERE chamados.id=?",(id,)).fetchone()
    if chamado is None:
        conn.close(); return "Chamado não encontrado",404
    if session["usuario_tipo"]=="usuario" and chamado["usuario_id"]!=session["usuario_id"]:
        conn.close(); return "Acesso negado",403
    comentarios=conn.execute("SELECT c.*,u.nome AS usuario_nome,u.tipo AS usuario_tipo FROM comentarios c INNER JOIN usuarios u ON c.usuario_id=u.id WHERE c.chamado_id=? ORDER BY c.id ASC",(id,)).fetchall()
    historico=conn.execute("SELECT h.*,u.nome AS usuario_nome,u.tipo AS usuario_tipo FROM historico h INNER JOIN usuarios u ON h.usuario_id=u.id WHERE h.chamado_id=? ORDER BY h.id ASC",(id,)).fetchall()
    conn.close()
    return render_template("chamado.html",chamado=chamado,comentarios=comentarios,historico=historico)



# =====================================================
# ASSUMIR CHAMADO
# =====================================================

@app.route("/chamado/<int:id>/assumir", methods=["POST"])
@login_obrigatorio
def assumir_chamado(id):
    if session["usuario_tipo"]!="tecnico": return "Acesso negado",403
    conn=conectar(); chamado=conn.execute("SELECT * FROM chamados WHERE id=?",(id,)).fetchone()
    if chamado is None: conn.close(); return "Chamado não encontrado",404
    if chamado["tecnico_id"] is not None:
        conn.close(); flash("Este chamado já possui um técnico responsável.","erro"); return redirect(url_for("visualizar_chamado",id=id))
    tecnico_id=session["usuario_id"]
    conn.execute("UPDATE chamados SET tecnico_id=?,status='Em andamento' WHERE id=?",(tecnico_id,id))
    conn.execute("INSERT INTO historico (chamado_id,usuario_id,acao) VALUES (?,?,?)",(id,tecnico_id,"Chamado assumido pelo técnico e colocado em Em andamento"))
    conn.commit(); conn.close()
    flash("Chamado assumido com sucesso. Você é o técnico responsável.","sucesso")
    return redirect(url_for("visualizar_chamado",id=id))



# ADICIONAR COMENTÁRIO
# =====================================================

@app.route("/chamado/<int:id>/comentario", methods=["POST"])
@login_obrigatorio
def adicionar_comentario(id):
    usuario_id=session["usuario_id"]; mensagem=request.form.get("mensagem","").strip()
    conn=conectar(); chamado=conn.execute("SELECT * FROM chamados WHERE id=?",(id,)).fetchone()
    if chamado is None: conn.close(); return "Chamado não encontrado",404
    if session["usuario_tipo"]=="usuario" and chamado["usuario_id"]!=usuario_id: conn.close(); return "Acesso negado",403
    if not mensagem:
        conn.close(); flash("Digite uma mensagem antes de enviar.","erro"); return redirect(url_for("visualizar_chamado",id=id))
    conn.execute("INSERT INTO comentarios (chamado_id,usuario_id,mensagem) VALUES (?,?,?)",(id,usuario_id,mensagem))
    conn.execute("INSERT INTO historico (chamado_id,usuario_id,acao) VALUES (?,?,?)",(id,usuario_id,"Novo comentário adicionado"))
    conn.commit(); conn.close(); flash("Comentário enviado.","sucesso")
    return redirect(url_for("visualizar_chamado",id=id))



# =====================================================
# ALTERAR STATUS
# =====================================================

@app.route("/chamado/<int:id>/status", methods=["POST"])
@login_obrigatorio
def alterar_status(id):
    if session["usuario_tipo"]!="tecnico": return "Acesso negado",403
    novo_status=request.form.get("status","").strip(); solucao=request.form.get("solucao","").strip()
    validos=["Aberto","Em andamento","Resolvido","Cancelado"]
    if novo_status not in validos:
        flash("O status selecionado é inválido.","erro"); return redirect(url_for("visualizar_chamado",id=id))
    conn=conectar(); chamado=conn.execute("SELECT * FROM chamados WHERE id=?",(id,)).fetchone()
    if chamado is None: conn.close(); return "Chamado não encontrado",404
    if novo_status=="Resolvido" and not solucao:
        conn.close(); flash("Para marcar como Resolvido, descreva a solução aplicada.","erro"); return redirect(url_for("visualizar_chamado",id=id))
    anterior=chamado["status"]; antiga=chamado["solucao"] or ""
    if anterior==novo_status and solucao==antiga:
        conn.close(); flash("Nenhuma alteração foi realizada.","erro"); return redirect(url_for("visualizar_chamado",id=id))
    tecnico_id=chamado["tecnico_id"] or session["usuario_id"]
    conn.execute("UPDATE chamados SET status=?,solucao=?,tecnico_id=? WHERE id=?",(novo_status,solucao,tecnico_id,id))
    partes=[]
    if anterior!=novo_status: partes.append(f"Status alterado de {anterior} para {novo_status}")
    if solucao!=antiga and solucao: partes.append("Solução/observação técnica atualizada")
    if chamado["tecnico_id"] is None: partes.append("Técnico responsável definido automaticamente")
    conn.execute("INSERT INTO historico (chamado_id,usuario_id,acao) VALUES (?,?,?)",(id,session["usuario_id"]," | ".join(partes)))
    conn.commit(); conn.close(); flash(f"Chamado #{id} atualizado com sucesso.","sucesso")
    return redirect(url_for("visualizar_chamado",id=id))



# =====================================================
# EXECUTAR
# =====================================================

if __name__ == "__main__":

    app.run(
        debug=True
    )