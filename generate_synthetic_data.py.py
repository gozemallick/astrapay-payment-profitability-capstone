import numpy as np, pandas as pd
from pathlib import Path
np.random.seed(42)
base=Path('/mnt/data/astrapay_capstone'); data_dir=base/'data'; data_dir.mkdir(exist_ok=True, parents=True)
start=pd.Timestamp('2026-01-01'); end=pd.Timestamp('2026-06-30'); dates=pd.date_range(start,end,freq='D')
countries=['India','Singapore','UAE']; cur_by={'India':'INR','Singapore':'SGD','UAE':'AED'}; base_rates={'INR':0.01205,'SGD':0.745,'AED':0.2723}
segments=['Consumer','SME','Enterprise']; msegments=['SME','Enterprise','Strategic']; categories=['Retail','Travel','Education','Food','Digital Services','Healthcare','Electronics','Professional Services']; risk_tiers=['Low','Medium','High']; channels=['Card','UPI','Wallet','Bank Transfer']
# Customers
n_c=15000
cust=pd.DataFrame({'customer_id':[f'C{i:06d}' for i in range(1,n_c+1)],'segment':np.random.choice(segments,n_c,p=[.63,.27,.10]),'country':np.random.choice(countries,n_c,p=[.58,.24,.18]),'onboarding_date':np.random.choice(pd.date_range('2024-01-01','2026-05-31'),n_c),'kyc_status':np.random.choice(['VERIFIED','PENDING','REJECTED'],n_c,p=[.88,.09,.03])})
cust.to_csv(data_dir/'customer.csv',index=False)
# Merchants
n_m=1000
m_country=np.random.choice(countries,n_m,p=[.52,.28,.20]); m_segment=np.random.choice(msegments,n_m,p=[.68,.24,.08])
plans=[]
for seg in m_segment:
    plans.append(np.random.choice(['Enterprise','Promotional'],p=[.75,.25]) if seg=='Strategic' else np.random.choice(['Enterprise','Standard','Growth'],p=[.45,.40,.15]) if seg=='Enterprise' else np.random.choice(['Standard','Growth','Promotional','High Risk'],p=[.36,.35,.18,.11]))
merchant=pd.DataFrame({'merchant_id':[f'M{i:05d}' for i in range(1,n_m+1)],'merchant_segment':m_segment,'category':np.random.choice(categories,n_m,p=[.20,.10,.10,.15,.16,.08,.12,.09]),'country':m_country,'pricing_plan':plans,'risk_tier':np.random.choice(risk_tiers,n_m,p=[.55,.34,.11])})
merchant.to_csv(data_dir/'merchant.csv',index=False)
# FX
fx=[]
for d in dates:
    drift=(d-start).days/180
    for cur,rate in base_rates.items():
        fx.append([d.date(),cur,round(rate*(1+np.random.normal(0,.006)+.005*drift),6),'SPOT'])
        fx.append([d.date(),cur,round(rate*(1+.002*np.sin(d.dayofyear/20)+.002*drift),6),'ACCOUNTING'])
fx=pd.DataFrame(fx,columns=['rate_date','currency','rate_to_usd','rate_type']); fx.to_csv(data_dir/'fx_rate.csv',index=False)
# Route cost
route_map=pd.DataFrame({'route_id':['R_IN_01','R_IN_02','R_SG_01','R_SG_02','R_UAE_01','R_UAE_02'],'provider':['SwiftRoute','CostSaver','LionPay','PremiumRail','GulfNet','FastCross'],'region':['India','India','Singapore','Singapore','UAE','UAE']})
rc=[]
for d in dates:
    for _,r in route_map.iterrows():
        fixed={'India':.018,'Singapore':.055,'UAE':.060}[r.region]; var={'India':.0035,'Singapore':.0060,'UAE':.0065}[r.region]
        if r.route_id in ['R_SG_02','R_UAE_02'] and d>=pd.Timestamp('2026-04-01'): fixed*=1.28; var*=1.20
        if r.route_id=='R_IN_02' and d>=pd.Timestamp('2026-04-01'): fixed*=1.10; var*=1.12
        rc.append([r.route_id,r.provider,r.region,d.date(),round(fixed,5),round(var,5)])
