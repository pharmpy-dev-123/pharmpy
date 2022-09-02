$PROBLEM PERIPHERALS(1)
$INPUT ID VISI XAT2=DROP DGRP DOSE FLAG=DROP ONO=DROP
       XIME=DROP NEUY SCR AGE SEX NYHA=DROP WT DROP ACE
       DIG DIU NUMB=DROP TAD TIME VIDD=DROP CLCR AMT SS II DROP
       CMT=DROP CONO=DROP DV EVID=DROP OVID=DROP
$DATA /tmp/tool_results/modelsearch/models/.datasets/input_model.csv IGNORE=@
$SUBROUTINES ADVAN4  TRANS4
$PK
VP1 = THETA(5)
QP1 = THETA(4)
CL = THETA(1) * EXP(ETA(1))
VC = THETA(2) * EXP(ETA(2))
MAT = THETA(3) * EXP(ETA(3))
KA = 1/MAT
V2 = VC
Q = QP1
V3 = VP1
$ERROR
CONC = A(2)/VC
Y = CONC + CONC * EPS(1)
$ESTIMATION METHOD=0
$THETA (0, 24.5328, Inf) ; POP_CL
$THETA (0, 104.23, Inf) ; POP_VC
$THETA (0, 0.433676, Inf) ; POP_MAT
$THETA  (0,24.5328,999999) ; POP_QP1
$THETA  (0,5.211500000000001,999999) ; POP_VP1
$OMEGA 0.481858; IIV_CL
$OMEGA 0.593654; IIV_VC
$OMEGA 0.01; IIV_MAT
$SIGMA 0.209972; RUV_PROP
$TABLE ID TIME DV CWRES CIPREDI NOAPPEND FILE=mytab_mox1
