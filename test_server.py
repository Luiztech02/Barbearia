import copy
from pathlib import Path
import tempfile
import unittest
import server
import threading
import urllib.request
import urllib.error
import re
import http.cookiejar
import json


class CoreTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.old_db = server.DB
        server.DB = Path(self.tmp.name) / 'test.sqlite3'
        server.initialize()
        self.state = server.read_state()['state']

    def tearDown(self):
        server.DB = self.old_db
        self.tmp.cleanup()

    def test_seed_valid_and_three_barbers(self):
        server.validate(self.state)
        self.assertEqual(len(self.state['barbers']), 3)

    def test_negative_stock_rejected(self):
        self.state['products'][0]['quantity'] = -1
        with self.assertRaises(server.Invalid):
            server.save_state(self.state, 1)
        self.assertGreaterEqual(server.read_state()['state']['products'][0]['quantity'], 0)

    def test_overlap_rejected_but_other_barber_allowed(self):
        original = self.state['appointments'][0]
        extra = copy.deepcopy(original)
        extra['id'] = 'new-conflict'
        self.state['appointments'].append(extra)
        with self.assertRaises(server.Invalid):
            server.validate(self.state)
        extra['status'] = 'cancelled'
        server.validate(self.state)

    def test_update_conflict_and_backup(self):
        self.state['settings']['name'] = 'Meu Santo Bigode'
        result = server.save_state(self.state, 1)
        self.assertEqual(result['revision'], 2)
        self.assertEqual(server.read_state()['state']['settings']['name'], 'Meu Santo Bigode')
        with self.assertRaises(server.Conflict):
            server.save_state(self.state, 1)
        with server.connect() as db:
            self.assertEqual(db.execute('SELECT count(*) FROM history').fetchone()[0], 1)

    def test_visage_price_fixed(self):
        next(s for s in self.state['services'] if s['id'] == 'visage')['price'] = 9900
        with self.assertRaises(server.Invalid):
            server.validate(self.state)

    def test_invalid_dates_and_duplicate_ids(self):
        self.state['appointments'][0]['date'] = '2026-02-31'
        with self.assertRaises(server.Invalid):
            server.validate(self.state)

    def test_incomplete_restore_rejected(self):
        with self.assertRaises(server.Invalid):
            server.validate({'schema': 1})

    def test_local_team_can_login_and_revoke_immediately(self):
        server.auth.setup(server.connect, 'responsavel', 'Senha-responsavel-123', server.auth.SETUP_TOKEN)
        owner_token = server.auth.login(server.connect, 'responsavel', 'Senha-responsavel-123', 'owner-test')
        self.assertTrue(server.auth.principal(server.connect, 'sb_admin=' + owner_token)['owner'])
        member = dict(name='Barbeiro teste', email='barber@example.test', barberId='rafael', password='Senha-barbeiro-123')
        server.auth.save_member(server.connect, member, self.state['barbers'])
        token = server.auth.login(server.connect, 'barber@example.test', 'Senha-barbeiro-123', 'member-test')
        cookie = 'sb_admin=' + token
        self.assertTrue(server.auth.authenticated(server.connect, cookie))
        self.assertFalse(server.auth.principal(server.connect, cookie)['owner'])
        self.assertNotIn('password_hash', server.auth.list_team(server.connect)['members'][0])
        server.auth.revoke_member(server.connect, member['email'])
        self.assertFalse(server.auth.authenticated(server.connect, cookie))
        server.auth.save_member(server.connect, {**member, 'password': ''}, self.state['barbers'])
        self.assertFalse(server.auth.authenticated(server.connect, cookie))
        fresh = server.auth.login(server.connect, member['email'], 'Senha-barbeiro-123', 'member-test')
        self.assertTrue(server.auth.authenticated(server.connect, 'sb_admin=' + fresh))
        with self.assertRaises(ValueError):
            server.auth.revoke_member(server.connect, 'responsavel')

    def test_public_and_admin_are_separated(self):
        public = server.public_projection(self.state)
        self.assertEqual(public['expenses'], [])
        self.assertEqual(public['products'], [])
        self.assertTrue(all('cost' not in s for s in public['services']))
        self.assertTrue(all('client' not in a and 'phone' not in a and 'notes' not in a and 'price' not in a for a in public['appointments']))

    def test_public_booking_ignores_tampered_price(self):
        target = server.today() + server.timedelta(days=10)
        values = dict(client='Cliente teste', date=target.isoformat(), time='10:00', barberId='rafael', serviceId='cut', visage=True, price=1, cost=0, status='completed')
        item = server.create_booking(self.state, values)
        self.assertEqual(item['price'], 14000)
        self.assertEqual(item['duration'], 100)
        self.assertEqual(item['status'], 'scheduled')
        self.state['appointments'].append(item)
        with self.assertRaises(server.Invalid):
            server.create_booking(self.state, values)

    def test_http_auth_csrf_state_and_logout(self):
        http = server.ThreadingHTTPServer(('127.0.0.1', 0), server.Handler)
        worker = threading.Thread(target=http.serve_forever, daemon=True)
        worker.start()
        url = f'http://127.0.0.1:{http.server_port}'
        jar = __import__('http.cookiejar', fromlist=['CookieJar']).CookieJar()
        client = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
        try:
            def get(path):
                with client.open(url + path) as r:
                    return json.load(r)
            def send(path, data, csrf=server.TOKEN, method='POST'):
                return client.open(urllib.request.Request(url + path, data=json.dumps(data).encode(), method=method, headers={'Content-Type':'application/json', 'X-CSRF-Token':csrf, 'X-SB-Request':'1', 'Origin':url}))
            self.assertFalse(get('/api/auth/session')['admin'])
            self.assertFalse(get('/api/auth/session')['configured'])
            self.assertEqual(get('/api/public')['state']['products'], [])
            with self.assertRaises(urllib.error.HTTPError) as denied:
                get('/api/state')
            self.assertEqual(denied.exception.code, 401)
            with self.assertRaises(urllib.error.HTTPError) as denied_write:
                send('/api/state', {'state':self.state,'revision':1}, method='PUT')
            self.assertEqual(denied_write.exception.code, 401)
            with self.assertRaises(urllib.error.HTTPError) as bad_setup:
                send('/api/auth/setup', {'username':'teste','password':'Senha-temporaria-123','setupToken':'errado'})
            self.assertEqual(bad_setup.exception.code, 400)
            with send('/api/auth/setup', {'username':'teste','password':'Senha-temporaria-123','setupToken':server.auth.SETUP_TOKEN}):
                pass
            self.assertTrue(get('/api/auth/session')['admin'])
            state=get('/api/state')
            state['state']['settings']['name']='Teste HTTP'
            with self.assertRaises(urllib.error.HTTPError) as csrf:
                send('/api/state',state,csrf='errado',method='PUT')
            self.assertEqual(csrf.exception.code, 403)
            with send('/api/state',state,method='PUT') as r:
                self.assertEqual(json.load(r)['revision'],2)
            with self.assertRaises(urllib.error.HTTPError) as conflict:
                send('/api/state',state,method='PUT')
            self.assertEqual(conflict.exception.code,409)
            with send('/api/auth/logout',{}):
                pass
            self.assertFalse(get('/api/auth/session')['admin'])
            with self.assertRaises(urllib.error.HTTPError):
                get('/api/state')
            with self.assertRaises(urllib.error.HTTPError):
                send('/api/auth/login',{'username':'teste','password':'senha-errada'})
            with send('/api/auth/login',{'username':'teste','password':'Senha-temporaria-123'}):
                pass
            self.assertTrue(get('/api/auth/session')['admin'])
        finally:
            http.shutdown()
            http.server_close()
            worker.join()


if __name__ == '__main__':
    unittest.main()