route_cost=pd.DataFrame(rc,columns=['route_id','provider','region','cost_date','fixed_fee','variable_fee_pct']); route_cost.to_csv(data_dir/'route_cost.csv',index=False)
# Transactions
n=75000
weights=np.linspace(.65,1.55,len(dates)); weights/=weights.sum(); dsel=np.random.choice(dates,n,p=weights); secs=np.random.randint(0,86400,n); created=pd.to_datetime(dsel)+pd.to_timedelta(secs,unit='s'); late=created>=pd.Timestamp('2026-04-01')
# msegment choice based on period
mseg_choices=np.where(late, np.random.choice(msegments,n,p=[.77,.18,.05]), np.random.choice(msegments,n,p=[.54,.34,.12]))
country_choices=np.where(late, np.random.choice(countries,n,p=[.46,.31,.23]), np.random.choice(countries,n,p=[.56,.25,.19]))
# sample merchant by segment and country fallback
merchant_groups={(seg,c):merchant[(merchant.merchant_segment==seg)&(merchant.country==c)].index.values for seg in msegments for c in countries}
merchant_by_seg={seg:merchant[merchant.merchant_segment==seg].index.values for seg in msegments}
m_idx=[]
for seg,c in zip(mseg_choices,country_choices):
    arr=merchant_groups[(seg,c)]
    if len(arr)==0: arr=merchant_by_seg[seg]
    m_idx.append(np.random.choice(arr))
m_idx=np.array(m_idx); mdf=merchant.iloc[m_idx].reset_index(drop=True)
# sample customer by country
cust_groups={c:cust[cust.country==c].index.values for c in countries}; cust_idx=np.array([np.random.choice(cust_groups[c]) for c in mdf.country]); cdf=cust.iloc[cust_idx].reset_index(drop=True)
# native amounts from usd lognormal
means={'SME':3.1,'Enterprise':3.55,'Strategic':4.0}; usd=np.array([np.random.lognormal(means[s],.75) for s in mdf.merchant_segment]); usd=np.clip(usd,3,4500); currency=mdf.country.map(cur_by).values; native=np.array([usd[i]/base_rates[currency[i]] for i in range(n)])
rev_mask=np.random.rand(n)<.007; zero_mask=(np.random.rand(n)<.004)&(~rev_mask); native[rev_mask]*=-np.random.uniform(.2,1.0,rev_mask.sum()); native[zero_mask]=0
# channels/routes/status
ch=[]; route=[]
for c,t in zip(mdf.country,created):
    if c=='India': ch.append(np.random.choice(channels,p=[.44,.36,.14,.06])); route.append(np.random.choice(['R_IN_01','R_IN_02'],p=[.70,.30] if t<pd.Timestamp('2026-04-01') else [.48,.52]))
    elif c=='Singapore': ch.append(np.random.choice(channels,p=[.62,0,.22,.16])); route.append(np.random.choice(['R_SG_01','R_SG_02'],p=[.72,.28] if t<pd.Timestamp('2026-04-01') else [.41,.59]))
    else: ch.append(np.random.choice(channels,p=[.57,0,.20,.23])); route.append(np.random.choice(['R_UAE_01','R_UAE_02'],p=[.74,.26] if t<pd.Timestamp('2026-04-01') else [.42,.58]))
