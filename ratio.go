package main

import (
	"compress/gzip"
	"encoding/gob"
	"encoding/json"
	"fmt"
	"math"
	"os"
	"path"
	"time"

	"github.com/kshedden/keyes/utils"
	"github.com/kshedden/statmodel/glm"
	"github.com/kshedden/statmodel/statmodel"
	"gonum.org/v1/gonum/floats"
	"gonum.org/v1/gonum/optimize"
)

var (
	locx map[string]*utils.Aggxt

	results map[string][][]float64
)

const (
	pa = "/nfs/kshedden/Daniel_Keyes"
)

func load() {

	fid, err := os.Open(path.Join(pa, "counts.gob.gz"))
	if err != nil {
		panic(err)
	}
	defer fid.Close()

	gid, err := gzip.NewReader(fid)
	if err != nil {
		panic(err)
	}
	defer gid.Close()

	enc := gob.NewDecoder(gid)

	if err := enc.Decode(&locx); err != nil {
		panic(err)
	}
}

func basis(d []float64, q int) [][]statmodel.Dtype {

	n := len(d)
	s := 20.0
	g := float64(n-1) / float64(q-1)

	var bx [][]float64

	for j := 0; j < q; j++ {
		b := make([]statmodel.Dtype, n)
		c := statmodel.Dtype(j) * g
		for i := 0; i < n; i++ {
			u := (d[i] - c) / s
			b[i] = math.Exp(-u * u / 2)
		}
		bx = append(bx, b)
	}

	return bx
}

type selector func(*utils.Aggt) []int

func regress(loc, sex, vname string, fx selector) {

	degf := 10

	var y []int
	var dt []time.Time
	switch sex {
	case "Female":
		y = fx(locx[loc].Female)
		dt = locx[loc].Female.Datex
	case "Male":
		y = fx(locx[loc].Male)
		dt = locx[loc].Male.Datex
	default:
		panic("")
	}

	dm := make(map[int]int)
	ii := -9
	for i, d := range dt {
		c := 1000*d.Year() + d.YearDay()
		dm[c] = i
		if d.Year() == 2020 && d.Month() == 1 && d.Day() == 1 {
			ii = i
		}
	}
	if ii == -9 {
		panic("!!")
	}

	var z, x, d []float64
	for i := ii; i < len(y); i++ {
		if !dt[i].IsZero() {
			jj, ok := dm[1000*2019+dt[i].YearDay()]
			if !ok {
				panic("!!")
			}
			z = append(z, float64(y[i]))
			d = append(d, float64(dt[i].YearDay()))

			xx := 0.0
			for k := 0; k < 7; k++ {
				xx += float64(y[jj+k])
			}
			xx /= 7

			x = append(x, math.Log(1+xx)) // One year ago
		}
	}

	if floats.Sum(z) < 100 {
		return
	}

	da := [][]statmodel.Dtype{z, x}
	varnames := []string{"y", "x"}
	bx := basis(d, degf)

	da = append(da, bx...)
	var xnames []string
	for j := range bx {
		varnames = append(varnames, fmt.Sprintf("d%d", j))
		xnames = append(xnames, fmt.Sprintf("d%d", j))
	}

	df := statmodel.NewDataset(da, varnames, "y", xnames)
	config := glm.DefaultConfig()
	config.Family = glm.NewFamily(glm.PoissonFamily)
	config.OffsetVar = "x"
	config.FitMethod = "gradient"

	l2p := make(map[string]float64)
	for j := 0; j < degf; j++ {
		l2p[fmt.Sprintf("d%d", j)] = 0.1
	}
	config.L2Penalty = l2p

	model := glm.NewGLM(df, config)
	model = model.OptSettings(&optimize.Settings{GradientThreshold: 1e-4})
	result := model.Fit()

	ky := fmt.Sprintf("%s:%s:%s", loc, sex, vname)
	cf := result.Params()
	f := make([]float64, len(d))
	for i := range d {
		for j := range cf {
			f[i] += cf[j] * bx[j][i]
		}
	}
	results[ky] = [][]float64{d, f}

	fmt.Printf("Location=%v sex=%v\n", loc, sex)
	fmt.Printf("%+v\n", result.Summary())
}

func save() {

	fid, err := os.Create("/nfs/kshedden/Daniel_Keyes/ratio_results.json.gz")
	if err != nil {
		panic(err)
	}
	defer fid.Close()

	gid := gzip.NewWriter(fid)
	defer gid.Close()

	enc := json.NewEncoder(gid)

	if err := enc.Encode(&results); err != nil {
		panic(err)
	}
}

func main() {
	load()

	results = make(map[string][][]float64)

	for loc := range locx {
		regress(loc, "Female", "Total", func(agg *utils.Aggt) []int { return agg.Total })
		regress(loc, "Male", "Total", func(agg *utils.Aggt) []int { return agg.Total })

		regress(loc, "Female", "Pediatric", func(agg *utils.Aggt) []int { return agg.Pediatric })
		regress(loc, "Male", "Pediatric", func(agg *utils.Aggt) []int { return agg.Pediatric })

		regress(loc, "Female", "Trauma", func(agg *utils.Aggt) []int { return agg.Trauma })
		regress(loc, "Male", "Trauma", func(agg *utils.Aggt) []int { return agg.Trauma })

		regress(loc, "Female", "Flu", func(agg *utils.Aggt) []int { return agg.Flu })
		regress(loc, "Male", "Flu", func(agg *utils.Aggt) []int { return agg.Flu })

		regress(loc, "Female", "Admit", func(agg *utils.Aggt) []int { return agg.Admit })
		regress(loc, "Male", "Admit", func(agg *utils.Aggt) []int { return agg.Admit })
	}

	save()
}
