
DEBUG = True

TEMPLATE_DEBUG = True

TEMPLATE_STRING_IF_INVALID = "INVALID EXPRESSION: %s"

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'kikar_hamedina',
        'USER': 'admin',
        'PASSWORD': '123456',
        'HOST': 'localhost'
    }
}
