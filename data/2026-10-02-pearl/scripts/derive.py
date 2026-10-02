import json, glob, math, datetime as dt
def load(prefix):
    f=sorted(glob.glob(prefix+'_market_chart_365_*.json'))[-1]
    d=json.load(open(f))
    daily={}; last=None
    for ts,p in d['prices']:
        t=dt.datetime.fromtimestamp(ts/1000,dt.timezone.utc)
        if t.hour==0 and t.minute==0 and t.second==0: daily[t.date()]=p
        last=(t,p)
    return f,daily,last
S={}
for k in ['pearl-2','bitcoin','bittensor','render-token']:
    f,daily,last=load(k); S[k]=daily
    print(k,f,len(daily),min(daily),max(daily),'last',last)
D=dt.date
p=S['pearl-2']
for d in ['2026-06-22','2026-06-25','2026-07-23','2026-08-20','2026-08-30','2026-08-31','2026-09-10','2026-09-11','2026-09-17','2026-09-18','2026-09-23','2026-09-27','2026-10-01','2026-10-02']:
    print(d, p.get(D.fromisoformat(d)))
dates=[D(2026,8,20)+dt.timedelta(i) for i in range(44)]
assert dates[-1]==D(2026,10,2)
for k in S: 
    miss=[x for x in dates if x not in S[k]]; print(k,'missing',miss)
ret={k:S[k][dates[-1]]/S[k][dates[0]]-1 for k in S}
print('returns',{k:round(v*100,1) for k,v in ret.items()})
lr={k:[math.log(S[k][dates[i]]/S[k][dates[i-1]]) for i in range(1,44)] for k in S}
def sd(x):
    m=sum(x)/len(x); return math.sqrt(sum((a-m)**2 for a in x)/(len(x)-1))
def corr(a,b):
    ma,mb=sum(a)/len(a),sum(b)/len(b)
    return sum((x-ma)*(y-mb) for x,y in zip(a,b))/math.sqrt(sum((x-ma)**2 for x in a)*sum((y-mb)**2 for y in b))
print('annvol',{k:round(sd(lr[k])*math.sqrt(365)*100,1) for k in S})
print('corr vs PRL',{k:round(corr(lr['pearl-2'],lr[k]),2) for k in S})
# peak daily in Sep
sep={d:v for d,v in p.items() if d>=D(2026,9,1)}
mx=max(sep,key=sep.get); print('max daily since Sep 1',mx,sep[mx])
print('Sep27->Oct2', p[D(2026,10,2)]/p[D(2026,9,27)]-1)
print('Aug30->Sep27', p[D(2026,9,27)]/p[D(2026,8,30)])
print('Sep10->11',p[D(2026,9,11)]/p[D(2026,9,10)]-1,'Sep17->18',p[D(2026,9,18)]/p[D(2026,9,17)]-1)
# biggest daily moves
mv=sorted(((p[d]/p[d-dt.timedelta(1)]-1,d) for d in p if d-dt.timedelta(1) in p and d>=D(2026,8,20)),reverse=True)[:5]; print('top daily moves',[(str(d),round(r*100,1)) for r,d in mv])
print('Aug20->Oct2 multiple', p[D(2026,10,2)]/p[D(2026,8,20)], 'Aug31->peak', sep[mx]/p[D(2026,8,31)], 'Aug20->peak', sep[mx]/p[D(2026,8,20)])
print('Jun25->Jul23', p[D(2026,7,23)]/p[D(2026,6,25)]-1)
