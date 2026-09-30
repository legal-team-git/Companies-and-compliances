import csv,glob,re,collections,os
from rapidfuzz import process, fuzz
R='/home/user/Companies-and-compliances/data/'
def norm(n):
    n=n.lower(); n=re.sub(r'\(.*?\)',' ',n); n=n.replace('&',' and ')
    n=re.sub(r'[^a-z0-9 ]',' ',n)
    n=re.sub(r'\b(limited|ltd|private|pvt|the|company|co|corporation|corp|india|of)\b',' ',n); return re.sub(r'\s+',' ',n).strip()
rank={'Search-confirmed':0,'Knowledge-based':1,'Needs manual check':2}
rows=[]
for f in sorted(glob.glob(R+'companies/*.csv')):
    for r in csv.DictReader(open(f,encoding='utf-8')):
        r['_file']=os.path.basename(f); rows.append(r)
# dedupe by normalized name
best={}
for r in rows:
    k=norm(r['name'])
    if not k: continue
    if k not in best: best[k]=r; best[k]['_files']={r['_file']}
    else:
        b=best[k]; b['_files'].add(r['_file'])
        if rank.get(r['verification'],3)<rank.get(b['verification'],3):
            r['_files']=b['_files']; best[k]=r
        for fld in ('ticker_or_cin','hq'):
            if not best[k][fld] and r[fld]: best[k][fld]=r[fld]
# NSE
nse=list(csv.reader(open(R+'official/EQUITY_L.csv',encoding='utf-8')))[1:]
nse=[[c.strip() for c in x] for x in nse]
nse_by_sym={x[0]:x for x in nse}
nse_norm=collections.defaultdict(list)
for x in nse: nse_norm[norm(x[1])].append(x)
nse_keys=list(nse_norm)
matched=set(); stat=collections.Counter()
out=[]
for k,r in best.items():
    isin=''; series=''; sym=(r['ticker_or_cin'] or '').strip()
    listed=r['listing'].startswith('Listed')
    hit=None
    if sym in nse_by_sym and listed: hit=nse_by_sym[sym]; stat['sym_match']+=1
    elif k in nse_norm and len(nse_norm[k])==1: hit=nse_norm[k][0]; stat['name_exact']+=1
    elif listed:
        m=process.extractOne(k,nse_keys,scorer=fuzz.token_sort_ratio,score_cutoff=93)
        if m and len(nse_norm[m[0]])==1: hit=nse_norm[m[0]][0]; stat['name_fuzzy']+=1
    if hit:
        matched.add(hit[0]); sym=hit[0]; isin=hit[6]; series=hit[2]
        if not listed: stat['unlisted_flag_fixed']+=1
        listing='Listed-NSE'+('+BSE' if r['listing']=='Listed-NSE+BSE' else '')
    else:
        listing=r['listing']
        if listed: stat['listed_not_on_nse']+=1
        sym=sym if listed else ''
    cin=''
    out.append(dict(name=r['name'],entity_type=r['entity_type'],ownership=r['ownership'],state_region=r['state_region'],hq=r['hq'],
      sector_raw=r['sector'],sub_sector_raw=r['sub_sector'],listing=listing,ticker=sym,isin=isin,nse_series=series,cin=cin,
      src=';'.join(sorted(r['_files'])),origin='agent'))
added=0
for x in nse:
    if x[0] in matched: continue
    out.append(dict(name=x[1],entity_type='Public Limited',ownership='',state_region='',hq='',sector_raw='',sub_sector_raw='',
      listing='Listed-NSE',ticker=x[0],isin=x[6],nse_series=x[2],cin='',src='NSE official EQUITY_L',origin='nse_added')); added+=1
for i,o in enumerate(out,1): o['id']=f'C{i:05d}'
cols=['id','name','entity_type','ownership','state_region','hq','sector_raw','sub_sector_raw','listing','ticker','isin','nse_series','cin','src','origin']
w=csv.DictWriter(open(R+'unified_companies.csv','w',newline='',encoding='utf-8'),fieldnames=cols,quoting=csv.QUOTE_ALL); w.writeheader(); w.writerows(out)
print('input rows',len(rows),'after dedupe',len(best),'NSE-added',added,'final',len(out)); print(dict(stat))
