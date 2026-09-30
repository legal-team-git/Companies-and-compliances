import json,time,urllib.request,urllib.parse,csv,sys
UA = "IndiaComplianceResearch/1.0 (educational research project; contact: research@example.org)"
API = "https://en.wikipedia.org/w/api.php"

def get(params, tries=5):
    params.setdefault('format', 'json')
    url = API + '?' + urllib.parse.urlencode(params)
    for i in range(tries):
        req = urllib.request.Request(url, headers={'User-Agent': UA})
        try:
            with urllib.request.urlopen(req, timeout=20) as r:
                d = json.load(r)
                if 'error' in d: raise Exception(d['error'])
                return d
        except Exception as e:
            time.sleep(3 * (i + 1))
    return {}

def members(cat, limit=500):
    out, cont = [], None
    while True:
        p = {'action': 'query', 'list': 'categorymembers', 'cmtitle': 'Category:' + cat, 'cmlimit': limit}
        if cont: p['cmcontinue'] = cont
        d = get(p)
        q = d.get('query', {}).get('categorymembers', [])
        out += q
        cont = d.get('continue', {}).get('cmcontinue')
        time.sleep(1.2)
        if not cont: break
    return out

if __name__ == '__main__':
    cats = sys.argv[1:]
    w = csv.writer(open('data/work/wiki_harvest.csv', 'a', newline='', encoding='utf-8'))
    for cat in cats:
        m = members(cat)
        pages = [x['title'] for x in m if x['ns'] == 0]
        subs = [x['title'].replace('Category:', '') for x in m if x['ns'] == 14]
        print(cat, 'pages:', len(pages), 'subcats:', len(subs))
        for p in pages: w.writerow([cat, p])
        for s in subs: print('  SUBCAT:', s)
