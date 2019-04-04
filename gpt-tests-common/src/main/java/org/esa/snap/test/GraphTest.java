package org.esa.snap.test;

import java.nio.file.Path;
import java.util.Map;

/**
 * Created by obarrile on 20/02/2019.
 */
public class GraphTest {

    private String id;
    private String description;
    private String frequency;
    private String graphPath;
    private Map<String, String> parameters;
    private Map<String, String> inputs;
    private Output[] outputs;

    public Map<String, String> getParameters() {
        return parameters;
    }
    public void setParameters(Map<String, String> properties) {
        this.parameters = properties;
    }

    public Map<String, String> getInputs() {
        return inputs;
    }
    public void setInputs(Map<String, String> properties) {
        this.inputs = properties;
    }

    public String getGraphPath() {
        return graphPath;
    }

    public void setGraphPath(String graphPath) {
        this.graphPath = graphPath;
    }

    public Output[] getOutputs() {
        return outputs;
    }

    public void setOutputs(Output[] outputs) {
        this.outputs = outputs;
    }

    public String getId() {
        return id;
    }

    public void setId(String id) {
        this.id = id;
    }

    public String getDescription() {
        return description;
    }

    public void setDescription(String description) {
        this.description = description;
    }

    public String getFrequency() {
        return frequency;
    }

    public void setFrequency(String frequency) {
        this.frequency = frequency;
    }

    public boolean inputExists(final Path inputFolder) {
        for (Map.Entry<String, String> entry : getInputs().entrySet()) {
            if(!inputFolder.resolve(entry.getValue()).toFile().exists()) {
                return false;
            }
        }
        return true;
    }
}
