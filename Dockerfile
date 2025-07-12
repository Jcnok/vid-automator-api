FROM python:3.9-slim-bullseye

# --- ETAPA 1: Instalar FFmpeg e dependências ---
# A imagem Bullseye já contém uma versão do FFmpeg que inclui o filtro 'xfade'.
# A instalação se torna muito mais simples e direta.
RUN apt-get update && \
    apt-get install -y ffmpeg && \
    rm -rf /var/lib/apt/lists/*


# Define o diretório de trabalho dentro do contêiner
WORKDIR /app

# Copia todos os arquivos do diretório atual para o diretório de trabalho do contêiner
COPY . .

# Instala as dependências Python
RUN pip install --no-cache-dir -r requirements.txt

# Expõe a porta que o FastAPI vai usar
EXPOSE 7860

# Comando para iniciar a aplicação.
# A notação "app.main:app" instrui o Uvicorn a procurar:
# no pacote 'app', o módulo 'main.py', e dentro dele, a variável 'app'.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "7860"]