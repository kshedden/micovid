import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
import json
import gzip

with gzip.open("/nfs/kshedden/Daniel_Keyes/counts.json.gz") as gid:
    dm = json.load(gid)


def facvol(smooth, sex, fname):

    pdf = PdfPages(fname)

    for loc in dm.keys():

        female = dm[loc]["Female"]
        male = dm[loc]["Male"]
        dff = []
        for ju, u in enumerate([female, male]):
            df = pd.DataFrame(u)
            df = df.loc[:, ["Date", "Total", "Flu", "Trauma", "Pediatric"]]
            dff.append(df)

        if sex == "female":
            df = dff[0]
        elif sex == "male":
            df = dff[1]
        else:
            df = dff[0]
            for c in ["Total", "Flu", "Trauma", "Pediatric"]:
                df[c] += dff[1][c]

        df = df.loc[df.Date != "0001-01-01", :]
        df.Date = pd.to_datetime(df.Date)

        plt.clf()
        plt.figure(figsize=(9, 6))
        plt.axes([0.1, 0.15, 0.76, 0.8])
        plt.grid(True)

        if smooth:
            oo = np.ones(df.shape[0])
            ox = np.ones(7)
            nn = np.convolve(oo, ox, mode='same')
            df.Total = np.convolve(df.Total, ox, mode='same') / nn
            df.Flu = np.convolve(df.Flu, ox, mode='same') / nn
            df.Trauma = np.convolve(df.Trauma, ox, mode='same') / nn
            df.Pediatric = np.convolve(df.Pediatric, ox, mode='same') / nn

        plt.axvline(pd.to_datetime("2020-03-11"), color="grey", ls="--")

        plt.plot(df.Date, df.Total, '-', label="Total", color='black', alpha=0.6)
        plt.plot(df.Date, df.Flu, '-', label="Flu-like", color="red", alpha=0.6)
        plt.plot(df.Date, df.Trauma, '-', label="Trauma", color="blue", alpha=0.6)
        plt.plot(df.Date, df.Pediatric, '-', label="Pediatric", color="orange", alpha=0.6)

        ha, lb = plt.gca().get_legend_handles_labels()
        leg = plt.figlegend(ha, lb, "center right")
        leg.draw_frame(False)

        plt.ylabel("Patients per day", size=15)
        if sex == "all":
            plt.title("%s" % loc)
        else:
            plt.title("%s -- %s" % (loc, sex))

        for x in plt.gca().get_xticklabels():
            x.set_rotation(60)

        pdf.savefig()

    pdf.close()

facvol(False, "all", "facility_volume_raw.pdf")
facvol(True, "all", "facility_volume_smooth.pdf")