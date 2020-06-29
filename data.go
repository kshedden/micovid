package main

import (
	"compress/gzip"
	"encoding/csv"
	"encoding/gob"
	"fmt"
	"io"
	"os"
	"path"
	"strings"
	"time"
	"unicode"

	"github.com/kshedden/keyes/utils"
)

const (
	pa = "/nfs/kshedden/Daniel_Keyes"
	fn = "UMICH_Demo_Output_20200615_utf8.txt.gz"
)

var (
	// Full data for the variables that we are using
	data utils.Datat

	// Billing codes that indicate Covid
	bcodes = []string{"J06.", "R50.", "U07.1", "Z03.818", "R05", "R06.", "J02.9",
		"J18.0", "J18.1", "J18.2", "J18.8", "J18.9", "R91.8", "Z20.828",
		"R09.", "R11.2", "R53.1", "J44.1", "J96.", "R07.9", "Z99.1",
		"Z99.11", "Z99.81", "J80"}

	// These codes exclude Covid even if one of the above codes matches
	xcodes = []string{"J09.X2", "J10.1"}

	// Patient flu-like complaints
	cterms = []string{"anosmia", "body aches", "breathing problem", "chest pain", "cough", "covid",
		"diarrhea", "febrile", "fever", "flu", "hypoxia", "nausea", "shortness of breath", "sob", "influenza",
		"difficulty breathing", "persistent pain", "respiratory distress",
		"vomit", "pneumonia", "pna", "pharyngitis", "seizures", "tachypnea",
		"weakness", "wheezing"}
)

func read() {

	fn := path.Join(pa, fn)
	fid, err := os.Open(fn)
	if err != nil {
		panic(err)
	}
	defer fid.Close()

	gid, err := gzip.NewReader(fid)
	if err != nil {
		panic(err)
	}
	defer gid.Close()

	cr := csv.NewReader(gid)
	cr.Comma = '|'
	cr.FieldsPerRecord = -1
	cr.LazyQuotes = true

	// Read the header
	head, err := cr.Read()
	if err != nil {
		panic(err)
	}

	// Get positions of all variables
	cx := make(map[string]int)
	for k, v := range head {
		cx[v] = k
	}

	// Get a key from a map, panic if the key is not
	// in the map
	get := func(cx map[string]int, x string) int {
		p, ok := cx[x]
		if !ok {
			panic(x)
		}
		return p
	}

	// Positions of the variables that we are using
	dobi := get(cx, "PTDOB")
	sexi := get(cx, "PTGENDER")
	dosi := get(cx, "DOS")
	cmpi := get(cx, "PTCOMPLAINT")
	pdgi := get(cx, "PRIMDIAG")
	loci := get(cx, "LOCATIONID")
	admi := get(cx, "ADMITFLAG")
	insi := get(cx, "PTINSURANCE")

	for {
		row, err := cr.Read()
		if err == io.EOF {
			break
		} else if err != nil {
			panic(err)
		}

		data.Sex = append(data.Sex, prawb(row, sexi))
		data.DOS = append(data.DOS, pdos(row, dosi))
		data.DOB = append(data.DOB, pdob(row, dobi))
		data.CMP = append(data.CMP, praw(row, cmpi))
		data.PDG = append(data.PDG, praw(row, pdgi))
		data.Loc = append(data.Loc, praw(row, loci))
		data.Ins = append(data.Ins, praw(row, insi))
		data.Admit = append(data.Admit, padm(row, admi))
	}

	for i, x := range data.Loc {
		data.Loc[i] = strings.Replace(x, "\r", "", -1)
	}
}

func praw(row []string, p int) string {
	if p < len(row) {
		return row[p]
	}
	return ""
}

func padm(row []string, p int) bool {
	return row[p] == "Y"
}

func prawb(row []string, p int) byte {
	if p < len(row) {
		if len(row[p]) == 1 {
			return row[p][0]
		}
	}
	return ' '
}

func pdos(row []string, p int) time.Time {

	if p >= len(row) {
		return time.Time{}
	}
	x := row[p]

	f := "2006-01-02 15:04:05"
	t, err := time.Parse(f, x)
	if err != nil {
		return time.Time{}
	}

	return t
}

func pdob(row []string, p int) time.Time {

	if p >= len(row) {
		return time.Time{}
	}
	x := row[p]

	if len(x) < 10 {
		return time.Time{}
	}

	f := "2006-01-02"
	t, err := time.Parse(f, x[0:10])
	if err != nil {
		panic(err)
	}

	return t
}

func setAge() {

	data.Age = make([]float64, len(data.DOB))

	for i, x := range data.DOB {
		y := data.DOS[i]
		if !data.DOB[i].IsZero() && !data.DOS[i].IsZero() {
			d := y.Sub(x)
			h := d.Hours()
			data.Age[i] = h / (24 * 365.25)
		}
	}
}

func setFluBill() {

	data.FluBill = make([]bool, len(data.PDG))

	for i, x := range data.PDG {

		s := false
		for _, y := range bcodes {
			if strings.HasPrefix(x, y) {
				s = true
				break
			}
		}

		t := false
		for _, y := range xcodes {
			if strings.HasPrefix(x, y) {
				t = true
				break
			}
		}

		data.FluBill[i] = s && !t
	}
}

func setFluComplaint() {

	data.FluComplaint = make([]bool, len(data.CMP))

	for i, x := range data.CMP {
		xl := strings.ToLower(x)
		for _, r := range cterms {
			if strings.Contains(xl, r) {
				data.FluComplaint[i] = true
				break
			}
		}
	}
}

func setTrauma() {

	data.Trauma = make([]bool, len(data.PDG))

	for i, x := range data.PDG {

		s := false
		s = s || (len(x) >= 8 && x[0] == 'S' && unicode.IsDigit(rune(x[1])) &&
			unicode.IsDigit(rune(x[2])) && strings.Contains("ABC", string(x[7])))
		s = s || strings.HasPrefix(x, "T07")
		s = s || strings.HasPrefix(x, "T14")
		s = s || (strings.HasPrefix(x, "T2") && len(x) >= 8 && strings.Contains("012345678", string(x[2])) && x[7] == 'A')
		s = s || (strings.HasPrefix(x, "T3") && len(x) >= 3 && strings.Contains("012", string(x[2])))
		s = s || (len(x) >= 8 && strings.HasPrefix(x, "T79.A") && strings.Contains("123456789", string(x[6])) && x[7] == 'A')

		// Exclude
		t := len(x) >= 3 && x[0] == 'S' && unicode.IsDigit(rune(x[1])) && x[2] == '0'

		data.Trauma[i] = s && !t
	}
}

func sumb(x []bool) int {
	n := 0
	for _, b := range x {
		if b {
			n++
		}
	}
	return n
}

func message() {
	fmt.Printf("Num records:         %16d\n", len(data.Age))
	fmt.Printf("Num trauma:          %16d\n", sumb(data.Trauma))
	fmt.Printf("Num flu-bill:        %16d\n", sumb(data.FluBill))
	fmt.Printf("Num flu-complaint:   %16d\n", sumb(data.FluComplaint))
}

func save() {

	fid, err := os.Create("/nfs/kshedden/Daniel_Keyes/data.gob.gz")
	if err != nil {
		panic(err)
	}
	defer fid.Close()

	gid := gzip.NewWriter(fid)
	defer gid.Close()

	enc := gob.NewEncoder(gid)

	if err := enc.Encode(&data); err != nil {
		panic(err)
	}
}

func main() {

	read()
	setAge()
	setFluBill()
	setFluComplaint()
	setTrauma()
	message()
	save()
}
