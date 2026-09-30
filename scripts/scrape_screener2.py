import csv,time,threading,os,urllib.parse,re,html,requests
R='data/'; OUT=R+'official/screener_classification.csv'
UA="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
todo=[l.strip() for l in open(R+'work/tickers_todo2.txt') if l.strip()]
print('todo',len(todo),flush=True)
lock=threading.Lock(); it=iter(todo)
pat=re.compile(r'title="(Broad Sector|Sector|Broad Industry|Industry)">\s*([^<]+?)\s*</a>',re.S)
def work():
    s=requests.Session(); s.headers['User-Agent']=UA
    while True:
        with lock:
            try: sym=next(it)
            except StopIteration: return
        st='ok'; vals={}
        # try both /company/<code>/ (BSE numeric) and normal ticker
        for attempt in range(3):
            try:
                r=s.get('https://www.screener.in/company/'+urllib.parse.quote(sym,safe='')+'/',timeout=25)
                if r.status_code==429: time.sleep(15*(attempt+1)); continue
                if r.status_code!=200: st=f'http{r.status_code}'; break
                vals={k:html.unescape(v).strip() for k,v in pat.findall(r.text)}
                if not vals: st='no_class'
                break
            except Exception: st='err'; time.sleep(3)
        with lock:
            with open(OUT,'a',newline='',encoding='utf-8') as f:
                csv.writer(f).writerow([sym,vals.get('Broad Sector',''),vals.get('Sector',''),vals.get('Broad Industry',''),vals.get('Industry',''),st])
        time.sleep(0.6)
ts=[threading.Thread(target=work) for _ in range(8)]
[t.start() for t in ts]; [t.join() for t in ts]; print('finished',flush=True)
