import sqlite3
import datetime
from flask import Flask, render_template, jsonify, request, redirect, url_for, flash
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps

app = Flask(__name__)
app.config['SECRET_KEY'] = 'tu-clave-sereta-muy-dificil'
DATABASE = 'InventarioBD_2.db'

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Por favor, inicia sesión para acceder.'

class User(UserMixin):
    """Modelo de Usuario para Flask-Login"""
    def __init__(self, id, nombre, rol):
        self.id = id
        self.nombre = nombre
        self.rol = rol

    @staticmethod
    def get(user_id):
        conn = get_db_connection()
        user_row = conn.execute('SELECT * FROM usuarios WHERE id = ?', (user_id,)).fetchone()
        conn.close()
        if user_row:
            return User(id=user_row['id'], nombre=user_row['nombre'], rol=user_row['rol'])
        return None

@login_manager.user_loader
def load_user(user_id):
    """Carga el usuario desde la BD para la sesión."""
    return User.get(user_id)

def role_required(*roles):
    """Decorador para restringir acceso basado en roles."""
    def wrapper(fn):
        @wraps(fn)
        def decorated_view(*args, **kwargs):
            if not current_user.is_authenticated:
                return login_manager.unauthorized()
            if current_user.rol not in roles:
                flash('No tienes permiso para acceder a esta página.', 'danger')
                return redirect(url_for('inicio'))
            return fn(*args, **kwargs)
        return decorated_view
    return wrapper

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


@app.route('/', methods=['GET', 'POST'])
def login():
    """Renderiza la vista 'Login'."""
    if current_user.is_authenticated:
        return redirect(url_for('inicio'))
    
    if request.method == 'POST':
        nombre = request.form['nombre']
        password = request.form['password']
        
        conn = get_db_connection()
        user_row = conn.execute('SELECT * FROM usuarios WHERE nombre = ?', (nombre,)).fetchone()
        conn.close()
        
        if user_row and check_password_hash(user_row['password'], password):
            user = User(id=user_row['id'], nombre=user_row['nombre'], rol=user_row['rol'])
            login_user(user)
            return redirect(url_for('inicio'))
        else:
            flash('Usuario o contraseña incorrectos.', 'danger')
            
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/inicio')
@login_required
def inicio():
    """Renderiza la vista 'Inicio' (Dashboard)."""
    return render_template('inicio.html', active_page='inicio')

@app.route('/productos')
@login_required
def productos():
    """Renderiza la vista 'Productos'."""
    return render_template('productos.html', active_page='productos')

@app.route('/almacenes')
@login_required
def almacenes():
    """Renderiza la vista 'Almacenes'."""
    return render_template('almacenes.html', active_page='almacenes')

@app.route('/admin')
@login_required
@role_required('admin')
def admin_panel():
    """Renderiza la vista de 'Admin' para crear usuarios."""
    return render_template('admin.html', active_page='admin')


@app.route('/api/usuarios', methods=['POST'])
@login_required
@role_required('admin')
def add_usuario():
    """Agrega un nuevo usuario (solo Admin)."""
    data = request.json
    nombre = data['nombre']
    password = data['password']
    rol = data['rol']

    if not nombre or not password or not rol:
        return jsonify({'success': False, 'error': 'Faltan datos.'}), 400

    hashed_password = generate_password_hash(password)
    
    conn = get_db_connection()
    try:
        conn.execute('INSERT INTO usuarios (nombre, password, rol) VALUES (?, ?, ?)',
                     (nombre, hashed_password, rol))
        conn.commit()
        return jsonify({'success': True}), 201
    except sqlite3.IntegrityError:
        conn.close()
        return jsonify({'success': False, 'error': 'El nombre de usuario ya existe.'}), 409
    finally:
        conn.close()



@app.route('/api/productos', methods=['GET'])
@login_required
def get_productos():
    conn = get_db_connection()
    productos = conn.execute('SELECT * FROM productos').fetchall()
    conn.close()
    return jsonify([dict(ix) for ix in productos])

@app.route('/api/productos', methods=['POST'])
@login_required
@role_required('admin', 'productos')
def add_producto():
    data = request.json
    fecha_mod = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    usuario_mod = current_user.nombre
    
    conn = get_db_connection()
    conn.execute(
        'INSERT INTO productos (nombre, precio, cantidad, departamento, almacen, fecha_modificacion, usuario_modificacion) VALUES (?, ?, ?, ?, ?, ?, ?)',
        (data['nombre'], data['precio'], data['cantidad'], data['departamento'], data['almacen'], fecha_mod, usuario_mod)
    )
    conn.commit()
    conn.close()
    return jsonify({'success': True}), 201

@app.route('/api/productos/<int:id>', methods=['PUT'])
@login_required
@role_required('admin', 'productos')
def update_producto(id):
    data = request.json
    fecha_mod = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    usuario_mod = current_user.nombre
    
    conn = get_db_connection()
    conn.execute(
        'UPDATE productos SET nombre = ?, precio = ?, cantidad = ?, departamento = ?, almacen = ?, fecha_modificacion = ?, usuario_modificacion = ? WHERE id = ?',
        (data['nombre'], data['precio'], data['cantidad'], data['departamento'], data['almacen'], fecha_mod, usuario_mod, id)
    )
    conn.commit()
    conn.close()
    return jsonify({'success': True})

@app.route('/api/productos/<int:id>', methods=['DELETE'])
@login_required
@role_required('admin', 'productos')
def delete_producto(id):
    conn = get_db_connection()
    conn.execute('DELETE FROM productos WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    return jsonify({'success': True})


@app.route('/api/almacenes', methods=['GET'])
@login_required
def get_almacenes():
    conn = get_db_connection()
    almacenes = conn.execute('SELECT * FROM almacenes').fetchall()
    conn.close()
    return jsonify([dict(ix) for ix in almacenes])

@app.route('/api/almacenes', methods=['POST'])
@login_required
@role_required('admin', 'almacenes')
def add_almacen():
    data = request.json
    fecha_mod = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    usuario_mod = current_user.nombre

    conn = get_db_connection()
    conn.execute(
        'INSERT INTO almacenes (nombre, fecha_modificacion, usuario_modificacion) VALUES (?, ?, ?)',
        (data['nombre'], fecha_mod, usuario_mod)
    )
    conn.commit()
    conn.close()
    return jsonify({'success': True}), 201

@app.route('/api/almacenes/<int:id>', methods=['PUT'])
@login_required
@role_required('admin', 'almacenes')
def update_almacen(id):
    data = request.json
    fecha_mod = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    usuario_mod = current_user.nombre

    conn = get_db_connection()
    conn.execute(
        'UPDATE almacenes SET nombre = ?, fecha_modificacion = ?, usuario_modificacion = ? WHERE id = ?',
        (data['nombre'], fecha_mod, usuario_mod, id)
    )
    conn.commit()
    conn.close()
    return jsonify({'success': True})

@app.route('/api/almacenes/<int:id>', methods=['DELETE'])
@login_required
@role_required('admin', 'almacenes')
def delete_almacen(id):
    conn = get_db_connection()
    try:
        conn.execute('PRAGMA foreign_keys = ON')
        conn.execute('DELETE FROM almacenes WHERE id = ?', (id,))
        conn.commit()
        return jsonify({'success': True})
    except sqlite3.IntegrityError:
        return jsonify({'success': False, 'error': 'No se puede eliminar. El almacén está siendo usado por uno o más productos.'}), 400
    finally:
        conn.close()

if __name__ == '__main__':
    app.run(debug=True)