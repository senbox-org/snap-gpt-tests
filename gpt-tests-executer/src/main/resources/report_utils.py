"""
Report utils script
"""
import os
import template


def performances(template_path, tst_name, summary, path_plt=None):
    """
    Creates the html performances report per tests

	Parameters:
	-----------
	 - template_path: absolute path of the html template
	 - tst_name: test name
	 - summary: performance summary dict
	 - path_plt: optional plot path
    """
    with open(template_path, 'r') as file:
        report_tmp = template.Template(file.read())
        summ = [
            {
                'label': "Process duration",
                'value': summary['duration']['value'],
                'unit': summary['duration']['unit']
            },
            {
                'label': "CPU total timer",
                'value': summary['cpu_time']['value'],
                'unit': summary['cpu_time']['unit']
            },
            {
                'label': "CPU average usage",
                'value': summary['cpu_usage']['average'],
                'unit': summary['cpu_usage']['unit']
            },
            {
                'label': "CPU max usage",
                'value': summary['cpu_usage']['max'],
                'unit': summary['cpu_usage']['unit']
            },
            {
                'label': "Memory average usage",
                'value': summary['memory']['average'],
                'unit': summary['memory']['unit']
            },
            {
                'label': "Memory max usage",
                'value': summary['memory']['max'],
                'unit': summary['memory']['unit']
            }
        ]
        plots = []
        if path_plt:
            plots = [
                os.path.join(path_plt, tst_name+"_cpu_usage.png"),
                os.path.join(path_plt, tst_name+"_memory_usage.png")
            ]
        return report_tmp.generate(test_id=tst_name, summary=summ, plots=plots)
    return None


def report