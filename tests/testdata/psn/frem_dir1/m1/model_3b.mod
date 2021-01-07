$PROBLEM    PHENOBARB SIMPLE MODEL
$DATA      ../frem_dataset.dta IGNORE=@
$INPUT      ID TIME AMT WGT APGR DV MDV FREMTYPE
$SUBROUTINE ADVAN1 TRANS2
$PK
CL=THETA(1)*EXP(ETA(1))
V=THETA(2)*EXP(ETA(2))
S1=V

    SDC3 = 2.23763568135
    SDC4 = 0.704564727537
$ERROR
Y=F+F*EPS(1)

;;;FREM CODE BEGIN COMPACT
;;;DO NOT MODIFY
    IF (FREMTYPE.EQ.100) THEN
;      APGR  2.23763568135
       Y = THETA(3) + ETA(3)*SDC3 + EPS(2)
       IPRED = THETA(3) + ETA(3)*SDC3
    END IF
    IF (FREMTYPE.EQ.200) THEN
;      WGT  0.704564727537
       Y = THETA(4) + ETA(4)*SDC4 + EPS(2)
       IPRED = THETA(4) + ETA(4)*SDC4
    END IF
;;;FREM CODE END COMPACT
$THETA  (0,0.00581756) ; TVCL
$THETA  (0,1.44555) ; TVV
$THETA  6.42372881356 FIX ; TV_APGR
 1.52542372881 FIX ; TV_WGT
$OMEGA  BLOCK(4)
 0.12599947825043922  ;       IVCL
 0.02019061328807956 0.22495923796766382  ;        IVV
 -0.01204160359398777 0.11542663299335346 1.000032179028572  ;   BSV_APGR
 0.2084749425323184 0.41558847222759365 0.24407956943624937 1.007762907974968  ;    BSV_WGT
$SIGMA  0.0164177
$SIGMA  0.0000001  FIX  ;     EPSCOV
$ESTIMATION METHOD=1 INTERACTION NONINFETA=1 MCETA=1 MAXEVALS=0
$ETAS       FILE=/home/rikard/testing/frem_dir1/m1/model_3b_input.phi

