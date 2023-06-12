package org.esa.snap.test;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;

/**
 * Created by obarrile on 12/09/2019.
 */
public class IndexGenerator {
    public static void main(String[] args) {

        if (args.length != 2) {
            System.out.println("The expected arguments are: [reportFolder] [scope] ");
            return;
        }

        Path reportFolder = Paths.get(args[0]);
        String scope = args[1];

        if (reportFolder == null) {
            System.out.println("Report folder is null");
            return;
        }

        if (Files.notExists(reportFolder)) {
            System.out.println("Report folder does not exist");
            return;
        }

        try {
            ReportUtils.createHtmlReportIndex (reportFolder, scope);
        } catch (IOException e) {
            System.out.println("Html index cannot be created: " + e.getMessage());
        }

        return;
    }
}