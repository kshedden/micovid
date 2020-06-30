import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
import matplotlib.dates as mdates
import json
import gzip

months = mdates.MonthLocator(interval=3)
months_fmt = mdates.DateFormatter("%b %Y")

with gzip.open("/nfs/kshedden/Daniel_Keyes/counts.json.gz") as gid:
    dc = json.load(gid)

# Maximum time index (day within 2020)
mxt = 365 * 2

hi = pd.read_csv("/nfs/kshedden/Daniel_Keyes/hospital_info.csv")

hg1 = [x for x,y in zip(hi.LOCATIONID, hi.RUCC) if y <= 2 and x in dc.keys()]
hg2 = [x for x,y in zip(hi.LOCATIONID, hi.RUCC) if y > 2 and x in dc.keys()]
hg2.remove("OWOSSO")
hg0 = hg1 + hg2

outname = "volume_agg.pdf"
pdf = PdfPages("volume_agg.pdf")

px = []
for ky in dc.keys():
	px.append(ky.split(":")[0])
px = list(set(px))
px.sort()

col = {"Trauma": "blue", "Total": "black", "Pediatric": "orange", "Flu": "red"}

tr = {"Trauma": "Trauma", "Total": "Total", "Pediatric": "Pediatric", "Flu": "Covid-like"}

xsum = []

for jh, hg in enumerate([hg0, hg1, hg2]):
    for smooth in False, True:

        plt.clf()
        plt.figure(figsize=(8, 5))
        plt.axes([0.1, 0.1, 0.73, 0.8])
        plt.grid(True)

        plt.axvline(pd.to_datetime("2020-03-11"), color="grey", ls="--")

        for cx in ["Total", "Trauma", "Flu", "Pediatric"]:

            y = np.zeros(mxt)
            for loc in hg:
                try:
                    dch = dc[loc]
                except KeyError:
                    continue
                for sex in "Female", "Male":
                    dq = dch[sex]
                    da = dq["Datex"]
                    da = [x[0:10] for x in da]
                    ii = [i for i,x in enumerate(da) if x != "0001-01-01"]
                    da = [da[i] for i in ii]
                    dx = [dq[cx][i] for i in ii]
                    da = pd.to_datetime(da)
                    day = da - pd.to_datetime("2019-01-01")
                    day = day.days.tolist()
                    y[day] += dx

            if smooth:
                oo = np.ones(len(y))
                oo = np.convolve(oo, np.ones(7), mode='same')
                y = np.convolve(y, np.ones(7), mode='same')
                y /= oo

            du = pd.DataFrame({"Count": y})
            du.loc[:, "Date"] = pd.to_datetime("2019-01-01") + pd.to_timedelta(np.arange(mxt), 'd')
            du = du.loc[du.Date <= pd.to_datetime("2020-06-01")]

            if smooth:
                dz = du.copy()
                dz.loc[dz.Date < pd.to_datetime("2020-03-11"), "Count"] = np.Inf
                i0 = dz.Count.idxmin()
                dz.loc[dz.Date < pd.to_datetime("2020-03-11"), "Count"] = -np.Inf
                i1 = dz.Count.idxmax()
                row = [cx, dz.loc[i0, "Date"], dz.loc[i0, "Count"], dz.loc[i1, "Date"], dz.loc[i1, "Count"]]
                xsum.append(row)

            plt.plot(du.Date, du.Count, label=tr[cx], color=col[cx], alpha=0.6)

        ha, lb = plt.gca().get_legend_handles_labels()
        leg = plt.figlegend(ha, lb, "center right")
        leg.draw_frame(False)
        plt.gca().xaxis.set_major_locator(months)
        plt.gca().xaxis.set_major_formatter(months_fmt)
        plt.xlim(pd.to_datetime("2018-12-31"), pd.to_datetime("2020-06-01"))
        plt.xlabel("Date", size=14)
        plt.ylabel("Daily ED visits", size=14)
        plt.ylim(ymin=0)
        if jh == 0:
            plt.title("All EDs (%d)" % len(hg))
        elif jh == 1:
            plt.title("Urban EDs (%d)" % len(hg))
        else:
            plt.title("Non-urban EDs (%d)" % len(hg))
        pdf.savefig()

pdf.close()

xsum = pd.DataFrame(xsum)
xsum.columns = ["Subgroup", "Nadir_date", "Nadir", "Peak_date", "Peak"]
xsum.to_csv(outname.replace(".pdf", ".txt"), index=None)