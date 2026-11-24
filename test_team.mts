import assert from 'node:assert/strict';
import {DatabaseSync} from 'node:sqlite';
import {readFileSync,readdirSync} from 'node:fs';
import {handleBarberAPI} from './lib/barber-api.ts';
import {bookingLink,PUBLIC_BOOKING_URL} from './web/team-ui.js';

const sql=new DatabaseSync(':memory:');for(const name of readdirSync('drizzle').filter(x=>x.endsWith('.sql')).sort())sql.exec(readFileSync('drizzle/'+name,'utf8'));
function statement(query:string,params:any[]=[]):any{return {bind:(...p:any[])=>statement(query,p),first:async()=>sql.prepare(query).get(...params)||null,all:async()=>({results:sql.prepare(query).all(...params)}),run:async()=>{const r=sql.prepare(query).run(...params);return {meta:{changes:Number(r.changes)}}}}}
const DB:any={prepare:statement,batch:async(items:any[])=>{sql.exec('BEGIN');try{const rows=[];for(const item of items)rows.push(await item.run());sql.exec('COMMIT');return rows}catch(e){sql.exec('ROLLBACK');throw e}}};
const env={DB,ADMIN_OWNER_EMAIL:'owner@example.test'};
const req=(path:string,email='',method='GET',body?:any)=>new Request('https://barber.test'+path,{method,headers:{...(email?{'oai-authenticated-user-email':email}:{}),...(body?{'Content-Type':'application/json','Origin':'https://barber.test','X-SB-Request':'1'}:{})},body:body?JSON.stringify(body):undefined});
async function call(path:string,email='',method='GET',body?:any){const r=await handleBarberAPI(req(path,email,method,body),env);return {status:r.status,body:await r.json() as any}}
assert.equal((await call('/api/state')).status,401);
assert.equal((await call('/api/state','barber@example.test')).status,401);
assert.equal((await call('/api/team/access')).status,403);
const member={name:'Barbeiro de teste',email:'Barber@Example.Test',barberId:'rafael'};
assert.equal((await call('/api/team/access','owner@example.test','POST',member)).status,200);
let auth=await call('/api/auth/session','barber@example.test');assert.equal(auth.body.admin,true);assert.equal(auth.body.canManageTeam,false);
assert.equal((await call('/api/state','barber@example.test')).status,200);
assert.equal((await call('/api/team/access','barber@example.test')).status,403);
assert.equal((await call('/api/team/access','barber@example.test','POST',{...member,email:'other@example.test'})).status,403);
let roster=await call('/api/team/access','owner@example.test');assert.equal(roster.body.members.length,1);assert.equal(roster.body.members[0].email,'barber@example.test');
assert.equal((await call('/api/team/access/revoke','owner@example.test','POST',{email:'barber@example.test'})).status,200);
assert.equal((await call('/api/state','barber@example.test')).status,401);
assert.equal((await call('/api/auth/session','barber@example.test')).body.admin,false);
assert.equal((await call('/api/team/access','owner@example.test','POST',member)).status,200);
assert.equal((await call('/api/state','barber@example.test')).status,200);
assert.equal((await call('/api/team/access/revoke','owner@example.test','POST',{email:'owner@example.test'})).status,400);
assert.equal((await call('/api/team/access','owner@example.test','POST',{...member,email:'invalido'})).status,400);
const publicState=(await call('/api/public')).body.state;assert.equal(publicState.products.length,0);assert.equal(publicState.expenses.length,0);assert(publicState.services.every((s:any)=>s.cost===undefined));
(globalThis as any).location={hostname:'localhost',origin:'http://127.0.0.1:8765'};const link=bookingLink('rafael');assert(link.startsWith(PUBLIC_BOOKING_URL));assert.equal(new URL(link).searchParams.get('barbeiro'),'rafael');assert.equal(new URL(link).hash,'#agendar');assert(!link.includes('127.0.0.1'));
console.log('Cadastro, login autorizado, bloqueio de visitante, administração completa, revogação, reativação e links públicos: OK.');sql.close();
