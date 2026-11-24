"""Local administration credentials; no default password, no browser-stored secrets."""
import hashlib
from http.cookies import SimpleCookie
import secrets
import time
import threading
import re

SETUP_TOKEN = secrets.token_urlsafe(32)
LOCK = threading.Lock()
ATTEMPTS = {}


def initialize(connect):
    with connect() as db:
        db.execute('CREATE TABLE IF NOT EXISTS admin_user (id INTEGER PRIMARY KEY CHECK(id=1), username TEXT NOT NULL, salt TEXT NOT NULL, password_hash TEXT NOT NULL)')
        db.execute('CREATE TABLE IF NOT EXISTS admin_session (token_hash TEXT PRIMARY KEY, expires REAL NOT NULL)')
        if 'username' not in {r[1] for r in db.execute('PRAGMA table_info(admin_session)')}:
            db.execute('ALTER TABLE admin_session ADD COLUMN username TEXT')
        db.execute('CREATE TABLE IF NOT EXISTS team_user (email TEXT PRIMARY KEY, name TEXT NOT NULL, barber_id TEXT, salt TEXT NOT NULL, password_hash TEXT NOT NULL, enabled INTEGER NOT NULL DEFAULT 1)')


def configured(connect):
    with connect() as db:
        return bool(db.execute('SELECT 1 FROM admin_user WHERE id=1').fetchone())


def password_hash(password, salt):
    return hashlib.pbkdf2_hmac('sha256', password.encode(), bytes.fromhex(salt), 310000).hex()


def setup(connect, username, password, token):
    if not isinstance(token, str) or not secrets.compare_digest(token, SETUP_TOKEN):
        raise ValueError('Abra o link de primeiro acesso exibido na janela do Python.')
    if not isinstance(username, str) or not 3 <= len(username.strip()) <= 80:
        raise ValueError('Informe um usuário com 3 a 80 caracteres.')
    if not isinstance(password, str) or not 10 <= len(password) <= 200:
        raise ValueError('Use uma senha com pelo menos 10 caracteres.')
    salt = secrets.token_hex(16)
    with connect() as db:
        db.execute('BEGIN IMMEDIATE')
        if db.execute('SELECT 1 FROM admin_user').fetchone():
            raise ValueError('A administração já foi configurada. Entre com sua senha.')
        db.execute('INSERT INTO admin_user VALUES(1,?,?,?)', (username.strip().lower(), salt, password_hash(password, salt)))


def login(connect, username, password, ip):
    if not isinstance(username, str) or not isinstance(password, str) or len(password) > 200:
        raise ValueError('Usuário ou senha inválidos.')
    now = time.time()
    with LOCK:
        attempts, reset = ATTEMPTS.get(ip, (0, now + 600))
        if now > reset:
            attempts, reset = 0, now + 600
        if attempts >= 5:
            raise ValueError('Muitas tentativas. Aguarde 10 minutos para tentar novamente.')
        ATTEMPTS[ip] = (attempts + 1, reset)
    with connect() as db:
        owner = db.execute('SELECT username,salt,password_hash FROM admin_user WHERE id=1').fetchone()
        identity = username.strip().lower()
        user = owner if owner and owner[0] == identity else db.execute('SELECT email,salt,password_hash FROM team_user WHERE email=? AND enabled=1', (identity,)).fetchone()
    salt = user[1] if user else '0' * 32
    digest = password_hash(password, salt)
    if not user or not secrets.compare_digest(user[2], digest) or not secrets.compare_digest(user[0], username.strip().lower()):
        raise ValueError('Usuário ou senha inválidos.')
    with LOCK:
        ATTEMPTS.pop(ip, None)
    token = secrets.token_urlsafe(32)
    with connect() as db:
        db.execute('DELETE FROM admin_session WHERE expires < ?', (now,))
        db.execute('INSERT INTO admin_session(token_hash,expires,username) VALUES(?,?,?)', (hashlib.sha256(token.encode()).hexdigest(), now + 28800, user[0]))
    return token


