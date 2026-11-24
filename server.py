#!/usr/bin/env python3
"""Santo Bigode: local Python server + transactional SQLite persistence. Python 3.10+."""
from __future__ import annotations

import argparse
import auth
from urllib.parse import urlsplit
from datetime import date, datetime, timedelta, timezone
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import secrets
import sqlite3
import threading
import time
import webbrowser

ROOT = Path(__file__).resolve().parent
STATIC = ROOT / 'web'
TOKEN = secrets.token_urlsafe(32)
DB = ROOT / 'data' / 'santo_bigode.sqlite3'
BOOKING_LOCK = threading.Lock()
BOOKING_ATTEMPTS = {}


class Invalid(ValueError):
    pass


class Conflict(ValueError):
    pass


def today():
    return datetime.now(timezone(timedelta(hours=-3))).date()


def checked(condition, message):
    if not condition:
        raise Invalid(message)


def integer(value, low=0, high=100_000_000):
    return type(value) is int and low <= value <= high


def text(value, size=300, nonempty=True):
    return isinstance(value, str) and len(value) <= size and (bool(value.strip()) or not nonempty)


def day(value):
    checked(isinstance(value, str), 'Data inválida.')
    try:
        parsed = date.fromisoformat(value)
    except ValueError:
        raise Invalid('Data inválida.') from None
    checked(parsed.isoformat() == value, 'Use uma data AAAA-MM-DD.')
    return parsed


def minutes(value):
    checked(isinstance(value, str) and len(value) == 5 and value[2] == ':', 'Horário inválido.')
    try:
        h, m = map(int, value.split(':'))
    except ValueError:
        raise Invalid('Horário inválido.') from None
    checked(0 <= h < 24 and 0 <= m < 60, 'Horário inválido.')
    return h * 60 + m


def rows(state, key):
    value = state.get(key)
    checked(isinstance(value, list) and len(value) <= 30000, f'Lista inválida: {key}.')
    checked(all(isinstance(x, dict) for x in value), f'Registro inválido: {key}.')
    ids = [x.get('id') for x in value]
    if key != 'blocks':
        checked(all(text(x, 100) for x in ids) and len(set(ids)) == len(ids), f'IDs inválidos: {key}.')
    return value


