# TTKbot

Aplicação para upload de vídeos e publicação automática no TikTok, usando Celery para processamento assíncrono.

## Funcionalidades

- Upload de vídeos pela interface web
- Listagem e visualização de vídeos enviados
- Publicação no TikTok imediatamente após o upload ou em uma data/hora agendada
- Acompanhamento de status: rascunho, agendado, enviando, publicado, erro

## Requisitos

- Python 3.10+
- Redis usado como broker do Celery
- Conta de desenvolvedor no [TikTok for Developers](https://developers.tiktok.com/) com acesso ao `video.publish`

## Instalação

1. Clone o repositório e entre na pasta do projeto.

2. Crie e ative um ambiente virtual:

   ```
   python -m venv venv
   venv\Scripts\activate      # Windows
   source venv/bin/activate   # Linux/Mac
   ```

3. Instale as dependências:

   ```
   pip install -r requirements.txt
   ```

4. Copie o arquivo de variáveis de ambiente de exemplo e preencha os valores:

   ```
   copy .env.example .env      # Windows
   cp .env.example .env        # Linux/Mac
   ```

   Variáveis principais:

   | Variável | Descrição |
   |---|---|
   | `SECRET_KEY` | chave secreta do Django |
   | `TIKTOK_ACCESS_TOKEN` | token OAuth do criador, obtido junto ao TikTok |
   | `TIKTOK_PRIVACY_LEVEL` | `SELF_ONLY` até o app ser auditado pela TikTok |
   | `CELERY_BROKER_URL` | endereço do Redis, ex: `redis://localhost:6379/0` |

5. Aplique as migrations do banco de dados:

   ```
   python manage.py migrate
   ```

6. Crie um superusuário (opcional, para acessar o admin):

   ```
   python manage.py createsuperuser
   ```

## Rodando o projeto

O projeto precisa de **três processos rodando ao mesmo tempo**, em terminais separados:

**1. Redis** (se não estiver rodando como serviço do sistema):

```
docker run -p 6379:6379 redis
```

**2. Worker do Celery** (responsável por processar e publicar os vídeos):

```
celery -A meu_projeto worker -l info
```

**3. Servidor do Django:**

```
python manage.py runserver
```

Depois disso, acesse **http://127.0.0.1:8000/** no navegador.

## Como usar

1. Na tela inicial, clique em **"Enviar vídeo"**.
2. Preencha título, descrição e selecione o arquivo de vídeo.
3. No campo **"Agendar publicação para"**:
   - deixe em branco para publicar assim que o upload terminar;
   - ou escolha uma data/hora futura para agendar a publicação.
4. Clique em **"Enviar vídeo"**.
5. Na listagem, o status do vídeo é atualizado automaticamente conforme o Celery processa a publicação:
   - **Rascunho / Agendado** → aguardando o horário de envio
   - **Enviando** → upload em andamento para o TikTok
   - **Publicado** → já está no ar (ou visível apenas para você, se o app ainda não foi auditado)
   - **Erro** → veja o campo de erro no admin do Django para detalhes

## Observações importantes

- Enquanto o app não passar pela auditoria da TikTok, todo vídeo é publicado como **privado** (`SELF_ONLY`), visível só na conta autenticada.
- O `TIKTOK_ACCESS_TOKEN` expira periodicamente — é necessário renová-lo via fluxo OAuth do criador.
- Sem o worker do Celery rodando, os vídeos ficam presos em "agendado"/"enviando" e nunca são publicados.

## Estrutura do projeto
```text
meu_projeto/
├── manage.py
├── requirements.txt
├── .env
├── .gitignore
│
├── meu_projeto/
│   ├── __init__.py
│   ├── settings.py
│   ├── urls.py
│   ├── celery.py
│   ├── wsgi.py
│   └── asgi.py
│
│
├── static/
│
├── videos/
│   ├── __init__.py
│   ├── migrations/
│   ├── templates/
│   │   ├── base.html
│   │   └── videos/
│   │       ├── lista.html
│   │       ├── upload.html
│   │       └── detalhe.html
│   ├── models.py
│   ├── forms.py
│   ├── views.py
│   ├── urls.py
│   ├── tasks.py
│   ├── admin.py
│   └── tests.py
│
└── media/
    └── videos/
