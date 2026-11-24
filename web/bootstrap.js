document.querySelector('.skip').onclick=e=>{e.preventDefault();document.querySelector('#main').focus()};
const url=new URL(location.href);
if(location.hash.startsWith('#admin?')){url.searchParams.set('area','admin');history.replaceState(null,'',url)}
try{
 const r=await fetch('/api/auth/session',{credentials:'same-origin',cache:'no-store'});
 if(!r.ok)throw Error('Servidor indisponível.');
 window.__SB_AUTH=await r.json();
 if(url.searchParams.get('area')==='admin'&&window.__SB_AUTH.admin)await import('./app.js');
 else await import('./client.js');
}catch(e){document.querySelector('#sidebar').hidden=true;document.querySelector('.shell').style.marginLeft='0';document.querySelector('#main').innerHTML='<section class="panel"><span class="eyebrow">SANTO BIGODE</span><h1>Vamos reconectar?</h1><p>Não foi possível conectar ao sistema. Confira sua conexão e tente novamente. Se o problema continuar, fale com o responsável pela barbearia.</p><button class="button primary" id="retry-load">Tentar novamente</button></section>';document.querySelector('#retry-load').onclick=()=>location.reload()}
