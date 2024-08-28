from flask import Flask, request, jsonify
import re
import dns.resolver
import smtplib
import socket
import os

app = Flask(__name__)

# Token de autenticação (em um ambiente de produção, isso deve ser armazenado de forma segura)
AUTH_TOKEN = os.getenv("AUTH_TOKEN", "VGF2yTPS0N0ivdJXBIWUhC4mihgnmUuY")

def validar_email(email):
    padrao = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
    return re.match(padrao, email) is not None

def verificar_registros_mx(dominio):
    try:
        registros_mx = dns.resolver.resolve(dominio, 'MX')
        mx_records = [(rdata.exchange.to_text(), rdata.preference) for rdata in registros_mx]
        return mx_records
    except Exception as e:
        app.logger.error(f"Erro ao verificar registros MX para {dominio}: {e}")
        return None

def verificar_servidor_email(mx_records, email):
    from_address = 'test@example.com'
    domain = email.split('@')[1]

    for mx_record in mx_records:
        mx_host = mx_record[0]
        try:
            server = smtplib.SMTP(mx_host, timeout=10)
            server.set_debuglevel(0)
            server.helo()
            server.mail(from_address)
            code, message = server.rcpt(email)
            server.quit()
            if code == 250:
                return True, f"Diálogo com {mx_host} conseguiu\nResposta do servidor: {message.decode()}"
            else:
                return False, f"Diálogo com {mx_host} falhou\nResposta do servidor: {message.decode()}"
        except (smtplib.SMTPConnectError, smtplib.SMTPServerDisconnected, smtplib.SMTPResponseException, socket.error) as e:
            app.logger.warning(f"Falha ao conectar ao servidor {mx_host}: {e}")
            continue
    return False, "Falha ao conectar a todos os servidores MX."

@app.route('/validate_email', methods=['GET'])
def validate_email():
    # Obtém o token e o e-mail dos parâmetros de query
    token = request.args.get('access_key')
    email = request.args.get('email')

    # Verifica o token de autenticação
    if token != AUTH_TOKEN:
        return jsonify({"error": "Unauthorized"}), 401

    if not email:
        return jsonify({"error": "Email is required"}), 400

    pontuacao = 0
    detalhes = []

    # Verifica a sintaxe do e-mail
    if validar_email(email):
        pontuacao += 1
        detalhes.append("A sintaxe do endereço de e-mail está correta.")
    else:
        return jsonify({"error": "Invalid email syntax"}), 400
    
    dominio = email.split('@')[1]
    mx_records = verificar_registros_mx(dominio)
    
    if mx_records:
        pontuacao += 1
        detalhes.extend([f"Registro MX encontrado: {record[0]} (Prioridade {record[1]})" for record in mx_records])
        server_valid, server_response = verificar_servidor_email(mx_records, email)
        if server_valid:
            pontuacao += 1
        detalhes.append(server_response)
    else:
        return jsonify({"error": "No MX records found"}), 400

    # Calcula a pontuação em porcentagem e formata a saída
    porcentagem = (pontuacao / 3) * 100
    score_formatted = f"Score {porcentagem:.2f}"

    return jsonify({
        "message": "Email validation completed",
        "details": detalhes,
        "score": score_formatted
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)