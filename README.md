
# Vid Automator API 🎬

![Badge Status](https://img.shields.io/badge/status-operacional-brightgreen)
![Badge License](https://img.shields.io/github/license/Jcnok/vid-automator-api?color=blue)
![Badge Last Commit](https://img.shields.io/github/last-commit/Jcnok/vid-automator-api?color=orange)

---

## 📖 Índice

1.  [**Sobre o Projeto**](#-1-sobre-o-projeto)
2.  [**Arquitetura e Filosofia de Design**](#-2-arquitetura-e-filosofia-de-design)
3.  [**Funcionalidades Principais**](#-3-funcionalidades-principais)
4.  [**🛠️ Tecnologias Utilizadas**](#-4-tecnologias-utilizadas)
5.  [**📁 Estrutura do Projeto**](#-5-estrutura-do-projeto)
6.  [**Endpoints da API**](#-6-endpoints-da-api)
    *   [Health Check (`GET /`)](#61-get---health-check)
    *   [Criação Completa de Vídeo (`POST /create-full-video-with-subtitles/`)](#62-post-create-full-video-with-subtitles---o-endpoint-principal)
7.  [**🚀 Como Executar Localmente**](#-7-como-executar-localmente)
8.  [**📄 Licença**](#-8-licença)
9.  [**👨‍💻 Desenvolvido por**](#-9-desenvolvido-por)

---

## 1. Sobre o Projeto

O **Vid Automator API** é um backend robusto e otimizado, construído para servir como o "cérebro" de um sistema de automação para criação de vídeos. Desenvolvido com **FastAPI** e orquestrado para interagir com o [**n8n.io**](https://n8n.io/), este serviço encapsula a complexa manipulação de mídia do **FFmpeg** em um único endpoint atômico e fácil de usar.

O objetivo principal deste projeto é demonstrar uma arquitetura de microsserviços desacoplada, onde tarefas pesadas (como transcodificação de vídeo, análise de áudio e renderização de legendas) são delegadas a um serviço especializado. O cliente (neste caso, um workflow n8n) apenas fornece os ativos de mídia via URL e upload, e a API orquestra todo o processo de produção, retornando um vídeo finalizado e pronto para distribuição.

Este projeto é uma peça central do meu portfólio, demonstrando habilidades em **Engenharia de Backend com Python, design de APIs, automação de processos, Docker e orquestração de tarefas assíncronas**.

[🔝 Voltar ao Índice](#-índice)

---

## 2. Arquitetura e Filosofia de Design

A API foi projetada com base nos seguintes princípios de engenharia:

-   **✅ Encapsulamento:** Toda a complexidade dos comandos e da lógica do FFmpeg é abstraída. O cliente não precisa saber como um vídeo é montado; ele apenas consome o serviço.
-   **✅ Atomicidade:** A criação do vídeo é tratada como uma única transação. O endpoint principal ou tem sucesso e retorna um vídeo completo, ou falha e retorna um erro claro, evitando resultados parciais.
-   **✅ Eficiência e Concorrência:** Utiliza **FastAPI** e **Uvicorn** para um ambiente ASGI de alta performance. Operações de I/O, como o download de múltiplos arquivos, são executadas de forma assíncrona usando `asyncio` e `aiohttp`.
-   **✅ Isolamento e Limpeza:** Cada requisição é processada em um diretório temporário isolado. Uma `BackgroundTask` do Starlette garante que este diretório seja completamente destruído após o processamento.
-   **✅ Robustez e Depuração:** O código inclui validação de entrada, tratamento de exceções e retorna códigos de status HTTP semânticos com mensagens detalhadas, facilitando a depuração no n8n.

[🔝 Voltar ao Índice](#-índice)

---

## 3. Funcionalidades Principais

-   **Orquestração Completa de Vídeo:** Executa um pipeline de 6 etapas em uma única chamada de API.
-   **Transições Profissionais:** Cria vídeos com transições *crossfade* suaves entre as imagens usando o filtro `xfade` do FFmpeg.
-   **Análise de Mídia Dinâmica:** Utiliza o `ffprobe` para determinar a duração exata do áudio e sincronizar perfeitamente o timing do slideshow visual.
-   **Renderização de Legendas ("Burn-in"):** Suporta o formato `.ass` (Advanced SubStation Alpha) e "queima" as legendas diretamente no vídeo.
-   **Arquitetura Híbrida de Ativos:** Otimizado para receber ativos pesados (áudio, imagens) via URL e ativos leves e dinâmicos (legendas) via upload de arquivo direto.

[🔝 Voltar ao Índice](#-índice)

---

## 4. 🛠️ Tecnologias Utilizadas

| Tecnologia      | Propósito                                      |
| --------------- | ---------------------------------------------- |
| **Python 3.9+** | Linguagem principal do backend.                |
| **FastAPI**     | Framework para a construção da API.            |
| **Uvicorn**     | Servidor ASGI de alta performance.             |
| **FFmpeg**      | Suíte para toda a manipulação de vídeo e áudio.|
| **aiohttp**     | Para downloads assíncronos de arquivos.        |
| **Docker**      | Para containerização e portabilidade.          |
| **n8n.io**      | Orquestrador do workflow de automação (cliente).|

[🔝 Voltar ao Índice](#-índice)

---

## 5. 📁 Estrutura do Projeto

A estrutura de pastas foi projetada para ser limpa, modular e intuitiva, separando claramente o código da aplicação dos arquivos de configuração e automação.

```

vid-automator-api/
├── app/
│ └── main.py # Código fonte principal da API FastAPI
├── n8n/
│ └── video_creation_workflow.json # Workflow exportável para o n8n
├── .gitignore # Arquivos e pastas ignorados pelo Git
├── Dockerfile # Define o ambiente do contêiner
├── LICENSE # Licença do projeto (MIT)
├── README.md # Esta documentação
└── requirements.txt # Dependências Python
```

[🔝 Voltar ao Índice](#-índice)

---

## 6. Endpoints da API

### 6.1. `GET /` - Health Check
- **Descrição:** Verifica se o serviço está online.
- **Resposta (200 OK):** `{ "message": "FFmpeg as a Service is online and ready." }`

### 6.2. `POST /create-full-video-with-subtitles/` - O Endpoint Principal
- **Descrição:** Orquestra todo o pipeline de criação de vídeo.
- **Requisição:** `multipart/form-data`
- **Parâmetros:**
    | Nome                | Tipo         | Obrigatório | Descrição                                                          |
    | ------------------- | ------------ | ----------- | ------------------------------------------------------------------ |
    | `image_urls_json`   | `string`     | Sim         | Uma string contendo um array JSON com as URLs das imagens.         |
    | `audio_url`         | `string`     | Sim         | A URL do arquivo de narração `.mp3`.                               |
    | `subtitle_file`     | `file`       | Sim         | O arquivo de legenda no formato `.ass`.                            |
    | `output_filename`   | `string`     | Não         | Nome do arquivo de vídeo de saída. Padrão: `final_video.mp4`.      |

- **Resposta (200 OK):** O corpo da resposta contém o binário do arquivo de vídeo final (`video/mp4`).

[🔝 Voltar ao Índice](#-índice)

---

## 7. 🚀 Como Executar Localmente

Para executar esta API em sua máquina local usando Docker, siga os passos abaixo:

1.  **Pré-requisitos:** Certifique-se de ter o [Docker](https://www.docker.com/get-started) instalado e em execução.

2.  **Clone o repositório:**
    ```bash
    git clone https://github.com/Jcnok/vid-automator-api.git
    ```

3.  **Navegue até o diretório do projeto:**
    ```bash
    cd vid-automator-api
    ```

4.  **Construa a imagem Docker:**
    ```bash
    docker build -t ffmpeg-service .
    ```

5.  **Execute o contêiner:**
    ```bash
    docker run -d -p 8000:7860 --name ffmpeg-api ffmpeg-service
    ```
    - `-p 8000:7860`: Mapeia a porta 8000 da sua máquina para a porta 7860 dentro do contêiner.

6.  **Teste a API:**
    - Abra seu navegador e acesse `http://localhost:8000`.
    - A documentação interativa (Swagger UI) estará disponível em `http://localhost:8000/docs`.

[🔝 Voltar ao Índice](#-índice)

---

## 8. 📄 Licença

Este projeto está sob a licença MIT. Veja o arquivo [LICENSE](./LICENSE) para mais detalhes.

[🔝 Voltar ao Índice](#-índice)

---

## 9. 👨‍💻 Desenvolvido por

<table>
  <tr>
    <td align="center">
      <a href="https://github.com/Jcnok">
        <img src="https://avatars.githubusercontent.com/u/61186265?v=4" width="100px;" alt="Foto de Julio Okuda no GitHub"/><br>
        <sub>
          <b>Julio Okuda</b>
        </sub>
      </a>
    </td>
  </tr>
</table>

**Vamos nos conectar!**
-   [![LinkedIn](https://img.shields.io/badge/LinkedIn-Julio%20Okuda-0077B5?style=for-the-badge&logo=linkedin)](https://www.linkedin.com/in/juliookuda/)
-   [![GitHub](https://img.shields.io/badge/GitHub-Jcnok-181717?style=for-the-badge&logo=github)](https://github.com/Jcnok)

[🔝 Voltar ao Índice](#-índice)