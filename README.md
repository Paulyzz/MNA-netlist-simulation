# MNA-netlist-simulation
MNA-Q
---------------------------------------------------------------------------
A SPICE netlist simulation tool for MATLAB

How to use:
--------------------------
1.  open main.m in MATLAB.
2.  enter 1 to select MNA as the circuit analysis method.
3.  enter the file name of the netlist.

MNA-Q supports the following circuit elements :
-------
- Resistors (R)
- Capacitors (C)
- Inductors (L)
- Independent voltage sources (V)
- Independent current sources (I)
- Voltage controlled voltage sources (VCVS) (E)
- Voltage controlled current sources (VCCS) (I)
- Current controlled voltage sources (CCVS) (H)
- Current controlled current sources (CCCS) (F)

MNA-Q currently support three simulation types :
--------
- DC bias point
- AC frequency analysis
- AC transient analysis

-note: The program only allow sinusoidal voltage and circuit sources with limited input. Also, This tool works only on versions of MATLAB from R2014b onwards.
