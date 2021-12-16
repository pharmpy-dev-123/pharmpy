$PROBLEM PHENOBARB SIMPLE MODEL
$DATA ../pheno.dta IGNORE=@
$INPUT ID TIME AMT WGT APGR DV
$SUBROUTINE ADVAN3 TRANS1
$PK
K=THETA(1)*EXP(ETA(1))
K12=THETA(2)*EXP(ETA(2))
K21=THETA(3)*EXP(ETA(3))
$ERROR
Y=F+F*EPS(1)
$THETA  (0,0.00499295) ; POP_K
$THETA  (0,0.166672) ; POP_K12
$THETA  (0,0.446654) ; POP_K21
$OMEGA  0.214263  ;        IVK
$OMEGA  1.90709  ;      IVK12
$OMEGA  3.2795E-05  ;      IVK21
$SIGMA  0.0269087
$ESTIMATION METHOD=1 INTERACTION