clc;
clear;
close all;
choice = input('<< Welcome to A SPICE netlist simulation tool >> \n 1. MNA \n');
switch(choice)
    case{1}
         system('python test1.py')
end