def validate(state):
    checked(isinstance(state, dict) and state.get('schema') == 1, 'Backup ou estado incompatível.')
    expected = {'schema', 'demo', 'settings', 'barbers', 'services', 'appointments', 'expenses', 'products', 'movements', 'blocks'}
    checked(set(state) == expected, 'Estrutura de dados inválida.')
    settings = state.get('settings')
    checked(isinstance(settings, dict) and text(settings.get('name'), 80), 'Nome da barbearia inválido.')
    whatsapp = settings.get('whatsapp', '')
    checked(isinstance(whatsapp, str) and (not whatsapp or whatsapp.isdigit() and 10 <= len(whatsapp) <= 15), 'WhatsApp inválido.')
    opening, closing = minutes(settings.get('open')), minutes(settings.get('close'))
    checked(opening < closing, 'O encerramento precisa ser depois da abertura.')
    barbers = rows(state, 'barbers')
    checked(len(barbers) == 3 and all(text(x.get('name'), 80) for x in barbers), 'Preencha os três barbeiros.')
    barber_ids = {x['id'] for x in barbers}
    services = rows(state, 'services')
    checked({x['id'] for x in services} == {'cut', 'beard', 'combo', 'visage', 'custom'}, 'Serviços inválidos.')
    for s in services:
        checked(text(s.get('name'), 100) and integer(s.get('price')) and integer(s.get('cost')) and integer(s.get('duration'), 1, 480), 'Serviço inválido.')
        checked(s.get('hair') in (0, 1) and s.get('beard') in (0, 1), 'Tipo de serviço inválido.')
    checked(next(x for x in services if x['id'] == 'visage')['price'] == 10000, 'Visagismo deve custar R$ 100.')
    for p in rows(state, 'products'):
        checked(text(p.get('name'), 100) and text(p.get('category'), 50) and text(p.get('unit'), 20), 'Produto inválido.')
        checked(all(integer(p.get(k)) for k in ('quantity', 'min', 'cost', 'sale')), 'Quantidade ou valor inválido no estoque.')
    occupied = {}
    for a in rows(state, 'appointments'):
        day(a.get('date'))
        start = minutes(a.get('time'))
        checked(text(a.get('client'), 100) and text(a.get('phone', ''), 30, False) and text(a.get('service'), 300) and text(a.get('notes', ''), 500, False), 'Dados do agendamento inválidos.')
        checked(a.get('barberId') in barber_ids and a.get('serviceId') in {x['id'] for x in services}, 'Barbeiro ou serviço não encontrado.')
        checked(a.get('status') in ('scheduled', 'completed', 'cancelled'), 'Status inválido.')
        checked(all(integer(a.get(k)) for k in ('price', 'cost', 'hair', 'beard')) and integer(a.get('duration'), 1, 480), 'Valores ou duração inválidos.')
        checked(start + a['duration'] <= 1440, 'Atendimento ultrapassa o fim do dia.')
        checked(a['status'] != 'completed' or day(a['date']) <= today(), 'Não é possível concluir atendimento futuro.')
        if a['status'] != 'cancelled':
            intervals = occupied.setdefault((a['date'], a['barberId']), [])
            intervals.append((start, start + a['duration']))
    for intervals in occupied.values():
        intervals.sort()
        checked(all(intervals[i][0] >= intervals[i - 1][1] for i in range(1, len(intervals))), 'Existem horários sobrepostos para um barbeiro.')
    for e in rows(state, 'expenses'):
        day(e.get('date'))
        checked(text(e.get('name'), 150) and integer(e.get('amount'), 1), 'Despesa inválida.')
    for m in rows(state, 'movements'):
        checked(m.get('kind') in ('in', 'out') and integer(m.get('quantity'), 1) and text(m.get('reason'), 150), 'Movimentação inválida.')
    for b in rows(state, 'blocks'):
        day(b.get('date'))
        checked(type(b.get('all', False)) is bool, 'Pausa inválida.')
        if not b.get('all'):
            checked(integer(b.get('start'), 0, 1439) and integer(b.get('end'), 1, 1440) and b['start'] < b['end'], 'Período de pausa inválido.')


def seed():
    value = json.loads((ROOT / 'demo_seed.json').read_text(encoding='utf-8'))
    old_start = min(date.fromisoformat(a['date']) for a in value['appointments'])
    new_start = today() - timedelta(days=today().weekday())
    delta = new_start - old_start
    for a in value['appointments']:
        a['date'] = (date.fromisoformat(a['date']) + delta).isoformat()
        a['status'] = 'completed' if a['date'] < today().isoformat() or a['date'] == today().isoformat() and minutes(a['time']) < 720 else 'scheduled'
    for e in value['expenses']:
        e['date'] = (date.fromisoformat(e['date']) + delta).isoformat()
    return value


def connect():
    db = sqlite3.connect(DB, timeout=10)
    db.execute('PRAGMA journal_mode=WAL')
    return db


def initialize():
    DB.parent.mkdir(parents=True, exist_ok=True)
    with connect() as db:
        db.execute('CREATE TABLE IF NOT EXISTS app_state (id INTEGER PRIMARY KEY CHECK(id=1), data TEXT NOT NULL, revision INTEGER NOT NULL)')
        db.execute('CREATE TABLE IF NOT EXISTS history (revision INTEGER PRIMARY KEY, data TEXT NOT NULL, saved_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP)')
        if not db.execute('SELECT 1 FROM app_state').fetchone():
            value = seed()
            validate(value)
            db.execute('INSERT INTO app_state VALUES (1, ?, 1)', (json.dumps(value, ensure_ascii=False),))


    auth.initialize(connect)


