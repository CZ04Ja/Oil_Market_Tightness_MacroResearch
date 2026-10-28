"""Synthetic timing check; no market data or investment-performance claim."""
import json
import numpy as np
import pandas as pd
carry=pd.Series([2.,3.,4.,5.,3.,2.])
ma=carry.rolling(4).mean()
signal=pd.Series(np.where(carry>ma,1.,-1.)).where(ma.notna())
exposure=np.array([1/3]*3+[-1/3]*3)
w=signal.iloc[-1]*exposure
assert np.isclose(w.sum(),0) and np.isclose(abs(w).sum(),2)
assert signal.iloc[:3].isna().all()
prices=pd.Series([100.,110.,99.]);decision=pd.Series([1.,-1.,1.])
forward=prices.shift(-1)/prices-1
assert np.isclose((decision*forward).iloc[0],.1)
assert np.isclose((decision*forward).iloc[1],.1)
print(json.dumps({'synthetic':True,'net_exposure':float(w.sum()),'gross_exposure':float(abs(w).sum()),'warmup_and_forward_timing':'PASS'},indent=2))