route=np.array(route); ch=np.array(ch)
base_success=np.full(n,.895); base_success-=np.where(mdf.risk_tier.values=='High',.065,0); base_success-=np.where(mdf.pricing_plan.values=='High Risk',.035,0); base_success-=np.where(late,.028,0); base_success-=np.where(np.isin(route,['R_SG_02','R_UAE_02'])&late,.032,0); base_success-=np.where((route=='R_IN_02')&(created>=pd.Timestamp('2026-05-01'))&(created<pd.Timestamp('2026-06-01')),.045,0)
rnd=np.random.rand(n); status=np.where(rnd<base_success,'SUCCESS',np.where(rnd<base_success+.055,'DECLINED_FRAUD',np.where(rnd<base_success+.085,'FAILED_TECHNICAL','CANCELLED')))
tx=pd.DataFrame({'transaction_id':[f'T{i:08d}' for i in range(1,n+1)],'customer_id':cdf.customer_id,'merchant_id':mdf.merchant_id,'amount':np.round(native,2),'currency':currency,'channel':ch,'status':status,'created_at':created,'route_id':route})
miss_idx=np.random.choice(tx.index,int(.014*n),replace=False); tx.loc[miss_idx,'merchant_id']=np.nan
dup=tx.sample(70,random_state=22).copy(); dup['created_at']=pd.to_datetime(dup['created_at'])+pd.to_timedelta(np.random.randint(1,60,len(dup)),unit='s'); tx_full=pd.concat([tx,dup],ignore_index=True); tx_full.to_csv(data_dir/'transaction.csv',index=False)
# events vector loop ok 75k
events=[]
for tid,t,st,rt in zip(tx.transaction_id, tx.created_at, tx.status, tx.route_id):
    events.append([tid,'CREATED',t,t+pd.Timedelta(minutes=np.random.randint(0,20)),None])
    b=np.random.normal(420,130)
    if rt=='R_IN_02' and pd.Timestamp('2026-05-01')<=t<pd.Timestamp('2026-06-01'): b=np.random.normal(1850,420)
    if rt in ['R_SG_02','R_UAE_02'] and t>=pd.Timestamp('2026-04-01'): b*=1.45
    b=max(70,b); et=t+pd.Timedelta(milliseconds=b); delay=np.random.exponential(.7)+(np.random.uniform(72,168) if np.random.rand()<.028 else 0)
    events.append([tid,'AUTHORIZED' if st=='SUCCESS' else 'DECISIONED',et,et+pd.Timedelta(hours=delay),int(b)])
    if st=='SUCCESS':
        pt=et+pd.Timedelta(milliseconds=max(80,np.random.normal(b*.8,120))); events.append([tid,'CAPTURED',pt,pt+pd.Timedelta(hours=np.random.exponential(.4)),int(max(80,np.random.normal(b*.8,120)))])
        if np.random.rand()<.82: events.append([tid,'SETTLED',pt+pd.Timedelta(days=np.random.randint(1,4)),pt+pd.Timedelta(days=np.random.randint(1,4),hours=np.random.exponential(1.2)),None])
    else: events.append([tid,'FAILED',et+pd.Timedelta(milliseconds=100),et+pd.Timedelta(hours=np.random.exponential(.5)),None])
payment_event=pd.DataFrame(events,columns=['transaction_id','event_type','event_time','processing_ms','ingestion_time'])
# Fix column order actually event_time, ingestion_time, processing_ms
payment_event=payment_event.rename(columns={'processing_ms':'ingestion_time','ingestion_time':'processing_ms'})
payment_event.to_csv(data_dir/'payment_event.csv',index=False)
# fraud
fd=[]
for tid,st,rtier,dt in zip(tx.transaction_id,tx.status,mdf.risk_tier,tx.created_at):
    if np.random.rand()<.018: continue
    mean={'Low':.22,'Medium':.47,'High':.71}[rtier]; score=np.clip(np.random.normal(mean,.17),0,1)
    if np.random.rand()<.009: score=np.random.choice([-.18,1.12,1.35])
    decision='DECLINE' if st=='DECLINED_FRAUD' else ('REVIEW' if score>.82 and np.random.rand()<.35 else 'APPROVE')
    fd.append([tid,np.random.choice(['velocity','geo_mismatch','new_device','amount_spike','watchlist','none'],p=[.18,.14,.20,.17,.07,.24]),decision,round(float(score),4),'v1.8' if dt<pd.Timestamp('2026-04-15') else 'v2.0'])
