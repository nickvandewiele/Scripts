import xlrd
import sys
import shutil
import urllib2
import numpy
import matplotlib
from scipy import interpolate
import csv

matplotlib.use('Agg')
from matplotlib import pyplot

import os
def read_and_convert_IUPAC_into_InChI(filename):
    '''
    reads in an array of IUPAC names and converts these to inchis using Cactus
    '''
   
    # Spreadsheet containing all the data
    sheetname = 'exp data'
    wb = xlrd.open_workbook(filename)
    wb.sheet_names()
    sheet_with_exp_data = wb.sheet_by_name(sheetname);
    #row no. corresponding to TCD conversion data:
    row_no = 6
    no_comps = 59
    column_with_names = sheet_with_exp_data.col_values(0, start_rowx=row_no, end_rowx = row_no + no_comps)
    #print column_with_names
    
    EXP_names = {}
    
    for name in column_with_names:
                    IUPAC = name[4:]#cut of 'wt% '
                    link = 'http://cactus.nci.nih.gov/chemical/structure/%s/stdinchi' % IUPAC
                    try:
                        opener = urllib2.build_opener()
                        request = opener.open(link)
                        inchi = request.read()
                        if not inchi == '' and inchi[:5] == 'InChI' and len(inchi) < 100:
                           EXP_names[IUPAC] = inchi[8:]
                        else:
                            print '%s did not yield a reasonable inchi' % IUPAC
                        
                    except urllib2.HTTPError, urllib2.URLError:
                        print '%s could not be parsed' % IUPAC
                    finally:
                        request.close()
    print 'Experimental names converted!'    
    return EXP_names

    
def main(RMG_names, EXP_names, EXP_Conversion_data, EXP_data, MOD_Conversion_data, MOD_data):
    '''
    For each of the components found in the experimental data, the corresponding RMG name is searched for.
    
    
    '''
    global current_dir
    current_dir = os.getcwd()
    global results_dir
    results_dir = os.path.join(current_dir, 'Plots')
    output = 'Names_table.txt'
    with open(output, 'w') as output_file:
        print [RMG_names[EXP_names['Toluene']]]
        for IUPAC in EXP_names:
            print IUPAC
            Ydata_exp = EXP_data[IUPAC]
            
            try:
                Ydata_model = MOD_data[RMG_names[EXP_names[IUPAC]]]
                print Ydata_model
                output_file.write(IUPAC + '\t' + EXP_names[IUPAC] + '\t' + RMG_names[EXP_names[IUPAC]] + '\n')
                Plots = Plotting()
                Plots.generatePlot(EXP_Conversion_data, MOD_Conversion_data, Ydata_exp, Ydata_model, IUPAC)
            except KeyError:#Species found in experiments is not found in RMG names list
                pass
    output_file.close()          
    print "Finished collecting data in bins."

def read_RMG_names(dictionary):
    '''
    reads in an RMG generated species dictionary that contains species names (and adjacency lists) and 
    the corresponding inchi
    
    returns a dict with inchis as keys and the RMG name as values
    '''
    RMG_names = {}
    with open(dictionary) as input_file:
        for each_line in input_file:
            if 'InChI' in each_line:
                name, inchi = each_line.split(' ')
                RMG_names[inchi[7:].strip()] = name#remove 'InChI=1' and end of line 
    
    print 'RMG names read in!'     
    return RMG_names

    
def read_model_data(filename):
    '''
    1) reads in an array for TCD conversions, consisting of two sub arrays corresponding of conversions
        at ND and HD.  
    2) reads row-centered model data with each row representing one component
        Per row 16 experiments represent ND experiments, while 11 experiments represent HD experiments
    3) a dictionary is created with RMG component names as keys and an array of data as value
        each array of data consists of two sub arrays, one for ND, one for HD
    4) the TCD conversion data and the yield data is returned    
    '''
    
    #1) collect conversion data
    Conversion_data = []
    # Spreadsheet containing all the data
    
    reader = csv.reader(open(filename, 'rb'), delimiter=',')
        
    #column number at which HD data is found:
    no_HD = 17
    #column number of end of data:
    no_END = 28
    
    #2 and #3 : collect yield data
    MOD_data = {}

    for row in reader:
        if row[0] == 'Mass_fraction_JP10(1)':#row no. corresponding to TCD conversion data:
            ND_conv_data = [(100-float(t)) for t in row[1:no_HD]]
            HD_conv_data = [(100-float(t)) for t in row[no_HD:no_END]]
            Conversion_data.append(ND_conv_data)
            Conversion_data.append(HD_conv_data)
        Component_data = []
        ND_comp_data = row[1:no_HD]
        HD_comp_data = row[no_HD:no_END]
        Component_data.append(ND_comp_data)
        Component_data.append(HD_comp_data)
        #store each data row in dictionary with corresponding component IUPAC name
        MOD_data[row[0][14:]] = Component_data 
    
    #4
    print 'Model data read in!'
    return Conversion_data, MOD_data        


