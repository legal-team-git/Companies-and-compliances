import csv,sys
sys.path.insert(0,'scripts')
R='data/'
exec(open('scripts/build_unified.py').read().split("rank=")[0])  # reuse norm()
U=list(csv.DictReader(open(R+'unified_companies.csv',encoding='utf-8')))
cols=list(U[0].keys())
have_norm={norm(r['name']) for r in U}; have_tick={r['ticker'] for r in U if r['ticker']}
n0=len(U); new=[]
for r in csv.DictReader(open(R+'companies/services_institutions.csv',encoding='utf-8')):
    k=norm(r['name'])
    if k in have_norm or (r['ticker_or_cin'] and r['ticker_or_cin'] in have_tick): continue
    have_norm.add(k)
    new.append(dict(name=r['name'],entity_type=r['entity_type'],ownership=r['ownership'],state_region=r['state_region'],hq=r['hq'],
      sector_raw=r['sector'],sub_sector_raw=r['sub_sector'],listing=r['listing'],ticker=r['ticker_or_cin'] if r['listing'].startswith('Listed') else '',
      isin='',nse_series='',cin='',src='services_institutions.csv',origin='agent'))
for i,o in enumerate(new,n0+1): o['id']=f'C{i:05d}'
U+= new
w=csv.DictWriter(open(R+'unified_companies.csv','w',newline='',encoding='utf-8'),fieldnames=cols,quoting=csv.QUOTE_ALL); w.writeheader(); w.writerows(U)
cc=['id','name','entity_type','ownership','state_region','hq','sector_raw','sub_sector_raw','listing']
w=csv.DictWriter(open(R+'work/class_in_6.csv','w',newline='',encoding='utf-8'),fieldnames=cc,extrasaction='ignore',quoting=csv.QUOTE_ALL); w.writeheader(); w.writerows(new)
print('added',len(new),'total',len(U))