fraud=pd.DataFrame(fd,columns=['transaction_id','rule_id','decision','risk_score','model_version']); fraud.to_csv(data_dir/'fraud_decision.csv',index=False)
# settlements
sett=[]; succ=tx[tx.status=='SUCCESS'].copy()
for _,r in succ.iterrows():
    if np.random.rand()<.035: continue
    splits=2 if np.random.rand()<.026 else 1; stat=np.random.choice(['SETTLED','PENDING','EXCEPTION'],p=[.925,.04,.035])
    for s in range(splits):
        part=r.amount/splits; fee=abs(part)*np.random.uniform(.001,.0032)+np.random.uniform(.02,.12); sdate=(r.created_at+pd.Timedelta(days=np.random.randint(1,6))).date(); sett.append([f'SET{len(sett)+1:08d}',r.transaction_id,round(part,2),r.currency,round(fee,2),stat,sdate])
    if np.random.rand()<.006:
        sett.append([f'SET{len(sett)+1:08d}',r.transaction_id,round(r.amount,2),r.currency,round(abs(r.amount)*np.random.uniform(.001,.0032)+np.random.uniform(.02,.12),2),'SETTLED',(r.created_at+pd.Timedelta(days=np.random.randint(1,6))).date()])
settlement=pd.DataFrame(sett,columns=['settlement_id','transaction_id','settlement_amount','settlement_currency','fee_amount','settlement_status','settlement_date']); settlement.to_csv(data_dir/'settlement.csv',index=False)
# chargebacks
cb=[]; tx_m=tx.merge(merchant,on='merchant_id',how='left',suffixes=('','_m'))
for _,r in tx_m[tx_m.status=='SUCCESS'].iterrows():
    p=.008 if r.created_at<pd.Timestamp('2026-04-01') else .014
    if r.risk_tier=='High': p*=2.2
    if r.category in ['Travel','Electronics']: p*=1.45
    if np.random.rand()<p:
        op=r.created_at+pd.Timedelta(days=np.random.randint(7,45)); res=op+pd.Timedelta(days=np.random.randint(10,60)) if np.random.rand()<.72 else pd.NaT
        cb.append([f'CB{len(cb)+1:07d}',r.transaction_id,np.random.choice(['fraud','service_not_received','duplicate','customer_dispute'],p=[.40,.26,.12,.22]),round(abs(r.amount)*np.random.uniform(.55,1.0),2),op.date(),'' if pd.isna(res) else res.date()])
chargeback=pd.DataFrame(cb,columns=['chargeback_id','transaction_id','reason','amount','opened_at','resolved_at']); chargeback.to_csv(data_dir/'chargeback.csv',index=False)
# merchant risk snapshot
mrs=[]; months=pd.date_range('2026-01-01','2026-06-01',freq='MS')
for _,m in merchant.iterrows():
    base_score={'Low':.22,'Medium':.52,'High':.76}[m.risk_tier]
    for mo in months:
        score=np.clip(np.random.normal(base_score,.08)+(.04 if mo>=pd.Timestamp('2026-04-01') and m.merchant_segment=='SME' else 0),.01,.99); band='Low' if score<.35 else 'Medium' if score<.67 else 'High'
        mrs.append([m.merchant_id,mo.date(),round(float(score),4),band])
        if np.random.rand()<.018:
            score2=np.clip(score+np.random.normal(0,.02),.01,.99); band2='Low' if score2<.35 else 'Medium' if score2<.67 else 'High'; mrs.append([m.merchant_id,mo.date(),round(float(score2),4),band2])