def get_token(cookie):
    try:
        c = SimpleCookie()
        c.load(cookie or '')
        return c['sb_admin'].value if 'sb_admin' in c else ''
    except Exception:
        return ''


def authenticated(connect, cookie):
    return principal(connect, cookie) is not None


def principal(connect, cookie):
    token = get_token(cookie)
    if not token:
        return None
    with connect() as db:
        session = db.execute('SELECT username FROM admin_session WHERE token_hash=? AND expires>?', (hashlib.sha256(token.encode()).hexdigest(), time.time())).fetchone()
        if not session:
            return None
        owner = db.execute('SELECT username FROM admin_user WHERE id=1').fetchone()
        if owner and (session[0] is None or session[0] == owner[0]):
            return {'email': owner[0], 'name': 'Responsável pela barbearia', 'owner': True}
        member = db.execute('SELECT email,name FROM team_user WHERE email=? AND enabled=1', (session[0],)).fetchone()
        return {'email': member[0], 'name': member[1], 'owner': False} if member else None


def list_team(connect):
    with connect() as db:
        owner = db.execute('SELECT username FROM admin_user WHERE id=1').fetchone()
        members = db.execute('SELECT email,name,barber_id,enabled FROM team_user ORDER BY name,email').fetchall()
    return {'owner': owner[0] if owner else '', 'members': [dict(email=m[0], name=m[1], barberId=m[2], enabled=m[3]) for m in members]}


def save_member(connect, values, barbers):
    email = values.get('email', '').strip().lower()
    name = values.get('name', '').strip()
    barber_id = values.get('barberId') or None
    password = values.get('password', '')
    if len(email) > 254 or not re.fullmatch(r'\S+@[^\s@.]+(?:\.[^\s@.]+)+', email):
        raise ValueError('Informe um e-mail válido.')
    if not name or len(name) > 100:
        raise ValueError('Informe um nome de até 100 caracteres.')
    if barber_id and not any(b['id'] == barber_id for b in barbers):
        raise ValueError('Selecione um profissional válido.')
    with connect() as db:
        owner = db.execute('SELECT username FROM admin_user WHERE id=1').fetchone()
        if owner and email == owner[0]:
            raise ValueError('O responsável já tem acesso permanente.')
        prior = db.execute('SELECT salt,password_hash FROM team_user WHERE email=?', (email,)).fetchone()
        if password:
            if not isinstance(password, str) or not 10 <= len(password) <= 200:
                raise ValueError('Use uma senha local com pelo menos 10 caracteres.')
            salt = secrets.token_hex(16)
            digest = password_hash(password, salt)
        elif prior:
            salt, digest = prior
        else:
            raise ValueError('Defina uma senha local de pelo menos 10 caracteres para o novo usuário.')
        if password and prior:
            db.execute('DELETE FROM admin_session WHERE username=?', (email,))
        db.execute('INSERT INTO team_user(email,name,barber_id,salt,password_hash,enabled) VALUES(?,?,?,?,?,1) ON CONFLICT(email) DO UPDATE SET name=excluded.name,barber_id=excluded.barber_id,salt=excluded.salt,password_hash=excluded.password_hash,enabled=1', (email, name, barber_id, salt, digest))


def revoke_member(connect, email):
    with connect() as db:
        owner = db.execute('SELECT username FROM admin_user WHERE id=1').fetchone()
        if owner and email.strip().lower() == owner[0]:
            raise ValueError('O acesso do responsável não pode ser removido.')
        db.execute('UPDATE team_user SET enabled=0 WHERE email=?', (email.strip().lower(),))
        db.execute('DELETE FROM admin_session WHERE username=?', (email.strip().lower(),))


def logout(connect, cookie):
    token = get_token(cookie)
    if token:
        with connect() as db:
            db.execute('DELETE FROM admin_session WHERE token_hash=?', (hashlib.sha256(token.encode()).hexdigest(),))
