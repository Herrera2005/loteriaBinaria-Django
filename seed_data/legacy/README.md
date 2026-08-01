# Datos legado no importables automáticamente

Los JSON del frontend antiguo permanecen dentro del ZIP de respaldo. No se
cargan desde Django ni desde JavaScript porque contienen reglas antiguas,
credenciales demo, floats y estados que no son autoridad del Taller #3.

El seed activo es `python manage.py seed_baseline`. `seed_demo` es opcional,
local, exige `DEBUG=True` y una contraseña suministrada mediante `.env`.