mr=pd.DataFrame(mrs,columns=['merchant_id','snapshot_month','risk_score','risk_band']); mr.to_csv(data_dir/'merchant_risk_snapshot.csv',index=False)
# Governed model
pricing_rates={'Standard':.019,'Growth':.015,'Enterprise':.022,'Promotional':.011,'High Risk':.026}; pricing_fixed={'Standard':.02,'Growth':.01,'Enterprise':.03,'Promotional':0,'High Risk':.05}
fx_spot=fx[fx.rate_type=='SPOT'].copy(); fx_spot['rate_date']=pd.to_datetime(fx_spot.rate_date)
model=tx.copy(); model['created_at']=pd.to_datetime(model.created_at); model['txn_date']=model.created_at.dt.normalize(); model=model.merge(fx_spot,left_on=['txn_date','currency'],right_on=['rate_date','currency'],how='left'); model['amount_usd']=model.amount*model.rate_to_usd
model=model.merge(merchant,on='merchant_id',how='left',suffixes=('','_merchant'))
model['merchant_fee_usd']=np.where(model.status=='SUCCESS',abs(model.amount_usd)*model.pricing_plan.map(pricing_rates).fillna(.018)+model.pricing_plan.map(pricing_fixed).fillna(.02),0)
route_cost['cost_date']=pd.to_datetime(route_cost.cost_date); model=model.merge(route_cost,left_on=['route_id','txn_date'],right_on=['route_id','cost_date'],how='left'); model['processing_cost_usd']=model.fixed_fee.fillna(0)+abs(model.amount_usd)*model.variable_fee_pct.fillna(0)
sett_calc=settlement.copy(); sett_calc['settlement_date']=pd.to_datetime(sett_calc.settlement_date); sett_calc=sett_calc.merge(fx_spot,left_on=['settlement_date','settlement_currency'],right_on=['rate_date','currency'],how='left'); sett_calc['settlement_fee_usd']=abs(sett_calc.fee_amount)*sett_calc.rate_to_usd
sett_agg=sett_calc.groupby('transaction_id').agg(settlement_fee_usd=('settlement_fee_usd','sum'),settlement_count=('settlement_id','count')).reset_index(); model=model.merge(sett_agg,on='transaction_id',how='left'); model['settlement_fee_usd']=model.settlement_fee_usd.fillna(0)
cb_calc=chargeback.merge(model[['transaction_id','rate_to_usd']],on='transaction_id',how='left'); cb_calc['chargeback_cost_usd']=abs(cb_calc.amount)*cb_calc.rate_to_usd; cb_agg=cb_calc.groupby('transaction_id').agg(chargeback_cost_usd=('chargeback_cost_usd','sum'),chargeback_count=('chargeback_id','count')).reset_index(); model=model.merge(cb_agg,on='transaction_id',how='left'); model['chargeback_cost_usd']=model.chargeback_cost_usd.fillna(0)
fx_acct=fx[fx.rate_type=='ACCOUNTING'].copy(); fx_acct['rate_date']=pd.to_datetime(fx_acct.rate_date); acct=model[['transaction_id','txn_date','currency','amount']].merge(fx_acct,left_on=['txn_date','currency'],right_on=['rate_date','currency'],how='left'); acct['acct_usd']=acct.amount*acct.rate_to_usd; model=model.merge(acct[['transaction_id','acct_usd']],on='transaction_id',how='left'); model['fx_impact_usd']=np.where(model.status=='SUCCESS',(model.amount_usd-model.acct_usd).fillna(0),0)
model['fraud_control_cost_usd']=np.where(model.status=='DECLINED_FRAUD',abs(model.amount_usd)*.0025,0); model['contribution_profit_usd']=model.merchant_fee_usd-model.processing_cost_usd-model.settlement_fee_usd-model.chargeback_cost_usd-model.fraud_control_cost_usd+model.fx_impact_usd; model['successful_txn']=(model.status=='SUCCESS').astype(int); model['period']=np.where(model.created_at<pd.Timestamp('2026-04-01'),'Baseline Jan-Mar','Deterioration Apr-Jun')
(base/'05_profitability_model').mkdir(exist_ok=True); model.to_csv(base/'05_profitability_model'/'transaction_profitability_model.csv',index=False)
# summaries
val=base/'validation'; val.mkdir(exist_ok=True)
summary={'transaction_rows':len(tx_full),'unique_transactions':tx_full.transaction_id.nunique(),'duplicate_transaction_id_rows':len(tx_full)-tx_full.transaction_id.nunique(),'missing_merchant_id':int(tx_full.merchant_id.isna().sum()),'zero_or_negative_amount':int((tx_full.amount<=0).sum()),'fraud_rows':len(fraud),'fraud_score_outside_0_1':int(((fraud.risk_score<0)|(fraud.risk_score>1)).sum()),'late_events_over_3_days':int(((pd.to_datetime(payment_event.ingestion_time)-pd.to_datetime(payment_event.event_time)).dt.total_seconds()/86400>3).sum()),'successful_transactions':int((tx.status=='SUCCESS').sum()),'settlement_rows':len(settlement),'successful_tx_without_settlement':int((tx.status=='SUCCESS').sum()-settlement.transaction_id.nunique()),'transactions_with_multiple_settlements':int((settlement.transaction_id.value_counts()>1).sum()),'fx_rate_duplicate_types':int(fx.groupby(['rate_date','currency']).rate_type.nunique().gt(1).sum()),'merchant_month_duplicate_snapshot_rows':int(mr.duplicated(['merchant_id','snapshot_month'],keep=False).sum()),'chargeback_rows':len(chargeback)}
pd.DataFrame(summary.items(),columns=['metric','value']).to_csv(val/'data_quality_counts.csv',index=False)
period=model.groupby('period').agg(attempted=('transaction_id','count'),successful=('successful_txn','sum'),gross_payment_value_usd=('amount_usd',lambda s: s[model.loc[s.index,'status'].eq('SUCCESS')].sum()),merchant_fee_usd=('merchant_fee_usd','sum'),processing_cost_usd=('processing_cost_usd','sum'),settlement_fee_usd=('settlement_fee_usd','sum'),chargeback_cost_usd=('chargeback_cost_usd','sum'),fraud_control_cost_usd=('fraud_control_cost_usd','sum'),fx_impact_usd=('fx_impact_usd','sum'),contribution_profit_usd=('contribution_profit_usd','sum')).reset_index(); period['success_rate']=period.successful/period.attempted; period['cp_per_success_txn']=period.contribution_profit_usd/period.successful; period.to_csv(val/'period_kpi_summary.csv',index=False)
# monthly summary
monthly=model.groupby(model.created_at.dt.to_period('M').astype(str)).agg(attempted=('transaction_id','count'),successful=('successful_txn','sum'),contribution_profit_usd=('contribution_profit_usd','sum'),processing_cost_usd=('processing_cost_usd','sum'),merchant_fee_usd=('merchant_fee_usd','sum')).reset_index().rename(columns={'created_at':'month'}); monthly['cp_per_success_txn']=monthly.contribution_profit_usd/monthly.successful; monthly.to_csv(val/'monthly_kpi_summary.csv',index=False)
for dim in ['merchant_segment','category','country','channel','provider','route_id','risk_tier','pricing_plan']:
    g=model.groupby(['period',dim],dropna=False).agg(successful=('successful_txn','sum'),attempted=('transaction_id','count'),profit=('contribution_profit_usd','sum'),proc=('processing_cost_usd','sum'),fees=('merchant_fee_usd','sum')).reset_index(); g['cp_per_success']=g.profit/g.successful.replace(0,np.nan); piv=g.pivot(index=dim,columns='period',values=['successful','attempted','profit','proc','fees','cp_per_success']).fillna(0); piv.columns=['_'.join(col) for col in piv.columns]; piv=piv.reset_index();
    if 'cp_per_success_Baseline Jan-Mar' in piv.columns:
        piv['delta_cp_per_success']=piv['cp_per_success_Deterioration Apr-Jun']-piv['cp_per_success_Baseline Jan-Mar']; piv['deterioration_contribution_usd']=piv['delta_cp_per_success']*piv['successful_Deterioration Apr-Jun']; piv=piv.sort_values('deterioration_contribution_usd')
    piv.to_csv(val/f'root_cause_by_{dim}.csv',index=False)
# mix decomp by merchant segment
seg=model.groupby(['period','merchant_segment']).agg(successful=('successful_txn','sum'),profit=('contribution_profit_usd','sum')).reset_index(); seg['rate']=seg.profit/seg.successful; totals=seg.groupby('period').successful.sum().to_dict(); wide=seg.pivot(index='merchant_segment',columns='period',values=['successful','rate']).fillna(0); wide.columns=['_'.join(col) for col in wide.columns]; wide=wide.reset_index(); wide['share_Baseline']=wide['successful_Baseline Jan-Mar']/totals['Baseline Jan-Mar']; wide['share_Deterioration']=wide['successful_Deterioration Apr-Jun']/totals['Deterioration Apr-Jun']; wide['mix_effect_per_txn']=(wide['share_Deterioration']-wide['share_Baseline'])*wide['rate_Baseline Jan-Mar']; wide['within_effect_per_txn']=wide['share_Deterioration']*(wide['rate_Deterioration Apr-Jun']-wide['rate_Baseline Jan-Mar']); wide.to_csv(val/'mix_decomposition_merchant_segment.csv',index=False)
print('OK generated')
print(pd.DataFrame(summary.items(),columns=['metric','value']))
print(period)