def read_experimental_data(filename):
    '''
    1) reads in an array for TCD conversions, consisting of two sub arrays corresponding of conversions
        at ND and HD.  
    2) reads row-centered experimental data with each row representing one component
        Per row 16 experiments represent ND experiments, while 11 experiments represent HD experiments
    3) a dictionary is created with IUPAC component names as keys and an array of data as value
        each array of data consists of two sub arrays, one for ND, one for HD
    4) the TCD conversion data and the yield data is returned    
    '''
    
    #1) collect conversion data
    Conversion_data = []
    # Spreadsheet containing all the data
    sheetname = 'exp data'
    wb = xlrd.open_workbook(filename)
    wb.sheet_names()
    sheet_with_exp_data = wb.sheet_by_name(sheetname);
    #row no. corresponding to TCD conversion data:
    no_conversion = 3
    column_with_conv_data = sheet_with_exp_data.row_values(no_conversion, start_colx=1)
    #column number at which HD data is found:
    no_HD = 48
    #column number of end of data:
    no_END = 81
    ND_conv_data = column_with_conv_data[1:no_HD]
    HD_conv_data = column_with_conv_data[no_HD:no_END]
    Conversion_data.append(ND_conv_data)
    Conversion_data.append(HD_conv_data)
    
    #2 and #3 : collect yield data
    EXP_data = {}
    #row at which component data is started:
    row_no = 6
    no_comps = 61
    column_with_component_names = sheet_with_exp_data.col_values(0, start_rowx=row_no, end_rowx = row_no + no_comps)
    
    i = 0 
    while i < len(column_with_component_names):
        Component_data = []
        row_with_comp_data = sheet_with_exp_data.row_values(i + row_no, start_colx=1)
        ND_comp_data = row_with_comp_data[1:no_HD]
        HD_comp_data = row_with_comp_data[no_HD:no_END]
        Component_data.append(ND_comp_data)
        Component_data.append(HD_comp_data)
        #each component name is started with 'wt% '
        #store each data row in dictionary with corresponding component IUPAC name
        EXP_data[column_with_component_names[i][4:]] = Component_data 
        i = i + 1
    
    #4
    print 'Experimental data read in!'
    return Conversion_data, EXP_data


class Plotting():
    
    def __init__(self):
        pass
    
    def generatePlot (self, Xdata_exp, Xdata_model, Ydata_exp, Ydata_model, Component_name): 
        """
        Plot of first column (X-axis) vs the other columns
        """
        
        #self.clear_results_directory(results_dir)
        
        XaxisLabel = 'TCD Conversion [%]'
        YaxisLabel = 'Product Yield [wt %]'
        
        self.drawplot(XaxisLabel, YaxisLabel, Xdata_exp, Xdata_model, Ydata_exp, Ydata_model, Component_name)

    def drawplot(self, XaxisLabel, YaxisLabel, Xdata_exp, Xdata_model, Ydata_exp, Ydata_model, Component_name): 
        '''
        A figure is made in which both Normal (ND) and High (HD) dilution experiments are depicted.
        '''
               
        fig = pyplot.figure()
        pyplot.clf()
        ax = fig.add_subplot(111)
        #ax = fig.add_subplot(212)
           
        #experimental data:    
        #plt_exp_ND = ax.plot(Xdata_exp[0], Ydata_exp[0], marker = 'o', color = 'r', label = Component_name + ' Exp. 9:1')   
        #plt_exp_HD = ax.plot(Xdata_exp[1], Ydata_exp[1], marker = 's', color = 'b', label = Component_name + ' Exp. 14:1')
        plt_exp_ND = ax.plot(Xdata_exp[0], Ydata_exp[0], 'ro')
        plt_exp_HD = ax.plot(Xdata_exp[1], Ydata_exp[1], 'sb')
        
        #model data with interpolated trend line
        f_ND = interpolate.interp1d(Xdata_model[0], Ydata_model[0], kind = 'zero')
        f_HD = interpolate.interp1d(Xdata_model[1], Ydata_model[1], kind = 'zero')     
        trendline_ND = ax.plot(Xdata_model[0],f_ND(Xdata_model[0]), "r--", lw = 2,label = Component_name + ' Model 9:1')
        trendline_HD = ax.plot(Xdata_model[1],f_HD(Xdata_model[1]), "b-", lw = 2,label = Component_name + ' Model 14:1')

        #axis labels
        ax.set_xlabel(XaxisLabel, fontsize = 14)
        ax.set_ylabel(YaxisLabel, fontsize = 14)
    
        ax.grid(which='major')
        
        #ax.legend(numpoints=1,loc = 'best', fancybox = True, shadow = True, ncol = 1)
        #ax.legend(numpoints=1, bbox_to_anchor=(0., 1.02, 0.7, .4), loc=3, mode="expand", borderaxespad=0., fancybox = True, shadow = True, ncol = 1)
        title = ''
        pyplot.title(title)
                
        #backend drawing
        fig.canvas.print_figure(os.path.join(results_dir, Component_name + '.png'), dpi=None)
     

def clear_results_directory(self, name):
        """
        Clear the contents of the directory with the specified name
        """
        if os.path.exists(name):
            shutil.rmtree(name)
        if name:
            os.mkdir(name)

if __name__ == "__main__":
    
    #input = sys.stdin.readlines()
    #1st arg: input folder
    #filename = os.path.join(input,'all compounds validation.xls')
    filename = 'input/all compounds validation.xls'
    
    EXP_names = read_and_convert_IUPAC_into_InChI(filename)
    print EXP_names
    
    EXP_Conversion_data, EXP_data = read_experimental_data(filename)
    
    filename = 'output/Summary.csv'
    MOD_Conversion_data, MOD_data = read_model_data(filename)
    
    dictionary = 'input/RMG_Dictionary.txt'
    RMG_names = read_RMG_names(dictionary)
    #print RMG_names 
    main(RMG_names, EXP_names, EXP_Conversion_data, EXP_data, MOD_Conversion_data, MOD_data)
    
    

