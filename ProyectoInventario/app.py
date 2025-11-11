import sqlite3
from flask import Flask, render_template, jsonify, request

# --- Configuración de la Aplicación Flask ---
app = Flask(__name__)
DATABASE = 'InventarioBD_2.db' # La BD debe estar en la misma carpeta que app.py

# --- Funciones de Base de Datos ---

def get_db_connection():
    """Crea una conexión a la base de datos."""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row  # Permite acceder a las columnas por nombre
    return conn

# --- Rutas de las "Vistas" (Páginas) ---
# Flask buscará automáticamente los archivos HTML en la carpeta "templates".

@app.route('/')
def inicio():
    """Renderiza la vista 'Inicio'."""
    # render_template busca 'inicio.html' en la carpeta 'templates'
    return render_template('inicio.html', active_page='inicio')

@app.route('/productos')
def productos():
    """Renderiza la vista 'Productos'."""
    return render_template('productos.html', active_page='productos')

@app.route('/almacenes')
def almacenes():
    """Renderiza la vista 'Almacenes'."""
    return render_template('almacenes.html', active_page='almacenes')

# --- API Endpoints (Para CRUD con JavaScript) ---
# Esta lógica de API no cambia en absoluto.

# --- API: PRODUCTOS ---

@app.route('/api/productos', methods=['GET'])
def get_productos():
    """Obtiene todos los productos de la BD."""
    conn = get_db_connection()
    productos = conn.execute('SELECT * FROM productos').fetchall()
    conn.close()
    return jsonify([dict(ix) for ix in productos])

@app.route('/api/productos', methods=['POST'])
def add_producto():
    """Agrega un nuevo producto a la BD."""
    data = request.json
    conn = get_db_connection()
    conn.execute('INSERT INTO productos (nombre, precio, cantidad, departamento, almacen) VALUES (?, ?, ?, ?, ?)',
                 (data['nombre'], data['precio'], data['cantidad'], data['departamento'], data['almacen']))
    conn.commit()
    conn.close()
    return jsonify({'success': True}), 201

@app.route('/api/productos/<int:id>', methods=['PUT'])
def update_producto(id):
    """Modifica un producto existente en la BD."""
    data = request.json
    conn = get_db_connection()
    conn.execute('UPDATE productos SET nombre = ?, precio = ?, cantidad = ?, departamento = ?, almacen = ? WHERE id = ?',
                 (data['nombre'], data['precio'], data['cantidad'], data['departamento'], data['almacen'], id))
    conn.commit()
    conn.close()
    return jsonify({'success': True})

@app.route('/api/productos/<int:id>', methods=['DELETE'])
def delete_producto(id):
    """Elimina un producto de la BD."""
    conn = get_db_connection()
    conn.execute('DELETE FROM productos WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    return jsonify({'success': True})

# --- API: ALMACENES ---

@app.route('/api/almacenes', methods=['GET'])
def get_almacenes():
    """Obtiene todos los almacenes de la BD."""
    conn = get_db_connection()
    almacenes = conn.execute('SELECT * FROM almacenes').fetchall()
    conn.close()
    return jsonify([dict(ix) for ix in almacenes])

@app.route('/api/almacenes', methods=['POST'])
def add_almacen():
    """Agrega un nuevo almacén a la BD."""
    data = request.json
    conn = get_db_connection()
    conn.execute('INSERT INTO almacenes (nombre) VALUES (?)', (data['nombre'],))
    conn.commit()
    conn.close()
    return jsonify({'success': True}), 201

@app.route('/api/almacenes/<int:id>', methods=['PUT'])
def update_almacen(id):
    """Modifica un almacén existente en la BD."""
    data = request.json
    conn = get_db_connection()
    conn.execute('UPDATE almacenes SET nombre = ? WHERE id = ?', (data['nombre'], id))
    conn.commit()
    conn.close()
    return jsonify({'success': True})

@app.route('/api/almacenes/<int:id>', methods=['DELETE'])
def delete_almacen(id):
    """Elimina un almacén de la BD."""
    conn = get_db_connection()
    try:
        conn.execute('PRAGMA foreign_keys = ON')
        conn.execute('DELETE FROM almacenes WHERE id = ?', (id,))
        conn.commit()
        return jsonify({'success': True})
    except sqlite3.IntegrityError as e:
        return jsonify({'success': False, 'error': 'No se puede eliminar. El almacén está siendo usado por uno o más productos.'}), 400
    finally:
        conn.close()


# --- Iniciar la aplicación ---
if __name__ == '__main__':
    app.run(debug=True)