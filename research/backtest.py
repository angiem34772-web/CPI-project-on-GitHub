import pickle, numpy as np, sys
idx,sa,ri,eia,fac=pickle.load(open('panel_full.pkl','rb'))
def mi(m): return int(m[:4])*12+int(m[5:])-1
def ms(i): return f'{i//12:04d}-{i%12+1:02d}'
A='All items'; CORE='All items less food and energy'; T='Tobacco and smoking products'
base=['Food at home','Food away from home','Gasoline (all types)','Fuel oil','Electricity','Utility (piped) gas service','Apparel','New vehicles','Used cars and trucks','Medical care commodities','Alcoholic beverages',T,'Rent of primary residence',"Owners' equivalent rent of residences",'Medical care services','Motor vehicle insurance','Airline fares','Motor vehicle maintenance and repair','Household furnishings and operations','Recreation','Education','Communication','Other goods and services']
proxy={'Apparel':(("Women's apparel",0.5),("Men's and boys' apparel",0.3),('Footwear',0.2)),'Household furnishings and operations':(('Household furnishings and supplies',0.8),('Moving, storage, freight expense',0.2)),'Recreation':(('Toys',0.15),('Pet services including veterinary',0.15),('Cable, satellite, and live streaming television service',0.3),('Club membership for shopping clubs, fraternal, or other organizations, or participant sports fees',0.2),('Televisions',0.1),('Other video equipment',0.1)),'Education':(('Tuition, other school fees, and childcare',1.0),),'Communication':(('Telephone hardware, calculators, and other consumer information items',0.3),('Postage',0.1),('Delivery services',0.1),('Cable, satellite, and live streaming television service',0.5)),'Other goods and services':(('Personal care',1.0),),'Food at home':(),'Food away from home':(),'Medical care commodities':(),'Alcoholic beverages':(),T:(),'Motor vehicle maintenance and repair':()}
def gap(name,t):
    prev=ms(mi(t)-1)
    if name in proxy: return sum(w*(fac[n][mi(prev)%12]/fac[n][mi(t)%12]-1)*100 for n,w in proxy[name])
    return (fac[name][mi(prev)%12]/fac[name][mi(t)%12]-1)*100 if name in fac else 0.0
def wt(c,m):
    ks=[k for k in ri.get(c,{}) if mi(k)<=mi(m)]; return ri[c][max(ks,key=mi)] if ks else None
def run(k=4,start='2020-11',use_eia=True,use_resid=True,shrink=0.0):
    out=[]
    comps=base if use_resid else base[:18]
    for t in sorted(idx[A]):
        p=ms(mi(t)-1)
        if mi(t)<mi(start) or p not in idx[A]: continue
        tot_w=0; tot=0
        for c in comps:
            w=wt(c,p)
            if w is None or p not in idx.get(c,{}): continue
            sas=[sa[c][m] for m in sorted(sa.get(c,{})) if mi(m)<=mi(p)][-k:]
            if not sas: continue
            trend=np.mean(sas)
            if shrink: 
                lng=[sa[c][m] for m in sorted(sa.get(c,{})) if mi(m)<=mi(p)][-12:]
                trend=(1-shrink)*trend+shrink*np.mean(lng)
            fc=trend-gap(c,t)
            if use_eia and c=='Gasoline (all types)' and t in eia and p in eia: fc=(eia[t]/eia[p]-1)*100
            tot_w+=w; tot+=w*fc
        rw=100-tot_w
        core_sas=[sa[CORE][m] for m in sorted(sa[CORE]) if mi(m)<=mi(p)][-k:]
        rg=(fac['Services less rent of shelter'][mi(p)%12]/fac['Services less rent of shelter'][mi(t)%12]-1)*100
        m=(tot+rw*(np.mean(core_sas)-rg))/100
        act=(idx[A][t]/idx[A][p]-1)*100; py=ms(mi(t)-12)
        yo=lambda x: ((idx[A][p]*(1+x/100))/idx[A][py]-1)*100 if py in idx[A] else np.nan
        asa=sa[A].get(t); msa=m+(asa-act) if asa is not None else np.nan
        out.append((t,act,m,yo(act),yo(m),asa,msa,rw))
    return out
def score(out,label,show=True):
    R=np.array([[x[1],x[2]] for x in out]); e=R[:,1]-R[:,0]
    Y=np.array([[x[3],x[4]] for x in out if not np.isnan(x[3])]); ye=np.round(Y[:,1],1)-np.round(Y[:,0],1)
    S=np.array([[x[5],x[6]] for x in out if x[5] is not None]); se=np.round(S[:,1],1)-S[:,0]
    d=dict(n=len(R),mae=np.mean(np.abs(e)),rmse=np.sqrt(np.mean(e**2)),bias=np.mean(e),yoy_hit=np.mean(ye==0),yoy_1=np.mean(np.abs(ye)<=0.1+1e-9),sa_hit=np.mean(np.abs(se)<1e-9),sa_per=np.mean(np.abs(se)))
    if show: print(f"{label:40s} n={d['n']:2d} MAE {d['mae']:.3f} RMSE {d['rmse']:.3f} bias {d['bias']:+.3f} | YoY hit {d['yoy_hit']:.0%} ±0.1 {d['yoy_1']:.0%} | SA hit {d['sa_hit']:.0%} |SAerr|/print {d['sa_per']:.3f}")
    return d
if __name__=='__main__':
    print('=== FULL SAMPLE Nov 2020 – Sep 2026 ===')
    for k in (2,3,4,6,12): score(run(k),f'trend={k}, resid, EIA')
    score(run(4,use_eia=False),'trend=4, resid, NO EIA')
    score(run(4,use_resid=False),'trend=4, NO resid, EIA')
    for s in (0.3,0.5): score(run(4,shrink=s),f'trend=4 shrunk {s:.0%} to 12-mo')
    print('\n=== BY PERIOD, trend=4 ===')
    full=run(4)
    for lab,a,b in (('2020-11..2021-12 (reopening)','2020-11','2021-12'),('2022 (peak/energy)','2022-01','2022-12'),('2023 (disinflation)','2023-01','2023-12'),('2024 (calm)','2024-01','2024-12'),('2025-26 (tariff/energy)','2025-01','2026-09')):
        score([x for x in full if mi(a)<=mi(x[0])<=mi(b)],lab)
    print('\n=== Naive benchmark (last month NSA repeats) ===')
    nv=[]
    for x in full:
        p=ms(mi(x[0])-1); pp=ms(mi(x[0])-2)
        if pp in idx[A]: nv.append((x[0],x[1],(idx[A][p]/idx[A][pp]-1)*100,x[3],np.nan,x[5],np.nan,0))
    R=np.array([[x[1],x[2]] for x in nv]); e=R[:,1]-R[:,0]; print(f'naive n={len(R)} MAE {np.mean(np.abs(e)):.3f} RMSE {np.sqrt(np.mean(e**2)):.3f}')
    pickle.dump(full,open('bt_full.pkl','wb'))
