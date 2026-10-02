from flask import Flask, request, redirect, url_for, flash, render_template_string
import sqlite3
from datetime import datetime

app = Flask(__name__)
app.secret_key = "fila-atendimento-secret"

BANCO = "fila.db"


# ============================================================
# BANCO DE DADOS
# ============================================================

def conectar():
    conexao = sqlite3.connect(BANCO)
    conexao.row_factory = sqlite3.Row
    return conexao


def criar_banco():
    conexao = conectar()

    conexao.execute("""
        CREATE TABLE IF NOT EXISTS atendimentos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            prioridade TEXT NOT NULL DEFAULT 'Normal',
            status TEXT NOT NULL DEFAULT 'Aguardando',
            criado_em TEXT NOT NULL,
            chamado_em TEXT,
            finalizado_em TEXT
        )
    """)

    conexao.commit()
    conexao.close()


# ============================================================
# HTML DA APLICAÇÃO
# ============================================================

HTML = """
<!DOCTYPE html>
<html lang="pt-BR">

<head>

    <meta charset="UTF-8">

    <meta
        name="viewport"
        content="width=device-width, initial-scale=1.0"
    >

    <title>Fila de Atendimento</title>

    <style>

        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }

        body {
            font-family: Arial, Helvetica, sans-serif;
            background: #f1f5f9;
            color: #1e293b;
        }

        header {
            background: #2563eb;
            color: white;
            padding: 30px 20px;
            text-align: center;
        }

        header h1 {
            margin-bottom: 8px;
        }

        main {
            width: 92%;
            max-width: 1200px;
            margin: 30px auto;
        }

        .card {
            background: white;
            padding: 25px;
            margin-bottom: 25px;
            border-radius: 12px;
            box-shadow: 0 3px 12px rgba(0,0,0,0.08);
        }

        .card h2 {
            margin-bottom: 20px;
        }

        .formulario {
            display: grid;
            grid-template-columns: 2fr 1fr auto;
            gap: 15px;
            align-items: end;
        }

        label {
            display: block;
            margin-bottom: 7px;
            font-weight: bold;
        }

        input,
        select {
            width: 100%;
            padding: 12px;
            border: 1px solid #cbd5e1;
            border-radius: 7px;
            font-size: 15px;
        }

        button,
        .botao {
            display: inline-block;
            border: none;
            border-radius: 7px;
            padding: 11px 16px;
            text-decoration: none;
            cursor: pointer;
            font-weight: bold;
        }

        button {
            background: #2563eb;
            color: white;
        }

        button:hover {
            background: #1d4ed8;
        }

        .cabecalho-fila {
            display: flex;
            justify-content: space-between;
            align-items: center;
            gap: 15px;
            margin-bottom: 20px;
        }

        .chamar {
            background: #16a34a;
            color: white;
        }

        .chamar:hover {
            background: #15803d;
        }

        .tabela {
            width: 100%;
            border-collapse: collapse;
        }

        .tabela th,
        .tabela td {
            padding: 13px;
            text-align: left;
            border-bottom: 1px solid #e2e8f0;
        }

        .tabela th {
            background: #f8fafc;
        }

        .badge {
            display: inline-block;
            padding: 5px 10px;
            border-radius: 20px;
            font-size: 13px;
            font-weight: bold;
        }

        .normal {
            background: #e2e8f0;
            color: #334155;
        }

        .preferencial {
            background: #fef3c7;
            color: #92400e;
        }

        .aguardando {
            background: #dbeafe;
            color: #1e40af;
        }

        .atendimento {
            background: #dcfce7;
            color: #166534;
        }

        .concluido {
            background: #dcfce7;
            color: #166534;
        }

        .cancelado {
            background: #fee2e2;
            color: #991b1b;
        }

        .concluir {
            background: #16a34a;
            color: white;
        }

        .cancelar {
            background: #dc2626;
            color: white;
        }

        .vazio {
            padding: 30px;
            text-align: center;
            color: #64748b;
        }

        .alerta {
            padding: 15px;
            margin-bottom: 20px;
            border-radius: 8px;
            font-weight: bold;
        }

        .sucesso {
            background: #dcfce7;
            color: #166534;
        }

        .erro {
            background: #fee2e2;
            color: #991b1b;
        }

        .cliente-atual {
            background: #eff6ff;
            border-left: 5px solid #2563eb;
            padding: 20px;
            border-radius: 8px;
        }

        .cliente-atual h3 {
            font-size: 25px;
            margin-bottom: 10px;
        }

        .cliente-atual p {
            margin-bottom: 15px;
        }

        .estatisticas {
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 15px;
            margin-bottom: 25px;
        }

        .estatistica {
            background: white;
            padding: 20px;
            border-radius: 10px;
            text-align: center;
            box-shadow: 0 3px 10px rgba(0,0,0,0.06);
        }

        .estatistica strong {
            display: block;
            font-size: 30px;
            color: #2563eb;
            margin-top: 5px;
        }

        .acoes {
            display: flex;
            gap: 7px;
            flex-wrap: wrap;
        }

        @media (max-width: 800px) {

            .formulario {
                grid-template-columns: 1fr;
            }

            .estatisticas {
                grid-template-columns: repeat(2, 1fr);
            }

            .cabecalho-fila {
                flex-direction: column;
                align-items: stretch;
            }

            .tabela {
                min-width: 800px;
            }

            .tabela-container {
                overflow-x: auto;
            }
        }

    </style>

</head>

<body>

<header>

    <h1>📋 Fila de Atendimento</h1>

    <p>Sistema de gerenciamento de clientes</p>

</header>


<main>

    {% with mensagens = get_flashed_messages(with_categories=true) %}

        {% if mensagens %}

            {% for categoria, mensagem in mensagens %}

                <div class="alerta {{ categoria }}">
                    {{ mensagem }}
                </div>

            {% endfor %}

        {% endif %}

    {% endwith %}


    <!-- ESTATÍSTICAS -->

    <div class="estatisticas">

        <div class="estatistica">
            Aguardando
            <strong>{{ aguardando }}</strong>
        </div>

        <div class="estatistica">
            Em atendimento
            <strong>{{ em_atendimento }}</strong>
        </div>

        <div class="estatistica">
            Concluídos
            <strong>{{ concluidos }}</strong>
        </div>

        <div class="estatistica">
            Cancelados
            <strong>{{ cancelados }}</strong>
        </div>

    </div>


    <!-- CADASTRO -->

    <section class="card">

        <h2>➕ Cadastrar cliente</h2>

        <form
            action="{{ url_for('cadastrar') }}"
            method="POST"
            class="formulario"
        >

            <div>

                <label for="nome">
                    Nome do cliente
                </label>

                <input
                    type="text"
                    id="nome"
                    name="nome"
                    placeholder="Digite o nome do cliente"
                    required
                >

            </div>


            <div>

                <label for="prioridade">
                    Prioridade
                </label>

                <select
                    id="prioridade"
                    name="prioridade"
                >

                    <option value="Normal">
                        Normal
                    </option>

                    <option value="Preferencial">
                        Preferencial
                    </option>

                </select>

            </div>


            <button type="submit">
                Adicionar
            </button>

        </form>

    </section>


    <!-- CLIENTE ATUAL -->

    {% if atual %}

    <section class="card">

        <h2>🔔 Cliente em atendimento</h2>

        <div class="cliente-atual">

            <h3>
                {{ atual["nome"] }}
            </h3>

            <p>
                Prioridade:
                <strong>
                    {{ atual["prioridade"] }}
                </strong>
            </p>

            <p>
                Chamado em:
                {{ atual["chamado_em"] }}
            </p>

            <a
                href="{{ url_for('concluir', id=atual['id']) }}"
                class="botao concluir"
            >
                ✓ Concluir atendimento
            </a>

        </div>

    </section>

    {% endif %}


    <!-- FILA -->

    <section class="card">

        <div class="cabecalho-fila">

            <h2>👥 Fila de espera</h2>

            <a
                href="{{ url_for('chamar') }}"
                class="botao chamar"
            >
                📢 Chamar próximo
            </a>

        </div>


        {% if fila %}

        <div class="tabela-container">

            <table class="tabela">

                <thead>

                    <tr>
                        <th>Posição</th>
                        <th>Nome</th>
                        <th>Prioridade</th>
                        <th>Status</th>
                        <th>Entrada</th>
                        <th>Ações</th>
                    </tr>

                </thead>

                <tbody>

                    {% for cliente in fila %}

                    <tr>

                        <td>
                            {{ loop.index }}
                        </td>

                        <td>
                            <strong>
                                {{ cliente["nome"] }}
                            </strong>
                        </td>

                        <td>

                            {% if cliente["prioridade"] == "Preferencial" %}

                                <span class="badge preferencial">
                                    Preferencial
                                </span>

                            {% else %}

                                <span class="badge normal">
                                    Normal
                                </span>

                            {% endif %}

                        </td>

                        <td>

                            {% if cliente["status"] == "Aguardando" %}

                                <span class="badge aguardando">
                                    Aguardando
                                </span>

                            {% else %}

                                <span class="badge atendimento">
                                    Em Atendimento
                                </span>

                            {% endif %}

                        </td>

                        <td>
                            {{ cliente["criado_em"] }}
                        </td>

                        <td>

                            <div class="acoes">

                                {% if cliente["status"] == "Em Atendimento" %}

                                <a
                                    href="{{ url_for('concluir', id=cliente['id']) }}"
                                    class="botao concluir"
                                >
                                    Concluir
                                </a>

                                {% endif %}


                                <a
                                    href="{{ url_for('cancelar', id=cliente['id']) }}"
                                    class="botao cancelar"
                                    onclick="return confirm('Deseja cancelar este atendimento?')"
                                >
                                    Cancelar
                                </a>

                            </div>

                        </td>

                    </tr>

                    {% endfor %}

                </tbody>

            </table>

        </div>

        {% else %}

        <div class="vazio">
            <h3>Fila vazia</h3>
            <p>Nenhum cliente aguardando atendimento.</p>
        </div>

        {% endif %}

    </section>


    <!-- HISTÓRICO -->

    <section class="card">

        <h2>📜 Histórico de atendimentos</h2>

        {% if historico %}

        <div class="tabela-container">

            <table class="tabela">

                <thead>

                    <tr>
                        <th>Nome</th>
                        <th>Prioridade</th>
                        <th>Status</th>
                        <th>Entrada</th>
                        <th>Finalização</th>
                    </tr>

                </thead>

                <tbody>

                    {% for cliente in historico %}

                    <tr>

                        <td>
                            {{ cliente["nome"] }}
                        </td>

                        <td>
                            {{ cliente["prioridade"] }}
                        </td>

                        <td>

                            {% if cliente["status"] == "Concluído" %}

                                <span class="badge concluido">
                                    Concluído
                                </span>

                            {% else %}

                                <span class="badge cancelado">
                                    Cancelado
                                </span>

                            {% endif %}

                        </td>

                        <td>
                            {{ cliente["criado_em"] }}
                        </td>

                        <td>
                            {{ cliente["finalizado_em"] }}
                        </td>

                    </tr>

                    {% endfor %}

                </tbody>

            </table>

        </div>

        {% else %}

        <div class="vazio">
            Nenhum atendimento finalizado ainda.
        </div>

        {% endif %}

    </section>

</main>


<script>

    // Atualização automática da página a cada 10 segundos.
    setTimeout(function() {
        window.location.reload();
    }, 10000);

</script>

</body>

</html>
"""


