import csv,re,time,threading,os,sys,urllib.parse,html
import requests
R='data/'; OUT=R+'official/screener_classification.csv'
UA="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
syms=[r['ticker'] for r in csv.DictReader(open(R+'unified_companies.csv',encoding='utf-8')) if r['ticker'] and r['listing'].startswith('Listed')]
done=set()
if os.path.exists(OUT): done={r['symbol'] for r in csv.DictReader(open(OUT,encoding='utf-8'))}
else: open(OUT,'w',newline='',encoding='utf-8').write('symbol,broad_sector,sector,broad_industry,industry,status\n')
todo=[s for s in dict.fromkeys(syms) if s not in done]
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
        for attempt in range(4):
            try:
                r=s.get('https://www.screener.in/company/'+urllib.parse.quote(sym,safe='')+'/',timeout=30)
                if r.status_code==429: time.sleep(20*(attempt+1)); continue
                if r.status_code!=200: st=f'http{r.status_code}'; break
                vals={k:html.unescape(v).strip() for k,v in pat.findall(r.text)}
                if not vals: st='no_class'
                break
            except Exception as e: st='err'; time.sleep(3)
        with lock:
            with open(OUT,'a',newline='',encoding='utf-8') as f:
                csv.writer(f).writerow([sym,vals.get('Broad Sector',''),vals.get('Sector',''),vals.get('Broad Industry',''),vals.get('Industry',''),st])
        time.sleep(1.0)
ts=[threading.Thread(target=work) for _ in range(3)]
[t.start() for t in ts]; [t.join() for t in ts]; print('finished',flush=True)
