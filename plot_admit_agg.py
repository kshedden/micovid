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

subsets = ["All", "Urban", "NonUrban"]

outname = "admit_ratios_agg.pdf"

pdf = PdfPages(outname)

sumx = []

px = []
for ky in dm.keys():
	px.append(ky.split(":")[0])
px = list(set(px))
px.sort()


for jh, hg in enumerate([hg0, hg1, hg2]):

    plt.clf()
    plt.figure(figsize=(8, 5))
    plt.axes([0.1, 0.1, 0.64, 0.8])
    plt.grid(True)

    y = np.zeros((mxt+1, 3))
    moulton = []
    for loc in hg:
        for sex in "Female", "Male":
            wk = "%s:%s" % (loc, sex)
            if wk not in wgt:
                continue
            w = wgt[wk]

            ky1 = "%s:%s:%s" % (loc, sex, "Admit")
            if ky1 not in dm:
                continue
            du1 = dm[ky1]

            ky2 = "%s:%s:%s" % (loc, sex, "Total")
            if ky2 not in dm:
                continue
            du2 = dm[ky2]

            assert(np.all(du1[0] == du2[0]))

            day = np.asarray(du1[0]).astype(np.int) - 1
            rat = np.asarray(du1[1]) - np.asarray(du2[1])
            rat_se = np.sqrt(np.asarray(du1[2])**2 + np.asarray(du2[2])**2)
            y[day, 0] += w*rat
            y[day, 1] += w
            y[day, 2] += (w * rat_se)**2
            cc = (du1[3][0] + du2[3][0]) / 2
            moulton.append(np.sqrt(1 + len(day)*np.clip(cc, 0, np.inf)))
            print(np.median(moulton))

    y[:, 0] /= y[:, 1]
    y[:, 2] /= y[:, 1]**2
    y[:, 2] = np.sqrt(y[:, 2]) * np.median(moulton)
    du = pd.DataFrame({"Ratio": y[:, 0], "RatioSE": y[:, 2]})
    du.loc[:, "Date"] = pd.to_datetime("2020-01-01") + pd.to_timedelta(np.arange(mxt+1), 'd')
    du = du.loc[du.Date < pd.to_datetime("2020-06-01"), :]

    ii = du.Ratio.idxmax()
    r = du.loc[ii, :]
    sumrow = [subsets[jh], r.Date.isoformat()[0:10],
              np.exp(r.Ratio), np.exp(r.Ratio - 2*r.RatioSE), np.exp(r.Ratio + 2*r.RatioSE)]
    sumx.append(sumrow)

    lab = ["All EDs (%d)" % len(hg0), "Urban EDs (%d)" % len(hg1), "Non-urban EDs (%d)" % len(hg2)][jh]
    plt.title(lab)

    plt.plot(du.Date, np.exp(du.Ratio))

    plt.gca().xaxis.set_major_locator(months)
    plt.gca().xaxis.set_major_formatter(months_fmt)
    plt.xlabel("Date (2020)", size=14)
    plt.ylabel("Admission rate relative to 2019", size=14)
    pdf.savefig()

pdf.close()

sumx = pd.DataFrame(sumx)
sumx.columns = ["Location", "Peak_date", "Peak_ratio", "Peak_ratio_lcb", "Peak_ratio_ucb"]
sumx.to_csv(outname.replace(".pdf", ".txt"), index=None, float_format="%.4f")
