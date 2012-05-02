import xlrd
import shutil
import numpy
import matplotlib
from scipy import interpolate
matplotlib.use('Agg')
from matplotlib import pyplot
import csv
import os


def readExpConversion(filename):

    # Spreadsheet containing all the data
    wb = xlrd.open_workbook(filename)    

    data_components = wb.sheet_by_name('data_pyplot');
    number_of_data_cols = len(data_components.row_values(0))
    
        
    data_cols_comps = []
    i = 0
    while i < number_of_data_cols:
            data_cols_comps.append(data_components.col_values(i, start_rowx=0))
            i = i+1
        
    Temperatures = [data_components.col_values(0, start_rowx=1), data_components.col_values(2, start_rowx=1)[:33]]
    Conv = [data_components.col_values(1, start_rowx=1), data_components.col_values(3, start_rowx=1)[:33]]
    assert len(Temperatures[0]) == len(Conv[0])  
    assert len(Temperatures[1]) == len(Conv[1])
    #print Temperatures, Conv
    print 'Experimental data read in!'
    return Temperatures, Conv

def readModelConversion(filename):
    reader = csv.reader(open(filename, 'rb'), delimiter=',')
        
    #column number at which HD data is found:
    no_HD = 17
    #column number of end of data:
    no_END = 32
    
    TND = [933.2, 943.2, 953.2, 963.2, 973.2, 983.2, 993.2, 1003.2, 1013.2, 1023.2, 1033.2, 1043.2, 1053.2, 1063.2, 1073.2, 1083.2]
    THD = [973.2, 987.1, 996.9, 1006.6, 1016.9, 1026.5, 1036.5, 1046.5, 1056.5, 1066.3, 1076.2, 1086.5, 1026.4, 1036.6, 1055.8]
    Temperatures = [TND, THD]
    
    for row in reader:
        if row[0] == 'Mass_fraction_JP10(1)':#row no. corresponding to TCD conversion data:
            ND_conv_data = [(100-float(t)) for t in row[1:no_HD]]
            HD_conv_data = [(100-float(t)) for t in row[no_HD:no_END]]
            break
    Conversion_data = [ND_conv_data, HD_conv_data]
    #4
    print 'Model conversion data read in!'
    assert len(Temperatures[0]) == len(Conversion_data[0])  
    assert len(Temperatures[1]) == len(Conversion_data[1])
    #print Temperatures, Conversion_data       
    return Temperatures, Conversion_data       

def main(file, EXP_Temperatures, EXP_Conversion_data, MOD_Temperatures, MOD_Conversion_data):

    Plots = Plotting()
    Plots.generatePlot([EXP_Temperatures, EXP_Conversion_data, MOD_Temperatures, MOD_Conversion_data])
    
    print "Finished collecting data in bins."

            
class Plotting():
    
    def __init__(self):
        pass
    
    def generatePlot (self,data_cols): 
        
        #self.clear_results_directory(results_dir)
        
        XaxisLabel = 'Reactor Temperature / K'
        YaxisLabel = 'TCD Conversion / %'
        
                
        self.drawplot(XaxisLabel, YaxisLabel, data_cols)

    def drawplot(self, XaxisLabel, YaxisLabel, data_cols):        

        #set colors and symbols:
        #http://matplotlib.sourceforge.net/api/pyplot_api.html#matplotlib.pyplot.plot
        colors = ['r', 'b', 'g', 'k', 'c', 'm', 'y', 'w']
        markers = ['o', 's','^' , 'D', 'v', '*', 'x', '+']

        fig = pyplot.figure()
        pyplot.clf()
        ax = fig.add_subplot(111)
           
        #experimental data: 
        plt_exp_ND = ax.plot(data_cols[0][0],data_cols[1][0], linestyle = '-', marker = 'o', color = 'r', label = 'Temperature Exp. ND')   
        plt_exp_HD = ax.plot(data_cols[0][1],data_cols[1][1], linestyle = '-', marker = 's', color = 'b', label = 'Temperature Exp. HD')
        
        #model data: 
        f_ND = interpolate.interp1d(data_cols[2][0],data_cols[3][0], kind = 'zero')     
        trendline_ND = ax.plot(data_cols[2][0],data_cols[3][0], "r--",lw = 2,label = 'TCD Conversion 9:1 Model ')        

        f_HD = interpolate.interp1d(data_cols[2][1],data_cols[3][1], kind = 'zero')     
        trendline_HD = ax.plot(data_cols[2][1],data_cols[3][1], "b-.",lw = 2,label = 'TCD Conversion 14:1 Model')        
          
            
        #axis labels
        ax.set_xlabel(XaxisLabel, fontsize = 14)
        ax.set_ylabel(YaxisLabel, fontsize = 14)
        ax.set_yscale('log')
        ax.grid(which='major')
    
        #ax.legend(numpoints=1, loc='best', fancybox = True, shadow = True, ncol = 1)
        title = ''
        pyplot.title(title)
                
        #backend drawing
        fig.canvas.print_figure(os.path.join(results_dir, 'conversion.png'), dpi=None)
        
    def clear_results_directory(self, name):
        """
        Clear the contents of the directory with the specified name
        """
        if os.path.exists(name):
            shutil.rmtree(name)
        if name:
            os.mkdir(name)

if __name__ == "__main__":
    
    global current_dir
    current_dir = os.getcwd()
    global results_dir
    results_dir = os.path.join(current_dir, 'Plots')
    
    #define name of xls input file:
    fileexp = 'input/exp_conversion.xls'
    EXP_Temperatures, EXP_Conversion_data = readExpConversion(fileexp)
    
    filename = 'output/Summary.csv'
    MOD_Temperatures, MOD_Conversion_data = readModelConversion(filename)
    
    main(filename, EXP_Temperatures, EXP_Conversion_data, MOD_Temperatures, MOD_Conversion_data)
    
    

