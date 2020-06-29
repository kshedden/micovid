package utils

import (
	"time"
)

type Datat struct {

	// Raw fields
	DOB []time.Time
	DOS []time.Time
	PDG []string
	CMP []string
	Ins []string

	// Derived fields
	Age          []float64
	Sex          []byte
	Loc          []string
	Admit        []bool
	FluBill      []bool
	FluComplaint []bool
	Trauma       []bool
}

type Aggt struct {
	Datex     []time.Time
	Date      []string
	Total     []int
	Flu       []int
	Trauma    []int
	Pediatric []int
	Age       [][100]int
	Admit     []int
}

type Aggxt struct {
	Female *Aggt
	Male   *Aggt
}

func (agg *Aggt) SetDate() {
	agg.Date = make([]string, len(agg.Datex))
	for i, d := range agg.Datex {
		agg.Date[i] = d.Format("2006-01-02")
	}
}

func NewAggt(m int) *Aggt {
	return &Aggt{
		Datex:     make([]time.Time, m),
		Total:     make([]int, m),
		Flu:       make([]int, m),
		Trauma:    make([]int, m),
		Pediatric: make([]int, m),
		Age:       make([][100]int, m),
		Admit:     make([]int, m),
	}
}

func NewAggxt(m int) *Aggxt {
	return &Aggxt{
		Female: NewAggt(m),
		Male:   NewAggt(m),
	}
}