# ============================================================
# PÁGINA PRINCIPAL
# ============================================================

@app.route("/")
def index():

    conexao = conectar()

    # Clientes que estão aguardando ou em atendimento.
    fila = conexao.execute("""
        SELECT *
        FROM atendimentos

        WHERE status IN (
            'Aguardando',
            'Em Atendimento'
        )

        ORDER BY

            CASE
                WHEN status = 'Em Atendimento'
                THEN 0
                ELSE 1
            END,

            CASE
                WHEN prioridade = 'Preferencial'
                THEN 0
                ELSE 1
            END,

            id ASC
    """).fetchall()


    # Cliente atualmente em atendimento.
    atual = conexao.execute("""
        SELECT *
        FROM atendimentos
        WHERE status = 'Em Atendimento'
        ORDER BY chamado_em ASC
        LIMIT 1
    """).fetchone()


    # Histórico.
    historico = conexao.execute("""
        SELECT *
        FROM atendimentos

        WHERE status IN (
            'Concluído',
            'Cancelado'
        )

        ORDER BY id DESC
    """).fetchall()


    # Estatísticas.
    aguardando = conexao.execute("""
        SELECT COUNT(*)
        FROM atendimentos
        WHERE status = 'Aguardando'
    """).fetchone()[0]


    em_atendimento = conexao.execute("""
        SELECT COUNT(*)
        FROM atendimentos
        WHERE status = 'Em Atendimento'
    """).fetchone()[0]


    concluidos = conexao.execute("""
        SELECT COUNT(*)
        FROM atendimentos
        WHERE status = 'Concluído'
    """).fetchone()[0]


    cancelados = conexao.execute("""
        SELECT COUNT(*)
        FROM atendimentos
        WHERE status = 'Cancelado'
    """).fetchone()[0]


    conexao.close()


    return render_template_string(
        HTML,
        fila=fila,
        atual=atual,
        historico=historico,
        aguardando=aguardando,
        em_atendimento=em_atendimento,
        concluidos=concluidos,
        cancelados=cancelados
    )


