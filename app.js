// FoundHer Content Calendar (read-only web version).
// Posts come from data/posts.json; assets live in /assets. Claude updates both and pushes.
const TYPES={event:"Event",article:"Article",auction:"Auction",recap:"Recap",app:"App tutorial"};
const STATUSES={placeholder:"Placeholder",draft:"Draft",review:"Ready for Jess",approved:"Approved by Jess",posted:"Posted"};
// Weekly formula: default slot for each weekday (0 = Sunday).
const SLOT=["auction","event","article","auction","recap","event","article"];
const MONTHS=["January","February","March","April","May","June","July","August","September","October","November","December"];
const DAYS=["Sunday","Monday","Tuesday","Wednesday","Thursday","Friday","Saturday"];

const now=new Date();
const pad=n=>String(n).padStart(2,"0");
const ymd=d=>d.getFullYear()+"-"+pad(d.getMonth()+1)+"-"+pad(d.getDate());
const todayKey=ymd(now);
const state={y:now.getFullYear(),m:now.getMonth(),sel:todayKey,posts:[],loaded:false,failed:false};
const $=s=>document.querySelector(s);
const el=(tag,cls,text)=>{const e=document.createElement(tag);if(cls)e.className=cls;if(text!=null)e.textContent=text;return e;};

function toast(msg){const t=$("#toast");t.textContent=msg;t.classList.add("on");clearTimeout(toast._t);toast._t=setTimeout(()=>t.classList.remove("on"),1800);}

async function copyText(text,btn){
  try{await navigator.clipboard.writeText(text);done();}
  catch(e){
    const ta=document.createElement("textarea");ta.value=text;ta.setAttribute("readonly","");ta.style.position="fixed";ta.style.opacity="0";
    document.body.appendChild(ta);ta.select();let ok=false;try{ok=document.execCommand("copy");}catch(_){}
    ta.remove();if(ok)done();else toast("Select the text and copy it manually");
  }
  function done(){toast("Copied");if(btn){const o=btn.textContent;btn.textContent="Copied";btn.classList.add("done");setTimeout(()=>{btn.textContent=o;btn.classList.remove("done");},1500);}}
}

function postsOn(key){return state.posts.filter(p=>p.date===key).sort((a,b)=>(a.order||0)-(b.order||0));}

function renderGrid(){
  $("#monthlabel").textContent=MONTHS[state.m]+" "+state.y;
  const g=$("#grid");g.replaceChildren();
  const first=new Date(state.y,state.m,1);
  const offset=(first.getDay()+6)%7; // Monday first
  const start=new Date(state.y,state.m,1-offset);
  const weeks=Math.ceil((offset+new Date(state.y,state.m+1,0).getDate())/7);
  for(let i=0;i<weeks*7;i++){
    const d=new Date(start.getFullYear(),start.getMonth(),start.getDate()+i);
    const key=ymd(d);
    const b=el("button","day");
    if(d.getMonth()!==state.m)b.classList.add("out");
    if(key===todayKey)b.classList.add("today");
    if(key===state.sel)b.classList.add("sel");
    const ps=postsOn(key);
    b.setAttribute("aria-label",DAYS[d.getDay()]+" "+d.getDate()+" "+MONTHS[d.getMonth()]+(ps.length?", "+ps.length+" post"+(ps.length>1?"s":""):""));
    b.appendChild(el("span","num",d.getDate()));
    const chips=el("div","chips");
    ps.forEach(p=>{const c=el("span","chip"+(p.status==="placeholder"?" ph":""));const dot=el("i","dot d-"+(TYPES[p.type]?p.type:"event"));c.append(dot,el("span","lbl",p.title||TYPES[p.type]||"Post"));chips.appendChild(c);});
    b.appendChild(chips);
    if(!ps.length)b.appendChild(el("span","slot",TYPES[SLOT[d.getDay()]]));
    b.addEventListener("click",()=>{state.sel=key;if(d.getMonth()!==state.m){state.y=d.getFullYear();state.m=d.getMonth();}render();
      if(window.matchMedia("(max-width:900px)").matches)$("#panel").scrollIntoView({behavior:matchMedia("(prefers-reduced-motion:reduce)").matches?"auto":"smooth",block:"start"});});
    g.appendChild(b);
  }
}

function linkRow(k,v){
  const r=el("div","linkrow");r.appendChild(el("span","k",k));
  r.appendChild(el("code",null,v));
  const b=el("button","copybtn","Copy");b.addEventListener("click",()=>copyText(v,b));r.appendChild(b);return r;
}

function labelRow(text,btn){const l=el("div","label");l.appendChild(el("span",null,text));if(btn)l.appendChild(btn);return l;}

