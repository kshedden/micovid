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

outname = "facility_volume_ratios.pdf"
pdf = PdfPages(outname)

px = []
for ky in dm.keys():
	px.append(":".join(ky.split(":")[0:-1]))
px = list(set(px))
px.sort()

col = {"Trauma": "blue", "Total": "black", "Pediatric": "orange", "Flu": "red"}

sumx = []

for kp in px:

    plt.clf()
    plt.figure(figsize=(8, 5))
    plt.axes([0.1, 0.11, 0.74, 0.8])
    plt.grid(True)

    for ky in [x for x in dm.keys() if x.startswith(kp)]:
        if "Admit" in ky:
            continue
        du = dm[ky]
        du = np.asarray(du).T
        dd = pd.to_datetime("2020-01-01") + pd.to_timedelta(du[:, 0], 'd')
        ii = dd < pd.to_datetime("2020-06-01")
        dd = dd[ii]
        du = du[ii, :]
        xt = ky.split(":")[-1]
        plt.plot(dd, np.exp(du[:, 1]), label=xt, color=col[xt], alpha=0.6)

        i0 = np.argmin(du[:, 1])
        dux = du.copy()
        dux[dd < pd.to_datetime("2020-03-11"), 1] = -np.Inf
        i1 = np.argmax(dux[:, 1])
        sr = kp.split(":")
        sumx.append(sr + [xt, dd[i0].isoformat()[0:10], np.exp(du[i0,1]),
                          dd[i1].isoformat()[0:10], np.exp(du[i1,1]), np.exp(du[-1,1])])

    ha, lb = plt.gca().get_legend_handles_labels()
    leg = plt.figlegend(ha, lb, "center right")
    leg.draw_frame(False)
    plt.gca().xaxis.set_major_locator(months)
    plt.gca().xaxis.set_major_formatter(months_fmt)
    plt.xlabel("Date (2020)", size=14)
    plt.ylabel("Ratio relative to 2019", size=14)
    plt.ylim(ymin=0)
    ti = ky.split(":")[0:-1]
    ti[1] = ti[1].lower()
    plt.title(" ".join(ti) + "s")
    pdf.savefig()

pdf.close()

sumx = pd.DataFrame(sumx)
sumx.columns = ["Location", "Sex", "Subgroup", "Nadir_date", "Nadir_ratio", "Peak_date", "Peak_ratio", "May31_ratio"]
sumx.to_csv(outname.replace(".pdf", ".txt"), index=None)
