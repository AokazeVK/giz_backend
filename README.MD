GIZ - SSEC

Requisitos del Sistema
    Python 3.9+
    pip (gestor de paquetes de Python)
    PostgreSQL (o la base de datos que estés usando)
    git (para clonar el repositorio)

Configuración del Entorno de Desarrollo
1. Clonar el repositorio:
    git clone https://github.com/AokazeVK/giz_backend
    cd giz_backend

2. Crear y activar el entorno virtual:
Es una buena práctica para aislar las dependencias del proyecto.
    python -m venv venv
# En Windows
    .\venv\Scripts\activate
# En macOS/Linux
    source venv/bin/activate

3. Instalar dependencias: Usa el archivo requirements.txt que ya tienes para instalar todas las librerías necesarias.
    pip install -r requirements.txt

4. Configurar las variables de entorno: Crea un archivo .env en la raíz de tu proyecto y añade las siguientes variables, rellenando con tus datos.

# .env
    SECRET_KEY=<TU_CLAVE_SECRETA_DE_DJANGO>
    DEBUG=True

# Configuración de la base de datos de PostgreSQL
    DATABASE_NAME=<NOMBRE_DE_BASE_DE_DATOS>
    DATABASE_USER=<NOMBRE_DE_USUARIO>
    DATABASE_PASSWORD=<TU_CONTRASEÑA>
    DATABASE_HOST=<HOST_DE_TU_BASE_DE_DATOS>
    DATABASE_PORT=<PUERTO_DE_TU_BASE_DE_DATOS>

# URL donde se guardarán los archivos multimedia
    MEDIA_ROOT_PATH=/TU/RUTA/


5. Ejecutar migraciones de la base de datos:
    python manage.py makemigrations
    python manage.py migrate

6. Poblar la base de datos (seeding): Usa el comando que creamos para generar el superusuario y los permisos.
    python manage.py seed_all

7. Iniciar el servidor:
    python manage.py runserver

Endpoints de la API
Aquí están los endpoints principales de la API

Autenticación (/api/accounts/)

    POST /login/ - Iniciar sesión

    POST /logout/ - Cerrar sesión

    POST /refresh/ - Renovar token de acceso

    GET /logs/ - Ver historial de acciones (solo para administradores)

    GET /permissions/tree/ - Obtener árbol de permisos

    GET /profile/ - Ver perfil del usuario logeado

    GET /public/ - Endpoint de prueba público

Gestión de Usuarios (/api/accounts/users/)

    GET / - Listar todos los usuarios

    POST / - Crear un nuevo usuario

    GET /{id}/ - Obtener detalles de un usuario

    PUT /{id}/ - Actualizar un usuario completamente

    PATCH /{id}/ - Actualizar un usuario parcialmente

    POST /{id}/cambiar-contrasena/ - Cambiar contraseña del usuario

    POST /{id}/toggle-status/ - Activar/desactivar un usuario

Gestión de Roles (/api/accounts/roles/)

    GET / - Listar todos los roles

    POST / - Crear un nuevo rol

    GET /{id}/ - Obtener detalles de un rol

    PUT /{id}/ - Actualizar un rol completamente

    PATCH /{id}/ - Actualizar un rol parcialmente

    GET /{id}/permissions/ - Listar los permisos de un rol

    POST /{id}/permissions/ - Actualizar los permisos de un rol

Gestión de Ministerios (/api/difusion/ministerios/)

    GET / - Listar todos los ministerios

    POST / - Crear un nuevo ministerio

    GET /{id}/ - Obtener detalles de un ministerio

    PUT /{id}/ - Actualizar un ministerio completamente

    PATCH /{id}/ - Actualizar un ministerio parcialmente

    GET /{id}/encargados/ - Obtener todos los encargados de este ministerio

    POST /{id}/toggle_estado/ - Activar/desactivar un ministerio

Gestión de Encargados (/api/difusion/encargados/)

    GET / - Listar todos los encargados

    POST / - Crear un nuevo encargado

    GET /{id}/ - Obtener detalles de un encargado

    PUT /{id}/ - Actualizar un encargado completamente

    PATCH /{id}/ - Actualizar un encargado parcialmente

    POST /{id}/toggle_estado/ - Activar/desactivar un encargado