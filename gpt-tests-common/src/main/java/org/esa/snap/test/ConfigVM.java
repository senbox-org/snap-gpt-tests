package org.esa.snap.test;

import com.fasterxml.jackson.annotation.JsonProperty;

public class ConfigVM {

    private String xmx;
    private String cacheSize;
    private String parallelism;

    public ConfigVM(){
        // default constructor needed for Jackson to avoid exception ...
    }

    public ConfigVM(String xmx, String cacheSize, String parallelism){
        this.xmx = xmx;
        this.cacheSize = cacheSize;
        this.parallelism = parallelism;
    }

    public ConfigVM(ConfigVM configVM){
        this.xmx = configVM.getXmX();
        this.cacheSize = configVM.getCacheSize();
        this.parallelism = configVM.getParallelism();
    }

    @JsonProperty("xmx")
    public String getXmX() {
        return xmx;
    }

    public void setXmX(String XmX) {
        this.xmx = XmX;
    }

    @JsonProperty("cacheSize")
    public String getCacheSize() { return cacheSize; }

    public void setCacheSize(String cacheSize) { this.cacheSize = cacheSize; }

    @JsonProperty("parallelism")
    public String getParallelism() { return parallelism; }

    public void setParallelism(String parallelism) { this.parallelism = parallelism; }

}

