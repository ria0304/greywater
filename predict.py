"""Greywater reuse classifier demo. Usage: python3 predict.py 7.2 5 320 0"""
import sys, pickle, pandas as pd
m = pickle.load(open("greywater_model.pkl","rb"))
cols = ["pH","turbidity_NTU","TDS_mgL","microbial_present"]
v = [float(x) for x in sys.argv[1:5]] if len(sys.argv)==5 else [7.2,5,320,0]
pred = m.predict(pd.DataFrame([v], columns=cols))[0]
print({0:"safe_garden",1:"safe_flushing_only",2:"unsafe"}[pred])