function renderPost(p){
  const card=el("article","post");
  const head=el("div","posthead");
  const t=TYPES[p.type]?p.type:"event";
  const tag=el("span","typetag");tag.style.color=`var(--t-${t})`;tag.append(el("i","dot d-"+t),document.createTextNode(TYPES[t]+(p.platform?" · "+p.platform:"")));
  head.appendChild(tag);
  const st=STATUSES[p.status]?p.status:"draft";
  const sw=el("span","status st-"+st);const sd=el("i","dot");sd.style.background="currentColor";sw.append(sd,document.createTextNode(STATUSES[st]));
  head.appendChild(sw);
  card.appendChild(head);
  card.appendChild(el("h4",null,p.title||"Untitled post"));

  const as=el("div","section");as.appendChild(labelRow("Asset"));
  if(p.asset){
    const box=el("div","asset");
    const type=p.assetType||(/\.(png|jpe?g|webp|gif)$/i.test(p.asset)?"image/":"video/");
    if(type.startsWith("image/")){const im=document.createElement("img");im.src=p.asset;im.alt="Post asset preview";box.appendChild(im);}
    else if(type.startsWith("video/")){const v=document.createElement("video");v.src=p.asset;v.muted=true;v.playsInline=true;v.controls=true;v.preload="metadata";box.appendChild(v);}
    const meta=el("div","meta");
    meta.appendChild(el("span","fname",p.assetName||p.asset.split("/").pop()));
    const dl=el("a","primary","Download asset");dl.href=p.asset;dl.setAttribute("download",p.assetName||p.asset.split("/").pop());meta.appendChild(dl);
    box.appendChild(meta);as.appendChild(box);
  }else{
    as.appendChild(el("div","noasset",p.assetNote||"No asset attached yet."));
  }
  card.appendChild(as);

  // Optional Instagram Story version with interactive stickers to add in the app.
  const S=p.story;
  if(S&&S.asset){
    const ss=el("div","section");ss.appendChild(labelRow("Story + interactive stickers"));
    const box=el("div","asset");
    const v=document.createElement("video");v.src=S.asset;v.muted=true;v.playsInline=true;v.controls=true;v.preload="metadata";box.appendChild(v);
    const meta=el("div","meta");
    const name=S.assetName||S.asset.split("/").pop();
    meta.appendChild(el("span","fname",name));
    const dl=el("a","primary","Download story");dl.href=S.asset;dl.setAttribute("download",name);meta.appendChild(dl);
    if(S.how)meta.appendChild(el("p","note",S.how));
    box.appendChild(meta);ss.appendChild(box);
    if(Array.isArray(S.stickers)&&S.stickers.length){
      const lb=el("div","links");
      S.stickers.forEach(s=>lb.appendChild(linkRow(s.label,s.value)));
      ss.appendChild(lb);
    }
    card.appendChild(ss);
  }

  if(p.caption){
    const both=[p.caption,p.hashtags].filter(Boolean).join("\n\n");
    const cb=el("button","copybtn","Copy caption + hashtags");cb.addEventListener("click",()=>copyText(both,cb));
    const cs=el("div","section");cs.append(labelRow("Caption",cb),el("div","textbox",p.caption));card.appendChild(cs);
  }
  if(p.hashtags){
    const hb=el("button","copybtn","Copy");hb.addEventListener("click",()=>copyText(p.hashtags,hb));
    const hs=el("div","section");hs.append(labelRow("Hashtags",hb),el("div","textbox",p.hashtags));card.appendChild(hs);
  }
  const L=p.links||{};
  if(L.instagram||L.facebook||p.linktreeTitle){
    const ls=el("div","section");ls.appendChild(labelRow("Links"));
    const box=el("div","links");
    if(L.instagram)box.appendChild(linkRow("Instagram / Linktree",L.instagram));
    if(L.facebook)box.appendChild(linkRow("Facebook",L.facebook));
    if(p.linktreeTitle)box.appendChild(linkRow("Linktree title",p.linktreeTitle));
    ls.appendChild(box);card.appendChild(ls);
  }
  if(p.notes)card.appendChild(el("p","note",p.notes));
  return card;
}

function renderPanel(){
  const pn=$("#panel");pn.replaceChildren();
  const [Y,M,D]=state.sel.split("-").map(Number);const d=new Date(Y,M-1,D);
  pn.appendChild(el("h3",null,DAYS[d.getDay()]+", "+D+" "+MONTHS[M-1]));
  if(state.failed){pn.appendChild(el("div","empty","The posts didn't load. Refresh the page to try again."));return;}
  if(!state.loaded){pn.appendChild(el("div","empty","Loading posts…"));return;}
  const ps=postsOn(state.sel);
  if(!ps.length){
    const e=el("div","empty");
    e.append(el("strong",null,"Nothing scheduled. "),document.createTextNode("This day's usual slot is "+TYPES[SLOT[d.getDay()]].toLowerCase()+"."));
    pn.appendChild(e);return;
  }
  pn.appendChild(el("p","sub",ps.length+" post"+(ps.length>1?"s":"")+" for this day. Download the asset, copy the caption, then add music in Instagram."));
  ps.forEach(p=>pn.appendChild(renderPost(p)));
}

function render(){renderGrid();renderPanel();}

$("#prev").addEventListener("click",()=>{state.m--;if(state.m<0){state.m=11;state.y--;}render();});
$("#next").addEventListener("click",()=>{state.m++;if(state.m>11){state.m=0;state.y++;}render();});
$("#todaybtn").addEventListener("click",()=>{state.y=now.getFullYear();state.m=now.getMonth();state.sel=todayKey;render();});

render();
fetch("data/posts.json",{cache:"no-store"}).then(r=>{if(!r.ok)throw new Error(r.status);return r.json();}).then(j=>{
  state.posts=j.posts||[];state.loaded=true;
  if(j.updatedAt){const u=new Date(j.updatedAt);$("#updated").textContent="Updated "+u.toLocaleDateString(undefined,{day:"numeric",month:"short",year:"numeric"});}
  render();
}).catch(()=>{state.failed=true;render();});
