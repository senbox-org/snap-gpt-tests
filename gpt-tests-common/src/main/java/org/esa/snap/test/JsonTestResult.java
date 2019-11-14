package org.esa.snap.test;

import java.text.SimpleDateFormat;
import java.util.ArrayList;
import java.util.Date;

/**
 * Created by obarrile on 06/09/2019.
 */
public class JsonTestResult {
    private String jsonName = "";
    private ArrayList<GraphTestResult> graphTestResultList;
    private String status = "UNKNOWN";
    private Date startDate = null;
    private Date endDate = null;
    private int totalDuration = 0;
    private String memoryPeak = " - ";
    private SimpleDateFormat formatter = new SimpleDateFormat("dd/MM/yyyy HH:mm:ss");

    public JsonTestResult(String jsonName) {
        this.jsonName = jsonName;
        graphTestResultList = new ArrayList<>();
    }

    public JsonTestResult(String jsonName, ArrayList<GraphTestResult> graphTestResultList) {
        this.jsonName = jsonName;
        this.graphTestResultList = graphTestResultList;
        refreshStatus();
    }

    private void refreshStatus(){
        if(graphTestResultList.size() > 0) {
            status = "PASSED";
        } else {
            status = "UNKNOWN";
            return;
        }
        for(GraphTestResult graphTestResult : graphTestResultList) {
            if(graphTestResult.getStatus().equals("FAILED")) {
                status = "FAILED";
                return;
            }
            if(graphTestResult.getStatus().equals("SKIPPED")) {
                status = "SKIPPED";
                return;
            }
            if(graphTestResult.getStatus().equals("UNKNOWN")) {
                status = "UNKNOWN";
            }
        }
    }

    public String getJsonName() {
        return jsonName;
    }

    public void addGraphTestResults(GraphTestResult graphTestResult) {
        graphTestResultList.add(graphTestResult);
        totalDuration = totalDuration + graphTestResult.getExecutionTime();
        refreshStatus();
    }

    public GraphTestResult[] getGraphTestResultArray() {
        return graphTestResultList.toArray(new GraphTestResult[graphTestResultList.size()]);
    }

    public String getStatus() {
        return status;
    }

    public Date getStartDate() {
        return startDate;
    }

    public void setStartDate(Date startDate) {
        this.startDate = startDate;
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

    public int getTotalDuration() {
        return totalDuration;
    }
}
