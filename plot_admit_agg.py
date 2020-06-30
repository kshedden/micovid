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

out = open(outname.replace(".pdf", ".txt"), "w")
pdf = PdfPages(outname)

px = []
for ky in dm.keys():
	px.append(ky.split(":")[0])
px = list(set(px))
px.sort()

plt.clf()
plt.figure(figsize=(8, 5))
plt.axes([0.1, 0.1, 0.64, 0.8])
plt.grid(True)

for jh, hg in enumerate([hg0, hg1, hg2]):

    y = np.zeros((mxt+1, 2))
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

            du1 = np.asarray(du1).T
            du2 = np.asarray(du2).T

            assert(np.all(du1[:, 0] == du2[:, 0]))

            day = np.asarray(du1[:, 0]).astype(np.int) - 1
            rat = np.exp(du1[:, 1] - du2[:, 1])
            y[day, 0] += w*rat
            y[day, 1] += w

    y[:, 0] /= y[:, 1]
    du = pd.DataFrame({"Ratio": y[:, 0]})
    du.loc[:, "Date"] = pd.to_datetime("2020-01-01") + pd.to_timedelta(np.arange(mxt+1), 'd')
    du = du.loc[du.Date < pd.to_datetime("2020-06-01"), :]

    ii = du.Ratio.idxmax()
    r = du.loc[ii, :]
    out.write("%-10s   %10s   %10.2f\n" % (subsets[jh], r.Date.isoformat()[0:10], r.Ratio))

    lab = ["All EDs (%d)" % len(hg0), "Urban EDs (%d)" % len(hg1), "Non-urban EDs (%d)" % len(hg2)][jh]
    plt.plot(du.Date, du.Ratio, label=lab)

ha, lb = plt.gca().get_legend_handles_labels()
leg = plt.figlegend(ha, lb, "center right")
leg.draw_frame(False)
plt.gca().xaxis.set_major_locator(months)
plt.gca().xaxis.set_major_formatter(months_fmt)
plt.xlabel("Date (2020)", size=14)
plt.ylabel("Admission rate relative to 2019", size=14)
pdf.savefig()

pdf.close()
out.close()
