package main

import (
	"compress/gzip"
	"encoding/gob"
	"fmt"
	"io"
	"math"
	"os"
	"path"

	"github.com/kshedden/keyes/utils"
	"gonum.org/v1/gonum/floats"
)

const (
	pa = "/nfs/kshedden/Daniel_Keyes"
)

var (
	code map[string][2]int
	tot  [2]int

	data utils.Datat
)

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

func scan() {

	for i, dos := range data.DOS {

		pdg := data.PDG[i]
		y := dos.Year() - 2019
		m := dos.Month() - 1
		if m == 3 {
			v := code[pdg]
			v[y]++
			code[pdg] = v
			tot[y]++
		}
	}
}

func sum(x [2]int) int {
	y := 0
	for _, v := range x {
		y += v
	}
	return y
}

type srec struct {
	Code string
	Z    float64
	P0   float64
	P1   float64
}

// ByAge implements sort.Interface for []Person based on
// the Age field.
type ByZ []srec

func (a ByZ) Len() int           { return len(a) }
func (a ByZ) Swap(i, j int)      { a[i], a[j] = a[j], a[i] }
func (a ByZ) Less(i, j int) bool { return a[i].Z < a[j].Z }

func compare() {

	var recs []srec
	var zv []float64
	for c, v := range code {

		if sum(v) < 200 {
			continue
		}

		p0 := float64(v[0]) / float64(tot[0])
		p1 := float64(v[1]) / float64(tot[1])
		se := math.Sqrt(p0*(1-p0)/float64(tot[0]) + p1*(1-p1)/float64(tot[1]))
		z := (p1 - p0) / se

		recs = append(recs, srec{c, z, p0, p1})
		zv = append(zv, z)
	}

	ii := make([]int, len(recs))
	floats.Argsort(zv, ii)

	out, err := os.Create("codes_april.txt")
	if err != nil {
		panic(err)
	}
	defer out.Close()

	for _, i := range ii {
		r := recs[i]
		io.WriteString(out, fmt.Sprintf("%v\t%f\t%f\n", r.Code, r.Z, r.P1/r.P0))
	}
}

func main() {

	load()

	code = make(map[string][2]int)

	scan()

	compare()
}
