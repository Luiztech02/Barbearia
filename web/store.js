export const iso = (d=new Date()) => `${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,'0')}-${String(d.getDate()).padStart(2,'0')}`;
export const fromISO = s => new Date(s+'T12:00:00');
export function addDays(s,n){const d=fromISO(s);d.setDate(d.getDate()+n);return iso(d)}
export function monday(s=iso()){const d=fromISO(s);return addDays(s,-((d.getDay()+6)%7))}
export const money = cents => (Number(cents||0)/100).toLocaleString('pt-BR',{style:'currency',currency:'BRL'});
export const uid = () => globalThis.crypto?.randomUUID?.() || `id-${Date.now()}-${Math.random().toString(36).slice(2)}`;
export const mins = t => Number(t.slice(0,2))*60+Number(t.slice(3,5));
export const time = m => `${String(Math.floor(m/60)).padStart(2,'0')}:${String(m%60).padStart(2,'0')}`;
export const normalize = s => String(s).trim().toLocaleLowerCase('pt-BR').normalize('NFD').replace(/[\u0300-\u036f]/g,'');
export const COLORS=['#b67c52','#69745c','#d4c5aa'];
export function seedState(){
 const start=monday(),today=iso(),services=[{id:'cut',name:'Corte de cabelo',price:4000,cost:800,duration:40,hair:1,beard:0},{id:'beard',name:'Barba completa',price:3000,cost:600,duration:30,hair:0,beard:1},{id:'combo',name:'Corte + barba',price:6500,cost:1400,duration:60,hair:1,beard:1},{id:'visage',name:'Visagismo',price:10000,cost:1500,duration:60,hair:0,beard:0},{id:'custom',name:'Serviço personalizado',price:6000,cost:1000,duration:60,hair:0,beard:0}];
 const barbers=[{id:'rafael',name:'Rafael Almeida',role:'Barbeiro & visagista'},{id:'lucas',name:'Lucas Santos',role:'Barbeiro'},{id:'matheus',name:'Matheus Costa',role:'Barbeiro'}];
 const names=['Gabriel Lima','Pedro Henrique','Bruno Oliveira','André Souza','Felipe Rocha','Diego Martins','Thiago Alves','Daniel Ribeiro','Gustavo Silva','Caio Fernandes','Eduardo Castro','João Miguel','Marcos Vinícius','Arthur Lopes','Henrique Dias','Vitor Moreira','Renato Azevedo','Leonardo Reis','Paulo Ferreira','Igor Melo','Fernando Nunes','Samuel Pires','Alex Borges','Davi Cardoso'];
 const appointments=[];
 for(let d=0;d<6;d++){const date=addDays(start,d);for(let b=0;b<3;b++){for(let k=0;k<3+(d+b)%3;k++){const svc=services[(d+b+k)%7===0?3:((d+b+k)%3)],hour=9+k*2,tm=time(hour*60);appointments.push({id:`demo-${d}-${b}-${k}`,client:names[(d*7+b*3+k)%names.length],phone:'',barberId:barbers[b].id,serviceId:svc.id,service:svc.name,date,time:tm,duration:svc.duration,price:svc.price,cost:svc.cost,hair:svc.hair,beard:svc.beard,status:date<today||(date===today&&hour<12)?'completed':'scheduled',notes:'Atendimento demonstrativo',visage:false,source:'demo'});}}}
 return {schema:1,demo:true,settings:{name:'Santo Bigode',whatsapp:'',open:'07:00',close:'23:00'},barbers,services,appointments,expenses:[{id:'demo-exp1',date:start,name:'Aluguel proporcional da semana',amount:45000},{id:'demo-exp2',date:addDays(start,1),name:'Energia e despesas operacionais',amount:12500}],products:[{id:'pomade',name:'Pomada modeladora matte',category:'Finalização',unit:'un',quantity:18,min:5,cost:2200,sale:4500},{id:'oil',name:'Óleo para barba',category:'Barba',unit:'un',quantity:4,min:5,cost:1800,sale:3500},{id:'shampoo',name:'Shampoo profissional 1 L',category:'Cabelo',unit:'un',quantity:8,min:3,cost:3200,sale:6500},{id:'blade',name:'Lâmina descartável',category:'Descartáveis',unit:'un',quantity:120,min:50,cost:90,sale:0},{id:'balm',name:'Balm pós-barba',category:'Barba',unit:'un',quantity:2,min:4,cost:2500,sale:4800},{id:'neck',name:'Gola higiênica (rolo)',category:'Descartáveis',unit:'un',quantity:12,min:4,cost:1200,sale:0}],movements:[],blocks:[]};
}
export function report(state,start){
 const end=addDays(start,6),a=state.appointments.filter(x=>x.date>=start&&x.date<=end&&x.status==='completed'),expenses=state.expenses.filter(x=>x.date>=start&&x.date<=end).reduce((s,x)=>s+x.amount,0),revenue=a.reduce((s,x)=>s+x.price,0),direct=a.reduce((s,x)=>s+x.cost,0);
 let allocated=0;
 const barbers=state.barbers.map((b,i)=>{const list=a.filter(x=>x.barberId===b.id),rev=list.reduce((s,x)=>s+x.price,0),cost=list.reduce((s,x)=>s+x.cost,0),share=i===state.barbers.length-1?expenses-allocated:Math.round(expenses*(revenue?rev/revenue:1/state.barbers.length));allocated+=share;return {...b,color:COLORS[i],revenue:rev,cost,share,profit:rev-cost-share,visits:list.length,clients:new Set(list.map(clientKey)).size,hair:list.reduce((s,x)=>s+x.hair,0),beard:list.reduce((s,x)=>s+x.beard,0)};});
 const days=Array.from({length:7},(_,i)=>{const date=addDays(start,i),daily=a.filter(x=>x.date===date),exp=state.expenses.filter(x=>x.date===date).reduce((s,x)=>s+x.amount,0);return {date,total:daily.reduce((s,x)=>s+x.price-x.cost,0),cost:exp,barbers:state.barbers.map(b=>daily.filter(x=>x.barberId===b.id).reduce((s,x)=>s+x.price-x.cost,0))}});
 return {revenue,direct,expenses,profit:revenue-direct-expenses,clients:new Set(a.map(clientKey)).size,visits:a.length,hair:a.reduce((s,x)=>s+x.hair,0),beard:a.reduce((s,x)=>s+x.beard,0),barbers,days};
}
const clientKey=x=>x.phone?.replace(/\D/g,'')||normalize(x.client);
export function available(state,date,barberId,duration,exclude=null){
 if(!/^\d{4}-\d{2}-\d{2}$/.test(date)||date<iso())return [];
 const result=[],start=mins(state.settings.open),close=mins(state.settings.close);
 for(let m=start;m+duration<=close;m+=30){if(date===iso()&&m<=new Date().getHours()*60+new Date().getMinutes())continue;const overlaps=state.appointments.some(a=>a.id!==exclude&&a.status!=='cancelled'&&a.date===date&&a.barberId===barberId&&m<mins(a.time)+a.duration&&m+duration>mins(a.time));const blocked=state.blocks.some(x=>x.date===date&&(x.all||m<x.end&&m+duration>x.start));if(!overlaps&&!blocked)result.push(time(m))}return result;
}
export function appointment(state,values){
 const s=state.services.find(x=>x.id===values.serviceId);if(!s)throw Error('Selecione um serviço.');
 if(!values.client?.trim())throw Error('Informe o nome do cliente.');
 const duration=s.duration+(values.visage&&s.id!=='visage'?60:0);
 if(!available(state,values.date,values.barberId,duration).includes(values.time))throw Error('Esse horário não está disponível. Escolha outro.');
 const add=values.visage&&s.id!=='visage';
 return {id:uid(),client:values.client.trim().slice(0,100),phone:values.phone?.trim()||'',barberId:values.barberId,serviceId:s.id,service:s.name+(add?' + visagismo':''),date:values.date,time:values.time,duration,price:s.price+(add?10000:0),cost:s.cost+(add?state.services.find(x=>x.id==='visage').cost:0),hair:s.hair,beard:s.beard,status:'scheduled',notes:values.notes?.trim()||'',visage:!!add,source:'app'};
}
export function validate(state){
 if(!state||typeof state!=='object'||!state.settings||!['barbers','services','appointments','expenses','products','movements','blocks'].every(k=>Array.isArray(state[k])))throw Error('Backup incompatível com o Santo Bigode 2.0.');
 if(state.schema!==1||state.barbers.length!==3)throw Error('O projeto precisa de três barbeiros.');
 if(state.barbers.some(x=>!x.name.trim()))throw Error('Preencha os nomes dos três barbeiros.');
 if(mins(state.settings.open)>=mins(state.settings.close))throw Error('O encerramento deve ser depois da abertura.');
 for(const p of state.products)if(!p.name.trim()||![p.quantity,p.min,p.cost,p.sale].every(x=>Number.isInteger(x)&&x>=0))throw Error('Confira as quantidades e valores do estoque.');
 const ids=new Set();for(const a of state.appointments){if(ids.has(a.id))throw Error('Agendamento duplicado.');ids.add(a.id);if(!state.barbers.some(b=>b.id===a.barberId)||!a.client.trim()||!['scheduled','completed','cancelled'].includes(a.status)||![a.price,a.cost,a.duration,a.hair,a.beard].every(Number.isInteger)||a.duration<=0||a.price<0||a.cost<0)throw Error('Agendamento inválido.');}
 const active=state.appointments.filter(x=>x.status!=='cancelled');for(let i=0;i<active.length;i++)for(let j=i+1;j<active.length;j++){const a=active[i],b=active[j];if(a.date===b.date&&a.barberId===b.barberId&&mins(a.time)<mins(b.time)+b.duration&&mins(b.time)<mins(a.time)+a.duration)throw Error('Existem horários sobrepostos para o mesmo barbeiro.');}
 for(const e of state.expenses)if(!e.name.trim()||!Number.isInteger(e.amount)||e.amount<=0)throw Error('Informe uma despesa com valor positivo.');
 if(state.services.find(x=>x.id==='visage')?.price!==10000)throw Error('O visagismo custa R$ 100,00.');
}
export function importLegacy(state,text,barberId){
 let count=0,blocks=0,skipped=0;
 for(const line of text.trim().split(/\r?\n/)){const f=line.split('\t');if(f[0]==='F'&&/^\d{4}-\d{2}-\d{2}$/.test(f[1])){if(!state.blocks.some(x=>x.date===f[1]&&x.all)){state.blocks.push({date:f[1],all:true});blocks++}continue}if(f[0]==='H60'&&/^\d{4}-\d{2}-\d{2}$/.test(f[1])&&/^\d{2}:\d{2}$/.test(f[2])){if(!state.blocks.some(x=>x.date===f[1]&&x.start===mins(f[2]))){state.blocks.push({date:f[1],start:mins(f[2]),end:mins(f[2])+60});blocks++}continue}if(f[0]!=='R'||f.length<6){if(line.trim())skipped++;continue}
 const id='legacy-'+Array.from(line).reduce((a,c)=>(Math.imul(a,31)+c.charCodeAt(0))|0,0).toString(16);if(state.appointments.some(x=>x.id===id)){skipped++;continue}
 if(!/^\d{4}-\d{2}-\d{2}$/.test(f[3])||!/^\d{2}:\d{2}$/.test(f[4])||!Number.isInteger(Number(f[5]))||Number(f[5])<=0){skipped++;continue}
 const type=normalize(f[2]),sid=type==='corte'?'cut':type==='barba'?'beard':type.startsWith('corte e barba')?'combo':'custom',svc=state.services.find(x=>x.id===sid);
 state.appointments.push({id,client:f[1],phone:'',barberId,serviceId:sid,service:f[2],date:f[3],time:f[4],duration:Number(f[5]),price:svc.price,cost:svc.cost,hair:svc.hair,beard:svc.beard,status:'scheduled',notes:'Importado do Java. Valores estimados da tabela atual; confirme antes de concluir.',visage:false,source:'legacy'});count++;
 }return {count,blocks,skipped};
}
export class Store{
 constructor(){this.state=null;this.revision=0;this.mode='server';this.role='client';this.busy=false;this.session=globalThis.window?.__SB_AUTH||{};}
 async request(path,body,method='POST'){const r=await fetch(path,{method,headers:{'Content-Type':'application/json','X-SB-Request':'1','X-CSRF-Token':this.session.csrf||''},body:JSON.stringify(body),credentials:'same-origin'});let data;try{data=await r.json()}catch{throw Error('O servidor não respondeu. Atualize a página.')}if(!r.ok)throw Error(data.error||'Não foi possível concluir.');return data}
 async init(role='client'){this.role=role;this.session=globalThis.window?.__SB_AUTH||await fetch('/api/auth/session').then(r=>r.json());this.mode=this.session.mode||'server';const r=await fetch(role==='admin'?'/api/state':'/api/public',{headers:{Accept:'application/json'},credentials:'same-origin',cache:'no-store'});const x=await r.json();if(!r.ok)throw Error(x.error||'Não foi possível carregar os dados.');this.state=x.state;this.revision=x.revision||0;}
 async change(fn){if(this.role!=='admin')throw Error('Acesso exclusivo da administração.');if(this.busy)throw Error('Aguarde o salvamento anterior.');this.busy=true;try{const next=structuredClone(this.state);fn(next);validate(next);const x=await this.request('/api/state',{state:next,revision:this.revision},'PUT');this.revision=x.revision;this.state=next;return next}finally{this.busy=false}}
 async book(values){if(this.busy)throw Error('Aguarde a confirmação anterior.');this.busy=true;try{const result=await this.request('/api/bookings',values);if(this.role==='admin')await this.init('admin');else this.state=result.state;return result.booking}catch(e){try{await this.init(this.role)}catch{}throw e}finally{this.busy=false}}
}
