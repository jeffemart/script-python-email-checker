# Usar uma imagem base do Python
FROM python:3.9-slim

# Definir o diretório de trabalho dentro do container
WORKDIR /app

# Copiar os arquivos requirements.txt e o script da API para o diretório de trabalho
COPY requirements.txt requirements.txt
COPY app.py app.py

# Instalar as dependências do Python
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Expor a porta que a API vai rodar (opcional, mas recomendado)
EXPOSE 5000

# Definir a variável de ambiente para desabilitar buffering de saída
ENV PYTHONUNBUFFERED=1

# Comando para rodar a API
CMD ["python", "app.py"]