# ============================================================
# CADASTRAR CLIENTE
# ============================================================

@app.route("/cadastrar", methods=["POST"])
def cadastrar():

    nome = request.form.get("nome", "").strip()
    prioridade = request.form.get("prioridade", "Normal")


    if not nome:

        flash(
            "Digite o nome do cliente.",
            "erro"
        )

        return redirect(url_for("index"))


    if prioridade not in [
        "Normal",
        "Preferencial"
    ]:

        prioridade = "Normal"


    conexao = conectar()


    conexao.execute("""
        INSERT INTO atendimentos
        (
            nome,
            prioridade,
            status,
            criado_em
        )

        VALUES (?, ?, ?, ?)
    """, (
        nome,
        prioridade,
        "Aguardando",
        datetime.now().strftime(
            "%d/%m/%Y %H:%M:%S"
        )
    ))


    conexao.commit()
    conexao.close()


    flash(
        f"Cliente {nome} adicionado à fila!",
        "sucesso"
    )


    return redirect(url_for("index"))


# ============================================================
# CHAMAR PRÓXIMO
# ============================================================

@app.route("/chamar")
def chamar():

    conexao = conectar()


    # Só permite um cliente em atendimento por vez.
    atual = conexao.execute("""
        SELECT *
        FROM atendimentos
        WHERE status = 'Em Atendimento'
        LIMIT 1
    """).fetchone()


    if atual:

        flash(
            f"Finalize o atendimento de {atual['nome']} antes de chamar outro cliente.",
            "erro"
        )

        conexao.close()

        return redirect(url_for("index"))


    # Busca o próximo cliente.
    #
    # Preferencial vem antes de Normal.
    # Dentro da mesma prioridade, o ID menor
    # significa que entrou primeiro.

    proximo = conexao.execute("""
        SELECT *
        FROM atendimentos

        WHERE status = 'Aguardando'

        ORDER BY

            CASE
                WHEN prioridade = 'Preferencial'
                THEN 0
                ELSE 1
            END,

            id ASC

        LIMIT 1
    """).fetchone()


    if not proximo:

        flash(
            "Não existem clientes aguardando.",
            "erro"
        )

        conexao.close()

        return redirect(url_for("index"))


    horario = datetime.now().strftime(
        "%d/%m/%Y %H:%M:%S"
    )


    conexao.execute("""
        UPDATE atendimentos

        SET
            status = 'Em Atendimento',
            chamado_em = ?

        WHERE id = ?
    """, (
        horario,
        proximo["id"]
    ))


    conexao.commit()
    conexao.close()


    flash(
        f"📢 Próximo cliente: {proximo['nome']}",
        "sucesso"
    )


    return redirect(url_for("index"))