def read_state():
    with connect() as db:
        value, revision = db.execute('SELECT data, revision FROM app_state WHERE id=1').fetchone()
    return {'state': json.loads(value), 'revision': revision}


def save_state(state, revision):
    validate(state)
    checked(integer(revision, 1), 'Versão de dados inválida.')
    with connect() as db:
        db.execute('BEGIN IMMEDIATE')
        old, current = db.execute('SELECT data, revision FROM app_state WHERE id=1').fetchone()
        if revision != current:
            raise Conflict('Os dados mudaram em outra janela. Eles foram recarregados; confira e tente novamente.')
        db.execute('INSERT OR REPLACE INTO history(revision,data) VALUES (?,?)', (current, old))
        db.execute('UPDATE app_state SET data=?,revision=? WHERE id=1', (json.dumps(state, ensure_ascii=False), current + 1))
        db.execute('DELETE FROM history WHERE revision NOT IN (SELECT revision FROM history ORDER BY revision DESC LIMIT 20)')
    return {'revision': current + 1}


def public_projection(state):
    now = today().isoformat()
    return {
        'schema': 1,
        'settings': {key: state['settings'][key] for key in ('name', 'whatsapp', 'open', 'close')},
        'barbers': [{key: b.get(key, '') for key in ('id', 'name', 'role')} for b in state['barbers']],
        'services': [{key: s[key] for key in ('id', 'name', 'price', 'duration', 'hair', 'beard')} for s in state['services']],
        'appointments': [dict(id=f'occupied-{i}', date=a['date'], time=a['time'], duration=a['duration'], barberId=a['barberId'], status='scheduled') for i, a in enumerate(state['appointments']) if a['date'] >= now and a['date'] <= (today() + timedelta(days=90)).isoformat() and a['status'] != 'cancelled'],
        'blocks': [b for b in state['blocks'] if b['date'] >= now],
        'expenses': [], 'products': [], 'movements': []
    }


def create_booking(state, values):
    service = next((s for s in state['services'] if s['id'] == values.get('serviceId')), None)
    checked(service is not None and any(b['id'] == values.get('barberId') for b in state['barbers']), 'Escolha o serviço e o barbeiro.')
    checked(text(values.get('client'), 100) and len(values['client'].strip()) >= 2, 'Informe o nome do cliente.')
    checked(text(values.get('phone', ''), 30, False) and text(values.get('notes', ''), 300, False), 'Telefone ou observações inválidos.')
    booking_date = day(values.get('date'))
    checked(today() <= booking_date <= today() + timedelta(days=90), 'Escolha uma data nos próximos 90 dias.')
    start = minutes(values.get('time'))
    extra = values.get('visage') is True and service['id'] != 'visage'
    duration = service['duration'] + (60 if extra else 0)
    end = start + duration
    opening, closing = minutes(state['settings']['open']), minutes(state['settings']['close'])
    checked(start >= opening and end <= closing and (start - opening) % 30 == 0, 'Horário não disponível.')
    now = datetime.now(timezone(timedelta(hours=-3)))
    checked(booking_date != today() or start > now.hour * 60 + now.minute, 'Escolha um horário futuro.')
    checked(not any(b['date'] == values['date'] and (b.get('all') or start < b['end'] and end > b['start']) for b in state['blocks']), 'O horário está bloqueado.')
    checked(not any(a['date'] == values['date'] and a['barberId'] == values['barberId'] and a['status'] != 'cancelled' and start < minutes(a['time']) + a['duration'] and end > minutes(a['time']) for a in state['appointments']), 'Esse horário acabou de ser ocupado. Escolha outro.')
    return dict(id=secrets.token_hex(16), client=values['client'].strip(), phone=values.get('phone', '').strip(), notes=values.get('notes', '').strip(), date=values['date'], time=values['time'], barberId=values['barberId'], serviceId=service['id'], service=service['name'] + (' + visagismo' if extra else ''), duration=duration, price=service['price'] + (10000 if extra else 0), cost=service['cost'] + (next(s['cost'] for s in state['services'] if s['id'] == 'visage') if extra else 0), hair=service['hair'], beard=service['beard'], status='scheduled', visage=extra, source='client')


