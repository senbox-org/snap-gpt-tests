package org.esa.snap.test;

import javax.imageio.ImageIO;
import java.awt.*;
import java.awt.image.BufferedImage;
import java.io.BufferedReader;
import java.io.File;
import java.io.FileInputStream;
import java.io.FileNotFoundException;
import java.io.FileReader;
import java.io.FileWriter;
import java.io.IOException;
import java.io.InputStream;
import java.io.StringWriter;
import java.lang.reflect.InvocationTargetException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.text.ParseException;
import java.text.SimpleDateFormat;
import java.util.*;
import java.util.stream.Collectors;
import java.util.stream.Stream;

import org.apache.commons.io.filefilter.TrueFileFilter;
import org.apache.commons.io.filefilter.WildcardFileFilter;
import org.apache.velocity.Template;
import org.apache.velocity.VelocityContext;
import org.apache.velocity.app.VelocityEngine;
import org.apache.velocity.runtime.RuntimeConstants;
import org.apache.velocity.runtime.resource.loader.ClasspathResourceLoader;
import org.esa.snap.core.gpf.graph.GraphException;
import org.esa.snap.core.util.io.FileUtils;
import org.esa.snap.graphbuilder.rcp.dialogs.support.GraphExecuter;
import org.esa.snap.graphbuilder.rcp.dialogs.support.GraphPanel;
import org.jsoup.Jsoup;
import org.jsoup.nodes.Document;
import org.jsoup.nodes.Element;
import org.jsoup.select.Elements;

/**
 * Created by obarrile on 07/07/2019.
 */
public class ReportUtils {