# ============================================================
# CONCLUIR ATENDIMENTO
# ============================================================

@app.route("/concluir/<int:id>")
def concluir(id):

    conexao = conectar()


    cliente = conexao.execute("""
        SELECT *
        FROM atendimentos
        WHERE id = ?
    """, (id,)).fetchone()


    if not cliente:

        flash(
            "Cliente não encontrado.",
            "erro"
        )


    elif cliente["status"] != "Em Atendimento":

        flash(
            "Esse cliente não está em atendimento.",
            "erro"
        )


    else:

        horario = datetime.now().strftime(
            "%d/%m/%Y %H:%M:%S"
        )


        conexao.execute("""
            UPDATE atendimentos

            SET
                status = 'Concluído',
                finalizado_em = ?

            WHERE id = ?
        """, (
            horario,
            id
        ))


        conexao.commit()


        flash(
            f"Atendimento de {cliente['nome']} concluído!",
            "sucesso"
        )


    conexao.close()


    return redirect(url_for("index"))


# ============================================================
# CANCELAR ATENDIMENTO
# ============================================================

@app.route("/cancelar/<int:id>")
def cancelar(id):

    conexao = conectar()


    cliente = conexao.execute("""
        SELECT *
        FROM atendimentos
        WHERE id = ?
    """, (id,)).fetchone()


    if not cliente:

        flash(
            "Cliente não encontrado.",
            "erro"
        )


    elif cliente["status"] in [
        "Concluído",
        "Cancelado"
    ]:

        flash(
            "Esse atendimento já foi finalizado.",
            "erro"
        )


    else:

        horario = datetime.now().strftime(
            "%d/%m/%Y %H:%M:%S"
        )


        conexao.execute("""
            UPDATE atendimentos

            SET
                status = 'Cancelado',
                finalizado_em = ?

            WHERE id = ?
        """, (
            horario,
            id
        ))


        conexao.commit()


        flash(
            f"Atendimento de {cliente['nome']} cancelado.",
            "sucesso"
        )


    conexao.close()


    return redirect(url_for("index"))


# ============================================================
# INICIAR SISTEMA
# ============================================================

if __name__ == "__main__":

    criar_banco()

    print("")
    print("=" * 50)
    print(" SISTEMA DE FILA DE ATENDIMENTO")
    print("=" * 50)
    print(" Acesse: http://127.0.0.1:5000")
    print("=" * 50)
    print("")

    app.run(
        debug=True
    )