class Handler(SimpleHTTPRequestHandler):
    extensions_map = {**SimpleHTTPRequestHandler.extensions_map, '.mjs': 'text/javascript', '.js': 'text/javascript', '.wasm': 'application/wasm', '.task': 'application/octet-stream', '.bin': 'application/octet-stream'}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(STATIC), **kwargs)

    def end_headers(self):
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.send_header('Referrer-Policy', 'same-origin')
        self.send_header('Cache-Control', 'no-store' if self.path.startswith('/api/') or self.path in ('/', '/index.html') else 'public,max-age=3600')
        self.send_header('Permissions-Policy', 'camera=(self), microphone=()')
        super().end_headers()

    def json_response(self, value, status=200):
        body = json.dumps(value, ensure_ascii=False).encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def valid_host(self):
        host = self.headers.get('Host', '').split(':')[0]
        return host in ('localhost', '127.0.0.1')

    def is_admin(self):
        return auth.authenticated(connect, self.headers.get('Cookie'))

    def do_GET(self):
        if not self.valid_host():
            return self.json_response({'error': 'Este servidor aceita apenas acesso local.'}, 403)
        if self.path == '/api/auth/session':
            user = auth.principal(connect, self.headers.get('Cookie'))
            return self.json_response({'admin': bool(user), 'canManageTeam': bool(user and user['owner']), 'displayName': user['name'] if user else '', 'configured': auth.configured(connect), 'mode': 'python', 'csrf': TOKEN})
        if self.path == '/api/team/access':
            user = auth.principal(connect, self.headers.get('Cookie'))
            if not user or not user['owner']:
                return self.json_response({'error': 'Somente o responsável pode gerenciar acessos.'}, 403)
            return self.json_response(auth.list_team(connect))
        if self.path == '/api/public':
            return self.json_response({'state': public_projection(read_state()['state'])})
        if self.path == '/api/state':
            if not self.is_admin():
                return self.json_response({'error': 'Acesso exclusivo da administração.'}, 401)
            return self.json_response(read_state())
        if self.path.startswith('/api/'):
            return self.json_response({'error': 'Não encontrado.'}, 404)
        if self.path in ('/', '/index.html'):
            body = (STATIC / 'index.html').read_bytes()
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.send_header('Content-Length', str(len(body)))
            self.end_headers()
            return self.wfile.write(body)
        return super().do_GET()

    def list_directory(self, path):
        self.send_error(404)
        return None

    def mutation(self):
        if not self.valid_host() or not secrets.compare_digest(self.headers.get('X-CSRF-Token', ''), TOKEN) or self.headers.get('X-SB-Request') != '1':
            self.json_response({'error': 'Atualize a página antes de salvar.'}, 403)
            return
        if self.headers.get('Origin') and self.headers['Origin'] != 'http://' + self.headers.get('Host'):
            self.json_response({'error': 'Origem não autorizada.'}, 403)
            return
        if self.headers.get('Content-Type', '').split(';')[0] != 'application/json':
            self.json_response({'error': 'Envie JSON.'}, 415)
            return
        try:
            length = int(self.headers.get('Content-Length', '0'))
            checked(0 < length <= 8_000_000, 'Use um arquivo de até 8 MB.')
            payload = json.loads(self.rfile.read(length))
            checked(isinstance(payload, dict), 'Solicitação inválida.')
            if self.path == '/api/auth/setup' and self.command == 'POST':
                auth.setup(connect, payload.get('username'), payload.get('password'), payload.get('setupToken'))
                token = auth.login(connect, payload.get('username'), payload.get('password'), self.client_address[0])
                return self.auth_response(token)
            if self.path == '/api/auth/login' and self.command == 'POST':
                token = auth.login(connect, payload.get('username'), payload.get('password'), self.client_address[0])
                return self.auth_response(token)
            if self.path == '/api/auth/logout' and self.command == 'POST':
                auth.logout(connect, self.headers.get('Cookie'))
                return self.auth_response('', logout=True)
            if self.path in ('/api/team/access', '/api/team/access/revoke') and self.command == 'POST':
                user = auth.principal(connect, self.headers.get('Cookie'))
                if not user or not user['owner']:
                    return self.json_response({'error': 'Somente o responsável pode gerenciar acessos.'}, 403)
                if self.path.endswith('/revoke'):
                    auth.revoke_member(connect, payload.get('email', ''))
                else:
                    auth.save_member(connect, payload, read_state()['state']['barbers'])
                return self.json_response({'ok': True})
            if self.path == '/api/bookings' and self.command == 'POST':
                with BOOKING_LOCK:
                    ip = self.client_address[0]
                    now = time.time()
                    n, reset = BOOKING_ATTEMPTS.get(ip, (0, now + 600))
                    if now > reset:
                        n, reset = 0, now + 600
                    if n >= 10:
                        return self.json_response({'error': 'Muitas tentativas. Aguarde alguns minutos.'}, 429)
                    BOOKING_ATTEMPTS[ip] = (n + 1, reset)
                    current = read_state()
                    item = create_booking(current['state'], payload)
                    current['state']['appointments'].append(item)
                    save_state(current['state'], current['revision'])
                return self.json_response({'booking': {key: item[key] for key in ('client','service','date','time','price','duration')}, 'state': public_projection(current['state'])}, 201)
            if self.path != '/api/state' or self.command != 'PUT':
                return self.json_response({'error': 'Não encontrado.'}, 404)
            if not self.is_admin():
                return self.json_response({'error': 'Acesso exclusivo da administração.'}, 401)
            result = save_state(payload.get('state'), payload.get('revision'))
        except Conflict as exc:
            return self.json_response({'error': str(exc)}, 409)
        except (ValueError, TypeError, KeyError, AttributeError, StopIteration) as exc:
            message = str(exc) if isinstance(exc, (Invalid, ValueError)) else 'Dados inválidos. Confira os campos.'
            return self.json_response({'error': message}, 400)
        except sqlite3.Error:
            return self.json_response({'error': 'Não foi possível salvar no banco. Confira a pasta de dados.'}, 500)
        self.json_response(result)

    def auth_response(self, token, logout=False):
        body = b'{"ok":true}'
        self.send_response(200)
        self.send_header('Set-Cookie', f'sb_admin={token}; HttpOnly; SameSite=Strict; Path=/; Max-Age={0 if logout else 28800}')
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_PUT(self):
        return self.mutation()

    def do_POST(self):
        return self.mutation()

    def log_message(self, fmt, *args):
        # Avoid client names and request bodies in console logs.
        pass


def main():
    parser = argparse.ArgumentParser(description='Santo Bigode · Gestão local da barbearia')
    parser.add_argument('--port', type=int, default=8765)
    parser.add_argument('--no-browser', action='store_true')
    args = parser.parse_args()
    initialize()
    try:
        server = ThreadingHTTPServer(('127.0.0.1', args.port), Handler)
    except OSError:
        print(f'A porta {args.port} está em uso. Feche a outra versão ou use --port 8766.')
        return 1
    url = f'http://127.0.0.1:{args.port}'
    first = not auth.configured(connect)
    initial = url + '/#admin?setup=' + auth.SETUP_TOKEN if first else url
    if first:
        print('Primeiro acesso administrativo (defina usuário e senha): ' + initial)
    print(f'\nSANTO BIGODE\nAbra: {url}\nMantenha esta janela aberta. Ctrl+C para encerrar.\n')
    if not args.no_browser:
        threading.Timer(.5, lambda: webbrowser.open(initial)).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print('\nSanto Bigode encerrado. Seus dados foram preservados.')
    finally:
        server.server_close()
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