    public static void createHtmlReportForJson (GraphTestResult[] graphTestResults, String jsonName, Path outputPath, String scope) throws IOException {
        VelocityEngine velocityEngine = new VelocityEngine();
        velocityEngine.setProperty(RuntimeConstants.RESOURCE_LOADER, "classpath");
        velocityEngine.setProperty("classpath.resource.loader.class", ClasspathResourceLoader.class.getName());
        velocityEngine.init();

        Template template = velocityEngine.getTemplate("gptTest_report_template.vm");

        VelocityContext context = new VelocityContext();
        context.put("graphTestResults", graphTestResults);
        context.put("jsonName", jsonName);
        context.put("operatingSystem", System.getProperty("os.name"));
        context.put("scope", scope);
        //compute start and end date
        Date start = new Date(Long.MAX_VALUE);
        Date end = new Date(Long.MIN_VALUE);
        Long totalDuration = 0L;
        float memoryPeak = 0f;
        for(GraphTestResult graphTestResult : graphTestResults) {
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

    }

    public static void createHtmlReportIndex (JsonTestResult[] jsonTestResults, Path outputPath, String scope) throws IOException {
        VelocityEngine velocityEngine = new VelocityEngine();
        velocityEngine.setProperty(RuntimeConstants.RESOURCE_LOADER, "classpath");
        velocityEngine.setProperty("classpath.resource.loader.class", ClasspathResourceLoader.class.getName());
        velocityEngine.init();

        Template template = velocityEngine.getTemplate("gptIndex_report_template.vm");

        VelocityContext context = new VelocityContext();
        context.put("jsonTestResults", jsonTestResults);
        context.put("operatingSystem", System.getProperty("os.name"));
        context.put("scope", scope);
        //compute start and end date
        Date start = new Date(Long.MAX_VALUE);
        Date end = new Date(Long.MIN_VALUE);
        Long totalDuration = 0L;
        for(JsonTestResult jsonTestResult : jsonTestResults) {
            if(jsonTestResult.getStartDate() != null) {
                if (jsonTestResult.getStartDate().before(start)) {
                    start = jsonTestResult.getStartDate();
                }
            }
            if(jsonTestResult.getEndDate() != null) {
                if(jsonTestResult.getEndDate().after(end)) {
                    end = jsonTestResult.getEndDate();
                }
            }
            totalDuration = totalDuration + jsonTestResult.getExecutionTime();
        }

        SimpleDateFormat formatter = new SimpleDateFormat("dd/MM/yyyy HH:mm:ss");
        context.put("startDateString", formatter.format(start));
        context.put("endDateString", formatter.format(end));
        context.put("totalTime", Math.round((end.getTime()-start.getTime())/1000));
        context.put("sumTime", totalDuration);


        FileWriter fileWriter = new FileWriter(outputPath.toFile());
        template.merge( context, fileWriter );
        fileWriter.close();

    }


    public static void createHtmlReportIndex (Path reportPath, String scope) throws IOException {
        Path htmlPath = reportPath.resolve("html");

        String[] htmlFilepaths = FileUtils.listFilePathsWithExtension(htmlPath.toFile(),"html");
        JsonTestResult[] jsonTestResults = new JsonTestResult[htmlFilepaths.length];

        for(int i = 0 ; i < htmlFilepaths.length ; i++) {
            jsonTestResults[i] = readJsonTestResult(htmlPath.resolve(htmlFilepaths[i]));
        }

        createHtmlReportIndex (jsonTestResults, htmlPath.resolve("index.html"), scope);
    }


    public static void generateGraphImage(File graphFileOrigin, File outputFile) {

        GraphExecuter exec = new GraphExecuter();
        try {
            // Before loading check if the presentation part exists and add it if not
            File graphFile = checkPresentationPart(graphFileOrigin);

            try {
                exec.loadGraph(new FileInputStream(graphFile), graphFile, false, true);

            } catch (GraphException ge) {
                // there are some $xxxxx in the xml with problem ...
                System.out.println("~~~~~ Dollars in " + graphFile);
                File modifiedGraphFile = replaceDollarVariables(graphFile);

                try {
                    exec.loadGraph(new FileInputStream(modifiedGraphFile), modifiedGraphFile, true, true);
                } catch (GraphException e) {
                    System.out.println("###### GraphException: for modified (dollar) file : " + modifiedGraphFile);
                    e.printStackTrace();
                    return;
                } catch (NullPointerException np) {
                    System.out.println("###### NullPointerException : for modified (dollar) file : " + modifiedGraphFile);
                    np.printStackTrace();
                    return;
                } catch (Exception e) {
                    System.out.println("##### Exception (!!!)");
                    e.printStackTrace();
                    return;
                }
                modifiedGraphFile.delete();
            }

            GraphPanel panel = new GraphPanel(exec);
            panel.setBackground(Color.WHITE);
            Dimension dim = getGraphDimension(graphFile);
            panel.setSize(dim);
            BufferedImage im = new BufferedImage(panel.getWidth(), panel.getHeight(), BufferedImage.TYPE_INT_ARGB);

            java.lang.reflect.Method myPaintComponent =
                    org.esa.snap.graphbuilder.rcp.dialogs.support.GraphPanel.class.getDeclaredMethod("paintComponent",
                                                                                                     java.awt.Graphics.class);
            myPaintComponent.setAccessible(true);
            myPaintComponent.invoke(panel, im.getGraphics());
//            panel.paintComponent(im.getGraphics());
            ImageIO.write(im, "PNG", outputFile);

        } catch (FileNotFoundException e) {
            System.out.println("File not found: " + graphFileOrigin);
            e.printStackTrace();
        } catch (IOException e) {
            System.out.println("File (IOexception): " + graphFileOrigin);
            e.printStackTrace();
        } catch (NoSuchMethodException | IllegalAccessException | InvocationTargetException e ) {
            System.out.println("Method paintComponent does not exist in GraphPanel");
            e.printStackTrace();
        }
    }

    private static File replaceDollarVariables(File graphFile) {

        File modifiedFile = null;
        try {
            String graphFileName = FileUtils.getFilenameWithoutExtension(graphFile);
            Path modifiedPath = Files.createTempFile(graphFileName, "_withoutDollars.xml");

            //            File newFile = FileUtils.exchangeExtension(graphFile,"_withoutDollars.xml");
            //            Path modifiedPath = get(newFile.toURI());

            Path graphPath = Paths.get(graphFile.toURI());
            try (Stream<String> lines = Files.lines(graphPath)) {
                java.util.List<String> replaced = lines
                        .map(line-> line.replaceAll(">\\$.*<", "><"))
                        .collect(Collectors.toList());
                Files.write(modifiedPath, replaced);
            }
            modifiedFile = modifiedPath.toFile();
        } catch (IOException e) {
            e.printStackTrace();
        }
        return modifiedFile;
    }
    private static File checkPresentationPart(File graphFile) {

//        boolean hasPresentation = false;
//        Scanner in = null;
//        try {
//            in = new Scanner(new FileReader(graphFile));
//            while(in.hasNextLine() && !hasPresentation) {
//                hasPresentation = in.nextLine().indexOf("<applicationData id=\"Presentation\">") >= 0;
//            }
//        } catch (FileNotFoundException e) {
//            e.printStackTrace();
//        } finally {
//            try {
//                in.close() ;
//            } catch(Exception e) { /* ignore */ }
//        }
//
//        if (!hasPresentation) System.out.println("###### Has NOT presentation " + hasPresentation);
//        File modifiedFile = null;
////        return modifiedFile;
        return graphFile;
    }

    private static Dimension getGraphDimension (File file) {
        BufferedReader reader;
        int x = 0;
        int y = 0;
        try {
            reader = new BufferedReader(new FileReader(file));
            String line = reader.readLine();
            while (line != null) {
                String preprocessedLine = line.replaceAll("\\s","");
                if(preprocessedLine.startsWith("<displayPosition")) {
                    String[] split = preprocessedLine.split("\"");
                    int newX;
                    int newY;
                    if (split[2].startsWith("y")) {
                        newX = Double.valueOf(split[1]).intValue();
                        newY = Double.valueOf(split[3]).intValue();
                    } else if (split[2].startsWith("x")){
                        newX = Double.valueOf(split[3]).intValue();
                        newY = Double.valueOf(split[1]).intValue();
                    } else {
                        System.out.println("##### Impossible to find x and y for line: " + line + " in file " + file.toString());
                        newX = 0;
                        newY = 0;
                    }
                    if(newX > x) {
                        x = newX;
                    }
                    if(newY > y) {
                        y = newY;
                    }

                }
                // read next line
                line = reader.readLine();
            }
            reader.close();
        } catch (IOException e) {
            e.printStackTrace();
        }
        x = x + 100;
        y = y + 70;
        return new Dimension(x,y);
    }

    public static void copyResource(String name, Path targetPath) {
        try (InputStream is = ReportUtils.class.getClassLoader().getResourceAsStream(name)) {
            Files.copy(is, targetPath);
        } catch (IOException e) {
            // An error occurred copying the resource
        }
    }

    public static JsonTestResult readJsonTestResult(Path htmlReportPath) {
        if(htmlReportPath == null || !Files.exists(htmlReportPath)) {
            return null;
        }


        Document doc = null;
        try {
            doc = Jsoup.parse(htmlReportPath.toFile(), "utf-8");
        } catch (IOException e) {
            return null;
        }

        JsonTestResult jsonTestResult = new JsonTestResult(FileUtils.getFilenameWithoutExtension(htmlReportPath.toFile()));

        SimpleDateFormat formatter = new SimpleDateFormat("dd/MM/yyyy HH:mm:ss");
        //Read start date
        Elements tables = doc.select("table");
        Element table = tables.get(3);
        Element rowDate = table.select("td").get(1);
        String start = rowDate.text();
        try {
            Date startDate = formatter.parse(start);
            jsonTestResult.setStartDate(startDate);
        } catch (ParseException e) {
            jsonTestResult.setStartDate(null);
        }

        tables = doc.select("table");
        table = tables.get(6);
        Elements rows = table.select("tr");

        for (int i = 1 ; i < rows.size() ; i++) {
            Element row = rows.get(i);
            Element status = row.select("img").get(1);
            String statusString = status.attr("alt");
            String duration = row.select("td").get(4).text();
            if(duration == "NULL" || duration.length() < 2) {
                duration = "0";
            } else {
                duration = duration.substring(0, duration.length() - 2);
            }

            GraphTest graphTest = new GraphTest();
            graphTest.setId(row.select("a").get(0).text());
            GraphTestResult graphTestResult = new GraphTestResult(graphTest);
            graphTestResult.setStatus(statusString);
            try {
                int iDuration = Integer.parseInt(duration);
                graphTestResult.setDuration(iDuration);
                graphTestResult.setStartDate(null);
                graphTestResult.setEndDate(null);
            } catch (NumberFormatException e) {
                //do nothing
            }
            jsonTestResult.addGraphTestResults(graphTestResult);
        }
        //TODO check if it is needed to read more items for report
        return jsonTestResult;
    }

}
