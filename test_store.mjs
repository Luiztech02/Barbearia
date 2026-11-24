import assert from 'node:assert/strict';
import {seedState,validate,report,monday,appointment,available,addDays,iso,importLegacy} from './web/store.js';
const s=seedState();validate(s);
const r=report(s,monday());
assert.equal(r.barbers.reduce((sum,b)=>sum+b.profit,0),r.profit,'O lucro dos três precisa fechar com o total');
assert.equal(r.revenue-r.direct-r.expenses,r.profit);
assert.equal(r.barbers.reduce((sum,b)=>sum+b.hair,0),r.hair);
const combo=s.appointments.find(x=>x.serviceId==='combo'&&x.status==='completed');
if(combo){const before=report(s,monday());s.appointments.push({...combo,id:'extra',client:combo.client,time:'22:00'});const after=report(s,monday());assert.equal(after.clients,before.clients,'Cliente recorrente não duplica os clientes únicos');assert.equal(after.visits,before.visits+1);s.appointments.pop()}
const date=addDays(iso(),10),barberId=s.barbers[0].id;
const booking=appointment(s,{client:'Teste local',barberId,date,time:'10:00',serviceId:'cut',visage:true});
assert.equal(booking.price,14000);assert.equal(booking.duration,100);s.appointments.push(booking);
assert(!available(s,date,barberId,30).includes('11:00'),'O adicional ocupa mais tempo na agenda');
assert(available(s,date,s.barbers[1].id,30).includes('11:00'),'Outro barbeiro permanece disponível');
assert.throws(()=>appointment(s,{client:'Conflito',barberId,date,time:'10:30',serviceId:'cut'}));
const legacy='F\t2026-11-15\nH60\t2026-11-14\t07:00\nR\tLuiz\tCorte\t2026-11-14\t11:00\t40';
const out=importLegacy(s,legacy,barberId);assert.equal(out.count,1);assert.equal(out.blocks,2);assert.equal(importLegacy(s,legacy,barberId).count,0);validate(s);
const empty=seedState();empty.appointments=[];const zero=report(empty,monday());assert.equal(zero.barbers.reduce((sum,b)=>sum+b.profit,0),zero.profit);
console.log('Financeiro, clientes únicos, adicional de R$ 100, duração, conflitos, barbeiros e importação: OK.');
