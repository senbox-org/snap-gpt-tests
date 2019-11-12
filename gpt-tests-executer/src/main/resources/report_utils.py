"""
Report utils script
"""
import template as t
import sys


def create_html_report_per_json(template, json):
    """
	Create html report for each json test files

	Parameters:
	-----------
	- json: json file
	"""
	tmplt = t.Template(template)
	tmplt.generate(graphTestResult= graphTestResults,
				   jsonName=json,
				   operatingSystem=sys.platform,
				   scope=scope
				   )
    # compute start and end date
            if(graphTestResult.getStartDate() != null) {
                if (graphTestResult.getStartDate().before(start)) {
                    start = graphTestResult.getStartDate();
                }
            }
            if(graphTestResult.getEndDate() != null) {
                if(graphTestResult.getEndDate().after(end)) {
                    end = graphTestResult.getEndDate();
                }
            }
            totalDuration = totalDuration + graphTestResult.getExecutionTime();
        }
        SimpleDateFormat formatter = new SimpleDateFormat("dd/MM/yyyy HH:mm:ss");
        context.put("startDateString", formatter.format(start));
        context.put("endDateString", formatter.format(end));
        context.put("totalTime", Math.round((end.getTime()-start.getTime())/1000));
        context.put("sumTime", totalDuration);


        FileWriter fileWriter = new FileWriter(outputPath.toFile());
        StringWriter writer = new StringWriter();
        template.merge( context, fileWriter );
        fileWriter.close();


def main():
    """
    main entry point of the report utils
    """

if __name__ == '__main__':
    main()
