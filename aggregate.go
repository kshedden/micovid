package main

import (
	"compress/gzip"
	"encoding/gob"
	"encoding/json"
	"os"
	"path"
	"strings"
	"time"

	"github.com/kshedden/keyes/utils"
)

const (
	pa = "/nfs/kshedden/Daniel_Keyes"
)

var (
	// Summary statistics (counts per sex/location/day)
	locx map[string]*utils.Aggxt

	data utils.Datat
)

func aggregate() {

	// Get the earliest date
	ref := time.Time{}
	for _, y := range data.DOS {
		if ref.IsZero() || (!y.IsZero() && y.Before(ref)) {
			ref = y
		}
	}

	locx = make(map[string]*utils.Aggxt)

	mz := 366 * (2021 - ref.Year())

	for i, dos := range data.DOS {

		if dos.IsZero() {
			continue
		}

		locid := data.Loc[i]
		aggx, ok := locx[locid]
		if !ok {
			aggx = utils.NewAggxt(mz)
			locx[locid] = aggx
		}

		var agg *utils.Aggt
		switch data.Sex[i] {
		case 'F':
			agg = aggx.Female
		case 'M':
			agg = aggx.Male
		default:
			continue
		}

		y := dos.Year() - ref.Year()
		ii := 365*y + dos.YearDay() - 1
		agg.Datex[ii] = dos

		agg.Total[ii]++

		if data.Age[i] <= 18 {
			agg.Pediatric[ii]++
		}

		if data.FluBill[i] || data.FluComplaint[i] {
			agg.Flu[ii]++
		}

		if data.Trauma[i] {
			agg.Trauma[ii]++
		}

		if data.Admit[i] {
			agg.Admit[ii]++
		}

		age := int(data.Age[i])
		if age > 99 {
			age = 99
		}
		agg.Age[ii][age]++
	}

	// The dates only represent a day, so truncate.
	for k := range locx {
		locx[k].Female.SetDate()
		locx[k].Male.SetDate()
	}
}

func load() {

	fid, err := os.Open(path.Join(pa, "data.gob.gz"))
	if err != nil {
		panic(err)
	}
	defer fid.Close()

	gid, err := gzip.NewReader(fid)
	if err != nil {
		panic(err)
	}
	defer gid.Close()

	dec := gob.NewDecoder(gid)

	if err := dec.Decode(&data); err != nil {
		panic(err)
	}
}

func save(fname string) {

	fid, err := os.Create(path.Join(pa, fname))
	if err != nil {
		panic(err)
	}
	defer fid.Close()

	gid := gzip.NewWriter(fid)
	defer gid.Close()

	switch {
	case strings.Contains(fname, "json"):
		enc := json.NewEncoder(gid)
		if err := enc.Encode(locx); err != nil {
			panic(err)
		}
	case strings.Contains(fname, "gob"):
		enc := gob.NewEncoder(gid)
		if err := enc.Encode(locx); err != nil {
			panic(err)
		}
	default:
		panic("!!")
	}
}

func clean() {

	locx2 := make(map[string]*utils.Aggxt)

	for k, v := range locx {

		n := 0
		for _, v := range v.Female.Date {
			if v != "0001-01-01" {
				n++
			}
		}
		for _, v := range v.Male.Date {
			if v != "0001-01-01" {
				n++
			}
		}

		if n > 0 {
			locx2[k] = v
		}
	}

	locx = locx2
}

func main() {
	load()
	aggregate()
	clean()
	save("counts.json.gz")
	save("counts.gob.gz")
}
