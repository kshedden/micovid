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

with gzip.open("/nfs/kshedden/Daniel_Keyes/counts.json.gz") as gid:
    dc = json.load(gid)

# Maximum time index (day within 2020)
mxt = max([max(np.max(x[0]), np.max(x[1])) for x in dm.values()])

wgt = {}
for c in dc:
    for sex in "Female", "Male":
        da = np.asarray(dc[c][sex]["Date"])
        ii = (da != "0001-01-01")
        dx = np.asarray(dc[c][sex]["Datex"])[ii]
        dx = pd.to_datetime(dx)
        ct = np.asarray(dc[c][sex]["Total"])[ii]
        ii = dx.year == 2019
        wgt[c + ":" + sex] = ct.sum()

with open("/nfs/kshedden/Daniel_Keyes/counts.json.gz") as fid:
    hi = pd.read_csv("/nfs/kshedden/Daniel_Keyes/hospital_info.csv")

hg1 = [x for x,y in zip(hi.LOCATIONID, hi.RUCC) if y <= 2 and x in dc.keys()]
hg2 = [x for x,y in zip(hi.LOCATIONID, hi.RUCC) if y > 2 and x in dc.keys()]
hg2.remove("OWOSSO")
hg0 = hg1 + hg2

outname = "ratios_agg.pdf"
pdf = PdfPages("ratios_agg.pdf")

px = []
for ky in dm.keys():
	px.append(ky.split(":")[0])
px = list(set(px))
px.sort()

col = {"Trauma": "blue", "Total": "black", "Pediatric": "orange", "Flu": "red"}

tr = {"Trauma": "Trauma", "Total": "Total", "Pediatric": "Pediatric", "Flu": "Covid-like"}

subsets = ["All", "Urban", "NonUrban"]

out = open(outname.replace(".pdf", ".txt"), "w")

sumx = []

for jh, hg in enumerate([hg0, hg1, hg2]):

    plt.clf()
    plt.axes([0.1, 0.1, 0.69, 0.8])
    plt.grid(True)

    plt.axvline(pd.to_datetime("2020-03-11"), color="grey", ls="--")

    for cx in ["Total", "Pediatric", "Trauma", "Flu"]:

        y = np.zeros((mxt+1, 2))
        for loc in hg:
            for sex in "Female", "Male":
                wk = "%s:%s" % (loc, sex)
                if wk not in wgt:
                    continue
                w = wgt[wk]
                ky = "%s:%s:%s" % (loc, sex, cx)
                if ky not in dm:
                    continue
                du = dm[ky]
                day = np.asarray(du[0]) - 1
                rat = np.asarray(du[1])
                y[day, 0] += w*rat
                y[day, 1] += w

        y[:, 0] /= y[:, 1]
        du = pd.DataFrame({"Ratio": y[:, 0]})
        du.loc[:, "Date"] = pd.to_datetime("2020-01-01") + pd.to_timedelta(np.arange(mxt+1), 'd')
        du = du.loc[du.Date < pd.to_datetime("2020-06-01"), :]

        ii = du.Ratio.idxmin()
        r0 = du.loc[ii, :]
        r1 = du.iloc[-1, :]
        sumx.append([subsets[jh], cx, r0.Date.isoformat()[0:10], np.exp(r0.Ratio), np.exp(r1.Ratio)])

        plt.plot(du.Date, np.exp(du.Ratio), label=tr[cx], color=col[cx], alpha=0.6)

    ha, lb = plt.gca().get_legend_handles_labels()
    leg = plt.figlegend(ha, lb, "center right")
    leg.draw_frame(False)
    plt.gca().xaxis.set_major_locator(months)
    plt.gca().xaxis.set_major_formatter(months_fmt)
    plt.xlabel("Date (2020)", size=14)
    plt.ylabel("Patient volume relative to 2019", size=14)
    plt.ylim(ymin=0)
    if jh == 0:
        plt.title("All EDs (%d)" % len(hg))
    elif jh == 1:
        plt.title("Urban EDs (%d)" % len(hg))
    else:
        plt.title("Non-urban EDs (%d)" % len(hg))
    pdf.savefig()

pdf.close()

sumx = pd.DataFrame(sumx)
sumx.columns = ["Location", "Subgroup", "Nadir_date", "Nadir_ratio", "May31_ratio"]
sumx.to_csv(outname.replace(".pdf", ".txt"), index=None)