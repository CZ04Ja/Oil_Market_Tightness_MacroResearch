"""Local source audit and NEW timing reconstruction; not tradable futures/NDF PnL."""
from pathlib import Path
import ast,json
import numpy as np
import pandas as pd
ROOT=Path(__file__).resolve().parent
import argparse
parser=argparse.ArgumentParser()
parser.add_argument('--data-dir',type=Path,required=True)
parser.add_argument('--output',type=Path,default=Path('local_results'))
args=parser.parse_args()
BASE=args.data_dir
ROOT=args.output
ROOT.mkdir(parents=True,exist_ok=True)
nb=json.loads((BASE/'Finalised/AQMS_final.ipynb').read_text())
for c in nb['cells']:
    if c['cell_type']!='code':continue
    for node in ast.parse(''.join(c['source'])).body:
        if isinstance(node,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='BIN_ASSIGNMENTS' for t in node.targets):
            bins=ast.literal_eval(node.value)
fx=pd.read_csv(BASE/'Finalised/fx_data_final.csv',parse_dates=['Date'],index_col='Date').loc[:'2025-12-31']
sig=pd.read_csv(BASE/'Finalised/Signal_Carry_CarryMom_Thursday.csv',parse_dates=['Date'],index_col='Date').loc[fx.index]
assert fx.index.is_unique and fx.index.is_monotonic_increasing and (fx>0).all().all()
prices=[]
for name in ['CO3','CO12']:
    d=pd.read_excel(BASE/f'COMDTY/Daily/{name}_COMDTY_daily.xlsx',skiprows=6).set_index('Date').sort_index()
    prices.append(d.PX_LAST)
rebuilt=[]
for date in fx.index:
    for days in [1,2,3]:
        source=date-pd.Timedelta(days=days)
        values=[p.get(source,np.nan) for p in prices]
        if all(pd.notna(values)):
            rebuilt.append([date,source,*values]);break
    else:raise ValueError(f'No source price before {date}')
rebuilt=pd.DataFrame(rebuilt,columns=['Date','SourceDate','CO3','CO12']).set_index('Date')
assert np.allclose(rebuilt[['CO3','CO12']],sig[['CO3','CO12']])
assert (rebuilt.SourceDate<rebuilt.index).all()
assert np.allclose(sig.CARRY,sig.CO3-sig.CO12)
assert np.allclose(sig.CARRY_MA4,sig.CARRY.rolling(4).mean(),equal_nan=True)
rebuilt.to_csv(ROOT/'oil_signal_source_dates.csv')
rawlog=np.log(fx/fx.shift())
result={'data_checks':{'weeks':len(fx),'daily_to_signal_exact_match':True,'wednesday_fallbacks':int((rebuilt.SourceDate.dt.dayofweek==2).sum()),'initial_momentum_without_ma':int(sig.CARRY_MA4.isna().sum())},'original_formula':{},'new_forward_proxy':{}}
for col in ['SIGNAL_CARRY','SIGNAL_CARRY_MOM']:
    weights=pd.DataFrame(0.,index=fx.index,columns=fx.columns)
    for date in fx.index:
        b=bins[date.year];s=sig.loc[date,col]
        weights.loc[date,b['top']]=s/3
        weights.loc[date,b['bottom']]=-s/3
    assert np.allclose(weights.sum(axis=1),0) and np.allclose(weights.abs().sum(axis=1),2)
    old=(weights*rawlog).sum(axis=1).iloc[1:]
    flip=sig[col].iloc[1:].ne(sig[col].iloc[1:].shift());flip.iloc[0]=False
    old-=flip*.001
    result['original_formula'][col]={'weeks':len(old),'annual_mean_pct':float(old.mean()*5200),'mean_vol_ratio':float(old.mean()/old.std()*np.sqrt(52))}
    # Each date is the Friday ENTRY date. Profit is next Friday / this Friday.
    fw=fx.shift(-1)/fx-1
    w=weights.copy()
    if col.endswith('MOM'):w.loc[sig.CARRY_MA4.isna()]=0.
    turnover=w.diff().abs().sum(axis=1);turnover.iloc[0]=w.iloc[0].abs().sum()
    gross=(w*fw).sum(axis=1,min_count=1)
    for bps in [0,2.5,5,10]:
        cost=turnover*bps/10000
        net=(gross-cost).iloc[:-1]
        nav=np.r_[1.,(1+net).cumprod().values]
        result['new_forward_proxy'][f'{col}_{bps}bps']={'weeks':len(net),'annual_mean_pct':float(net.mean()*5200),'mean_vol_ratio':float(net.mean()/net.std()*np.sqrt(52)),'cagr_pct':float((nav[-1]**(52/len(net))-1)*100),'max_drawdown_pct':float((nav/np.maximum.accumulate(nav)-1).min()*100),'turnover_sum':float(turnover.iloc[:-1].sum())}
    pd.DataFrame({'entry_date':fx.index,'exit_date':pd.Series(fx.index,index=fx.index).shift(-1),'gross_forward_proxy':gross,'turnover':turnover,'net_2_5bps':gross-turnover*.00025}).iloc[:-1].to_csv(ROOT/(col+'_forward_proxy.csv'),index=False)
# Unit test: changing this Friday's price must not change a PRIOR entry decision.
test_fx=pd.Series([100.,110.,99.]);test_s=pd.Series([1.,-1.,1.])
assert np.isclose((test_s*(test_fx.shift(-1)/test_fx-1)).iloc[0],.1)
assert np.isclose((test_s*(test_fx.shift(-1)/test_fx-1)).iloc[1],.1)
result['timing_unit_test']=True
result['limitations']=['same-year country bins remain retrospective','simple price returns are NOT properly rolled futures or NDF holding PnL','transaction costs are scenario assumptions, not executed quotes','no financing, margin cash return or execution model','turnover uses target-weight changes, not drift-adjusted executed holdings']
(ROOT/'oil_reproduction_results.json').write_text(json.dumps(result,indent=2,ensure_ascii=False))
print(json.dumps(result,indent=2,ensure_ascii=False))
