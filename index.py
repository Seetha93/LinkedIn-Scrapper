import sys
import urllib2
from bs4 import BeautifulSoup
import sys
import os
import csv
import xlsxwriter
from linkedin import LinkedIn

def write_to_excel(records, output_file):
	# Write data to XLSX file
	workbook = xlsxwriter.Workbook('results/%s.xlsx' % output_file)
	worksheet1 = workbook.add_worksheet('dataset')
	
	# Set record position for XLSX
	recordpos = 1
	worksheet1.write('A%i' % recordpos, 'Cst_key')          
	worksheet1.write('B%i' % recordpos, 'Name')          
	worksheet1.write('C%i' % recordpos, 'Link')          
	worksheet1.write('D%i' % recordpos, 'Number of Jobs')          
	worksheet1.write('E%i' % recordpos, 'Job Title')          
	worksheet1.write('F%i' % recordpos, 'Job Organization')  
	worksheet1.write('G%i' % recordpos, 'Job Start Date')          
	recordpos = recordpos + 1       

	for record in records:
		worksheet1.write('A%i' % recordpos, record['id'])          
		worksheet1.write('B%i' % recordpos, record['name'])          
		worksheet1.write('C%i' % recordpos, record['url'])          
		worksheet1.write('D%i' % recordpos, record['no_of_jobs'])          
		worksheet1.write('E%i' % recordpos, record['current_position'] )          
		worksheet1.write('F%i' % recordpos, record['current_company'] )  
		worksheet1.write('G%i' % recordpos, record['job_start_date'])        
		# Increment Record Position
		recordpos = recordpos + 1
	

input_file = raw_input("Enter input file path\n")
outfile = raw_input("Enter filename for output (exclude file extension)\n")
print "[Info] Reading Customer Data"
analysis_reader = csv.reader(open(input_file, 'rU'), delimiter= ",")

rows = []

for line in analysis_reader:
	rows.append(line)

records = []
profiles = []
linkedin = LinkedIn()

for i in range(100):
	#Pass the customer name and get search results
	row = rows[i]
	# print row
	if(row[1] != 'cst_type' and row[5] != 'NULL' and row[1] == 'Individual'):
		print "[Info] Searching %s" % row[5].split(",")[0]
		print
		try:
			# Search in linkedin with customer name
			search_results = linkedin.search(row[5].split(",")[0])

			# If there are many records even after filtering based on city, skipping that for now. Should implement a new method to filter results.
			if(len(search_results) == 1):
				print search_results[0]['url']
				profiles.append(
					{
						'id' : row[0],
						'name' : row[5],
						'url' : search_results[0]['url']
					}
				)
				 
				# profile_data = linkedin.get_profile_data(search_results[0]['url'])
				# records.append({
				# 	'id' : row[0], 
				# 	'name' : row[5],
				# 	'url': search_results[0]['url'],
				# 	'no_of_jobs': profile_data['no_of_jobs'],
				# 	'current_position': profile_data['current_position'],
				# 	'current_company': profile_data['current_company'],
				# 	'job_start_date': profile_data['job_start_date'],
				# })
				# print {
				# 	'id' : row[0], 
				# 	'name' : row[5],
				# 	'url': search_results[0]['url'],
				# 	'no_of_jobs': profile_data['no_of_jobs'],
				# 	'current_position': profile_data['current_position'],
				# 	'current_company': profile_data['current_company'],
				# }
				
			# print "[Info]"
			print
			print
		except Exception as e:
			print e
			pass


linkedin.start_driver()
print "[Info] Getting Individual Profiles"
for profile in profiles:
	print "[Info] Getting %s" % profile['url']
	print
	try:
		profile_data = linkedin.get_profile_data(profile['url'])
		records.append({
			'id' : profile['id'], 
			'name' : profile['name'],
			'url': profile['url'],
			'no_of_jobs': profile_data['no_of_jobs'],
			'current_position': profile_data['current_position'],
			'current_company': profile_data['current_company'],
			'job_start_date': profile_data['job_start_date'],
		})
		print {
			'id' : profile['id'], 
			'name' : profile['name'],
			'url': profile['url'],
			'no_of_jobs': profile_data['no_of_jobs'],
			'current_position': profile_data['current_position'],
			'current_company': profile_data['current_company'],
		}
		print
		print	
	except Exception as e:
		print e	
		pass
		print

		

print "[Info] Writing Customer Data"
write_to_excel(records, outfile)
linkedin.logout()



