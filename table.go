package main

import (
	"compress/gzip"
	"encoding/gob"
	"fmt"
	"io"
	"os"
	"path"
	"sort"

	"github.com/kshedden/keyes/utils"
)

var (
	data utils.Datat
)

const (
	pa = "/nfs/kshedden/Daniel_Keyes"
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

func sumb(x []bool) int {
	n := 0
	for _, v := range x {
		if v {
			n++
		}
	}
	return n
}

func median(x []float64) (float64, float64, float64) {
	sort.Sort(sort.Float64Slice(x))
	n := float64(len(x))
	m1 := int(n * 0.5)
	m2 := int(n * 0.1)
	m3 := int(n * 0.9)
	return x[m1], x[m2], x[m3]
}

func main() {

	load()

	var age [2][]float64
	var female, male [2][]bool

	for i, _ := range data.DOS {

		if data.FluBill[i] || data.FluComplaint[i] {
			age[0] = append(age[0], data.Age[i])
			female[0] = append(female[0], data.Sex[i] == 'F')
			male[0] = append(male[0], data.Sex[i] == 'M')
		}
		age[1] = append(age[1], data.Age[i])
		female[1] = append(female[1], data.Sex[i] == 'F')
		male[1] = append(male[1], data.Sex[i] == 'M')
	}

	out, err := os.Create("table1.txt")
	if err != nil {
		panic(err)
	}
	defer out.Close()

	io.WriteString(out, "Age\n")
	a, b, c := median(age[0])
	io.WriteString(out, fmt.Sprintf("Covid-like median   %f\n", a))
	io.WriteString(out, fmt.Sprintf("Covid-like 10 pctl  %f\n", b))
	io.WriteString(out, fmt.Sprintf("Covid-like 90 pctl  %f\n", c))
	a, b, c = median(age[1])
	io.WriteString(out, fmt.Sprintf("Overall median      %f\n", a))
	io.WriteString(out, fmt.Sprintf("Overall 10 pctl     %f\n", b))
	io.WriteString(out, fmt.Sprintf("Overall 90 pctl     %f\n", c))

	io.WriteString(out, "\n\n")

	io.WriteString(out, fmt.Sprintf("Covid-like female   %d\n", sumb(female[0])))
	io.WriteString(out, fmt.Sprintf("Covid-like male     %d\n", sumb(male[0])))
	io.WriteString(out, fmt.Sprintf("Overall female      %d\n", sumb(female[1])))
	io.WriteString(out, fmt.Sprintf("Overall male        %d\n", sumb(male[1])))
}
