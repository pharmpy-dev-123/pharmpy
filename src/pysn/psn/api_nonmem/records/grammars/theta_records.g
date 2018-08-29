// $THETA  value1  [value2]  [value3] ...
//          [(value)xn]
//          [NUMBERPOINTS=n]
//          [ABORT|NOABORT|NOABORTFIRST]
//
// 5 legal forms
//   1. init [FIXED]
//   2. ([low,] init [,up] [FIXED])
//   3. ([low,] init [,up]) [FIXED]  // MUST have "low" if "up" exists
//   4. (low,,up)  // has NO init
//   5. (value)xn  // value is inside parenthesis of form 2-4
//
// Rules
//   1. "low" and "up" can be skipped with -INF/INF (default).
//   2. "FIXED" requires "low" & "up" to equal "init", insofar they appear.
//   3. "FIXED" implied if "low"="init"="up".

root : ws mandatory_theta (ws option | ws comment)* [ws]

?mandatory_theta : theta

?option : theta
        | KEY [WS] "=" [WS] VALUE -> option
        | VALUE                   -> option

theta : init [WS] [FIX]                  // form 1
      | _lpar init _rpar                 // form 2+3+5 (init)
      | _lpar low sep init _rpar         // form 2+3+5 (low, init)
      | _lpar low sep init sep up _rpar  // form 2+3+5 (low, init, up)
      | _lpar low sepsep up _rpar        // form 4+5 (low, up)
sep : WS
    | [WS] "," [WS]
sepsep : [WS] "," [WS] "," [WS]
_lpar : "(" [WS]
_rpar : [WS] [FIX] ")" [n]
       | [WS] ")" [FIX]

init : NUMERIC
low  : NUMERIC | NEG_INF
up   : NUMERIC | POS_INF
n    : "x" INT

FIX : "FIXED"|"FIXE"|"FIX"

// generic option terminals (key/value)
KEY   : /(?!([0-9]|\(|FIX))\w+/      // TODO: use priority (instead of negative lookahead)
VALUE : /(?!([0-9]|\(|FIX))[^\s=]+/  // TODO: use priority (instead of negative lookahead)

// common misc rules
ws      : WS_ALL
comment : ";" [WS] [COMMENT]

// common misc terminals
WS: (" " | /\t/)+
WS_ALL: /\s+/

// common naked/enquoted text terminals
COMMENT : /\S.*(?<!\s)/  // no left/right whitespace padding

// common numeric terminals
DIGIT: "0".."9"
INT: DIGIT+
DECIMAL: (INT "." [INT] | "." INT)
SIGNED_INT: ["+" | "-"] INT

EXP: "E" SIGNED_INT
FLOAT: (INT EXP | DECIMAL [EXP])
SIGNED_FLOAT: ["+" | "-"] FLOAT

NUMBER: (FLOAT | INT)
SIGNED_NUMBER: ["+" | "-"] NUMBER
NUMERIC: (NUMBER | SIGNED_NUMBER)

NEG_INF: "-INF" | "-1000000"
POS_INF: "INF" | "1000000"
