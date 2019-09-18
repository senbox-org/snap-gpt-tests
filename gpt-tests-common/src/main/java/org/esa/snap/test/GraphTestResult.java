package org.esa.snap.test;

import java.text.SimpleDateFormat;
import java.util.Date;

/**
 * Created by obarrile on 08/07/2019.
 */
public class GraphTestResult {
    private GraphTest graphTest;
    private String status = "UNKNOWN";
    private Date startDate = null;
    private Date endDate = null;
    private String memoryPeak = " - ";
    private SimpleDateFormat formatter;

    public GraphTestResult (GraphTest graphTest) {
        this(graphTest, "UNKNOWN", null, null, " - ");

    }

    public GraphTestResult (GraphTest graphTest, String status, Date startDate, Date endDate, String memoryPeak) {
        this.graphTest = graphTest;
        this.status = status;
        this.startDate = startDate;
        this.endDate = endDate;
        this.memoryPeak = memoryPeak;
        formatter = new SimpleDateFormat("dd/MM/yyyy HH:mm:ss");
    }

    public GraphTest getGraphTest() {
        return graphTest;
    }

    public String getStatus() {
        return status;
    }

    public Date getStartDate() {
        return startDate;
    }

    public Date getEndDate() {
        return endDate;
    }

    public String getStartDateString() {
        if(startDate == null) {
            return "NULL";
        }
        return formatter.format(startDate);
    }

    public String getEndDateString() {
        if(endDate == null) {
            return "NULL";
        }
        return formatter.format(endDate);
    }

    public String getExecutionTimeString() {
        if(endDate == null || startDate == null) {
            return "NULL";
        }
        return String.format("%d s",Math.round((endDate.getTime()-startDate.getTime())/1000));
    }

    public int getExecutionTime() {
        if(endDate == null || startDate == null) {
            return 0;
        }
        return Math.round((endDate.getTime()-startDate.getTime())/1000);
    }

    public String getMemoryPeak() {
        return memoryPeak;
    }


    public void setStatus(String status) {
        this.status = status;
    }

    public void setStartDate(Date startDate) {
        this.startDate = startDate;
    }

    public void setEndDate(Date endDate) {
        this.endDate = endDate;
    }

    public void setMemoryPeak(String memoryPeak) {
        this.memoryPeak = memoryPeak;
    }

    public String getconfigVMString() {
        String testEnvironment = "Default configuration";
        if (graphTest != null && graphTest.getConfigVM() != null) {
            testEnvironment = "MaxMemory: " + graphTest.getConfigVM().getXmX() +
                    "  Cache Size: " + graphTest.getConfigVM().getCacheSize() +
                    "  Parallelism: " + graphTest.getConfigVM().getParallelism();
        }
        return testEnvironment;
    }
}
