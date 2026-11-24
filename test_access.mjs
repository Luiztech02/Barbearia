import assert from 'node:assert/strict';
import {publicProjection,freshState,createBooking,validateFull,brazilNow} from './web/domain.js';
import {recommendReferences} from './web/references.js';
import {addDays,report,monday} from './web/store.js';
import {existsSync} from 'node:fs';
const state=freshState();validateFull(state);
const p=publicProjection(state);
assert(p.services.every(s=>!('cost' in s)));
assert(p.appointments.every(a=>!('client' in a)&&!('phone' in a)&&!('notes' in a)&&!('price' in a)&&!('cost' in a)));
assert.deepEqual(p.products,[]);assert.deepEqual(p.expenses,[]);
const values={client:'Cliente de teste',date:addDays(brazilNow().date,10),time:'10:00',barberId:state.barbers[0].id,serviceId:'cut',visage:true,price:1,cost:0,status:'completed'};
const a=createBooking(state,values);assert.equal(a.price,14000);assert.equal(a.duration,100);assert.equal(a.status,'scheduled');
state.appointments.push(a);assert.throws(()=>createBooking(state,values));
for(const shape of ['oval','round','square','long','heart'])for(const texture of ['straight','wavy','curly','coily'])for(const goal of ['natural','classic','bold']){const rows=recommendReferences(shape,texture,goal);assert(rows.length>=2);assert.equal(new Set(rows.map(x=>x.id)).size,rows.length);assert(rows.every(x=>x.name&&x.reason&&x.source&&existsSync(`web/assets/references/${x.image}.svg`)));}
assert.notDeepEqual(recommendReferences('long','straight','natural').map(x=>x.id),recommendReferences('round','straight','natural').map(x=>x.id));
const r=report(state,monday(brazilNow().date));assert.equal(r.barbers.reduce((n,b)=>n+b.profit,0),r.profit);
console.log('Projeção pública sem dados privados; preço calculado no servidor; conflito; 60 combinações de referências com imagens: OK.');
