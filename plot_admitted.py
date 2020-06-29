import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
import matplotlib.dates as mdates
import json
import gzip

months = mdates.MonthLocator()
months_fmt = mdates.DateFormatter("%b")

with gzip.open("/nfs/kshedden/Daniel_Keyes/ratio_results.json.gz") as gid:
    dm = json.load(gid)

pdf = PdfPages("admit_ratios.pdf")

px = []
for ky in dm.keys():
	px.append(":".join(ky.split(":")[0:-1]))
px = list(set(px))
px.sort()

for kp in px:

    plt.clf()
    plt.figure(figsize=(7, 5))
    plt.axes([0.1, 0.11, 0.8, 0.8])
    plt.grid(True)

    try:
        dun = dm[kp + ":Admit"]
        dud = dm[kp + ":Total"]
    except KeyError:
        continue
    dun = np.asarray(dun).T
    dud = np.asarray(dud).T
    dd = pd.to_datetime("2020-01-01") + pd.to_timedelta(dun[:, 0], 'd')
    xt = ky.split(":")[-1]
    plt.plot(dd, np.exp(dun[:, 1] - dud[:, 1]), label=xt, color='black', alpha=0.6)

    plt.gca().xaxis.set_major_locator(months)
    plt.gca().xaxis.set_major_formatter(months_fmt)
    plt.xlabel("Date (2020)", size=14)
    plt.ylabel("Ratio relative to 2019", size=14)
    plt.ylim(ymin=0)
    ti = kp.split(":")
    ti[1] = ti[1].lower()
    plt.title(" ".join(ti) + "s")
    pdf.savefig()

pdf.close()
