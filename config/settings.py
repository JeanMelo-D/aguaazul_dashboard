# settings.py

import os
from pathlib import Path
from decouple import config
import dj_database_url


# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# ==============================================================================
# CONFIGURAÇÕES DE SEGURANÇA PARA PRODUÇÃO
# ==============================================================================

# Carrega a chave secreta a partir das variáveis de ambiente. NUNCA deixe a chave no código.
SECRET_KEY = config('SECRET_KEY')

# DEBUG deve ser False em produção para não expor informações sensíveis.
# O config('DEBUG', default=False, cast=bool) permite ligá-lo em desenvolvimento com um .env

DEBUG = config('DEBUG', default=False, cast=bool)
# DEBUG = config('DEBUG', default=False, cast=bool)

# Adiciona os domínios que podem acessar sua aplicação.
ALLOWED_HOSTS = [
    'pindoramadashboard-hsfgc7ajhaaxcwgv.brazilsouth-01.azurewebsites.net',
    'https://fazaguaazul.com',
    "https://www.fazaguaazul.com",
    'fazaguaazul.com',# Adicione seu domínio customizado se tiver
    '127.0.0.1',
    'localhost',
]

# ==============================================================================
# APLICAÇÕES E MIDDLEWARE
# ==============================================================================

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # Apps de viadagem
    'tailwind',
    'ninetail',
    'whitenoise', # Adicionado para servir arquivos estáticos de forma otimizada
    'corsheaders', # Recomendado para APIs
    # meus apps
    'pipeline',
    'data',
    'maps',
    # 'django_browser_reload', # REMOVIDO: Ferramenta apenas para desenvolvimento.
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware', # Middleware do django-cors-headers
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'
WSGI_APPLICATION = 'config.wsgi.application'

# ==============================================================================
# TEMPLATES E TAILWIND
# ==============================================================================

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
        'context_processors': [
        'django.template.context_processors.debug',  # LINHA CORRIGIDA
        'django.template.context_processors.request',
        'django.contrib.auth.context_processors.auth',
        'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

TAILWIND_APP_NAME = 'ninetail'

# ✅ REMOVIDO: NPM_BIN_PATH não é necessário e causaria erro no Azure (Linux).
# A biblioteca django-tailwind encontrará o npm automaticamente no ambiente de build.

# ==============================================================================
# BANCO DE DADOS
# ==============================================================================

# ✅ CONFIGURAÇÃO DE BANCO DE DADOS PRONTA PARA PRODUÇÃO
# Em produção, usará a variável de ambiente DATABASE_URL.
# Em desenvolvimento, se não encontrar a variável, usará o SQLite.
DATABASES = {
    'default': dj_database_url.config(
        default=f"sqlite:///{BASE_DIR / 'db.sqlite3'}"
    )
}

# ==============================================================================
# INTERNACIONALIZAÇÃO E VALIDAÇÃO DE SENHA
# ==============================================================================

LANGUAGE_CODE = 'pt-br'
TIME_ZONE = 'America/Sao_Paulo' # Ajustado para um fuso horário mais comum no Brasil
USE_I18N = True
USE_TZ = True

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# ==============================================================================
# ARQUIVOS ESTÁTICOS (CONFIGURAÇÃO DE PRODUÇÃO COM WHITENOISE)
# ==============================================================================

# URL para acessar os arquivos estáticos no navegador.
STATIC_URL = '/static/'

# Diretórios onde o Django procura por arquivos estáticos (além das pastas 'static' dos apps).
STATICFILES_DIRS = [
    BASE_DIR / 'ninetail/static'
]

# # Pasta de destino para onde o `collectstatic` irá copiar todos os arquivos.
# STATIC_ROOT = BASE_DIR / 'staticfiles'  ## DESCOMENTAR SOMENTE EM PRODUÇÃO

STATIC_ROOT = BASE_DIR / 'staticfiles'

# Mecanismo de armazenamento para o WhiteNoise, que comprime e versiona os arquivos.
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# ==============================================================================
# CONFIGURAÇÃO DE CORS (RECOMENDADO PARA APIs)
# ==============================================================================

# Adicione aqui os domínios do seu front-end se ele for servido separadamente no futuro.
CORS_ALLOWED_ORIGINS = [
    "https://pindoramadashboard-hsfgc7ajhaaxcwgv.brazilsouth-01.azurewebsites.net",
    "http://localhost:8000",
    "http://127.0.0.1:8000",
]

# ==============================================================================
# CONFIGURAÇÕES GERAIS
# ==============================================================================

# NPM_BIN_PATH = r"C:\Program Files\nodejs\npm.cmd" ## COMENTAR PARA PRODUÇÃO

# config/settings.py

LOGIN_REDIRECT_URL = 'home'
LOGIN_URL = 'login'



DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'