'''
Created on Jan 24, 2012

Python version of Steven Pyl's fortran Convert script.

Objectives:

Read in a bunch of .ckcsv files (originating from NBMT's routine) and summarize them 
in a summary.csv file keeping only data at end distance of PFR reactor.

If a diluent.da file is present, renormalize data, with the species specified in 
this file as diluent.
@author: nmvdewie
'''
import os

with open(os.path.join('output','chem.asu')) as asu_file:
    number_of_species = int(asu_file.readline())
    print 'Number of species: ',number_of_species
    
with open(os.path.join('DILUENT.DA')) as diluent_file:
    diluent =  diluent_file.readline().split()[0]
    #print diluent
    diluent_name = diluent_file.readline().split()[0]
    diluent_name = 'Mass_fraction_'+diluent_name
    #print diluent_name
    number_of_experiments = int(diluent_file.readline().split()[0])
    
final_data = {}

with open(os.path.join('output','CKSoln.ckcsv_reactor_input_1.inp.csv')) as first_file:
    number_of_nodes =  first_file.readline().split()[2]
    #print number_of_nodes
    file_lines=first_file.readlines()
    start_to_read = 3
    for each_line in file_lines[start_to_read:(start_to_read+number_of_species)]:#read in all species
         pieces = each_line.split(',')
         name = pieces[0]
         #print name
         #if not name == diluent_name:
         final_data[name] = []#create list
counter = 1
while counter <number_of_experiments+1:#read in all experiments
    try:
       filename = os.path.join('output','CKSoln.ckcsv_reactor_input_%s.inp.csv')% counter
       counter = counter + 1
       with open(filename) as input:
          data = {}
          file_lines=input.readlines()
          for each_line in file_lines[4:(4+number_of_species-1)]:#read in all species
              pieces = each_line.split(',')
              name = pieces[0]
              value = float(pieces[-1])
              data[name] = value
          summation = 0.0
          summation = sum(data.values())
          
          summation = summation - data[diluent_name]
          check = 0.0
          for i in data.keys():
              data[i] = 100 * data[i]/summation
              #print diluent_name
              #if not (data[i] == diluent_name):
                #print i
                #check = check + data[i]
              final_data[i].append(data[i])#add value for this species and this experiment to final-data
    except IOError as e:
       print 'file does not exist.' , 
       pass
   
with open(os.path.join('output','Summary.csv'), 'w') as output_file:
    for name in final_data.keys():
        output_file.write(name+',')
        for item in final_data[name]:
            output_file.write("%s," % item)
        output_file.write('\n')
        
print 'Done!'