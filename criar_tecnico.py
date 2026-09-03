from database import conectar, criar_tabelas

criar_tabelas()

nome = input("Nome do técnico: ").strip()
email = input("E-mail do técnico: ").strip().lower()
senha = input("Senha: ")

if not nome or not email or not senha:
    raise SystemExit("Todos os campos são obrigatórios.")

conn = conectar()
try:
    conn.execute("INSERT INTO usuarios (nome, email, senha, tipo) VALUES (?, ?, ?, 'tecnico')", (nome, email, senha))
    conn.commit()
    print("Técnico criado com sucesso.")
except Exception as e:
    print(f"Não foi possível criar o técnico: {e}")
finally:
    conn.close()
