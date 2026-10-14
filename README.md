# Mini Biblioteca

Aplicación pequeña en Flask (Python + HTML) para practicar pruebas de API con Postman y JMeter.

## Cómo ejecutarla

```bash
python -m venv venv
source venv/bin/activate        # En Windows: venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

Abre `http://127.0.0.1:5000` en el navegador. La API queda en `http://127.0.0.1:5000/api`.

## Usuarios de prueba

| Usuario | Contraseña | Rol |
|---|---|---|
| admin | admin123 | administrador |
| estudiante | clase2026 | lector |

## Endpoints

| Método | Ruta | Requiere token | Descripción |
|---|---|---|---|
| GET | `/api/salud` | No | Estado del servicio |
| POST | `/api/login` | No | Devuelve un token. Cuerpo: `{"usuario": "...", "password": "..."}` |
| GET | `/api/libros` | No | Lista de libros. Filtro opcional: `?q=texto` |
| GET | `/api/libros/<id>` | No | Un libro por id |
| POST | `/api/libros` | Sí | Crea un libro. Cuerpo: `{"titulo": "...", "autor": "...", "anio": 2000}` |
| PUT | `/api/libros/<id>` | Sí | Actualiza campos de un libro |
| DELETE | `/api/libros/<id>` | Sí | Elimina un libro |
| GET | `/api/reporte` | No | Reporte de totales (consulta más pesada) |
| POST | `/api/reset` | No | Restaura los datos iniciales |

Para las rutas que requieren token, envía el encabezado:

```
Authorization: Bearer <token>
```

## Códigos de respuesta esperados

- `200` consulta o actualización correcta
- `201` recurso creado
- `400` datos inválidos
- `401` falta el token o es inválido
- `404` el recurso no existe

## Tu misión

La documentación describe cómo *debería* comportarse la API. Tu trabajo es comprobar si realmente lo hace.
Anota cada diferencia que encuentres: qué enviaste, qué esperabas y qué recibiste.

Antes de repetir una prueba, puedes restaurar los datos con `POST /api/reset`.
