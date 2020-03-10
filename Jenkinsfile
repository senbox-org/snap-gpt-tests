#!/usr/bin/env groovy

/**
 * Copyright (C) 2019 CS-SI
 * This program is free software; you can redistribute it and/or modify it
 * under the terms of the GNU General Public License as published by the Free
 * Software Foundation; either version 3 of the License, or (at your option)
 * any later version.
 * This program is distributed in the hope that it will be useful, but WITHOUT
 * ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
 * FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
 * more details.
 *
 * You should have received a copy of the GNU General Public License along
 * with this program; if not, see http://www.gnu.org/licenses/
 */

/**
 * Launch jobs in parallel for every json file listed in jsonString separated by '\n'
 */
def launchJobs(jsonString, scope, outputDir, saveOutput) {

    def jobs = [:]
    println "List of parallel Json file : " + jsonString
    jsonString = jsonString.trim()
    jsonList = jsonString.split("\n")
    num = 0
    status = true
    for (int i=0; i < jsonList.size(); i++) {
    //jsonList.each { item ->
        item = jsonList[i]
        def currentJsonFile = "" + item
        if (currentJsonFile.trim() != "") {

            echo "Schedule job for json file : " + item
            jobs["GPT Test ${num} ${item}"] = {
                b = build(job: "gpt-executor", parameters: [
                // build job: "test", parameters: [
                        [$class: 'StringParameterValue', name: 'gptBranchVersion', value: "${branchVersion}"],
                        [$class: 'StringParameterValue', name: 'dockerTagName', value: "${dockerTagName}"],
                        [$class: 'StringParameterValue', name: 'jsonPath', value: currentJsonFile],
                        [$class: 'StringParameterValue', name: 'testScope', value: "${scope}"],
                        [$class: 'StringParameterValue', name: 'outputReportDir', value: "${outputDir}"],
                        [$class: 'BooleanParameterValue', name: 'java', value: false],
                        [$class: 'BooleanParameterValue', name: 'saveOutput', value: saveOutput]
                    ],
                    quietPeriod: 0,
                    propagate: false,
                    wait: true).result
                if(b == 'FAILURE') {
                    echo "The job " + item + " failed."
                    // currentBuild.result = 'FAILURE'
                    status = false
                }
            }
        }
        num++
    }

    if (!status) {
        throw new Exception("At least one test failed")
    }
    // return jobs
    parallel jobs
}

def launchJobsSeq(jsonString, scope, outputDir, saveOutput) {

    def jobs = [:]
    println "List of sequentials Json file : " + jsonString
    jsonString = jsonString.trim()
    jsonList = jsonString.split("\n")
    num = 0
    status = true
    for (int i=0; i < jsonList.size(); i++) {
        item = jsonList[i]
        def currentJsonFile = "" + item
        if (currentJsonFile.trim() != "") {
            sh "mkdir -p ${outputDir}/report"
            try {
                sh "export LD_LIBRARY_PATH=. && python3 -u ${outputDir}/pygpt/snap_gpt_test.py '/home/snap/snap/jre/bin/java' '-Dncsa.hdf.hdflib.HDFLibrary.hdflib=/home/snap/snap/snap/modules/lib/amd64/libjhdf.so -Dncsa.hdf.hdf5lib.H5.hdf5lib=/home/snap/snap/snap/modules/lib/amd64/libjhdf5.so -cp ${outputDir}/gptExecutorTarget/TestOutput.jar' 'org.esa.snap.test.TestOutput' /opt/snap-gpt-tests/gpt-tests-executer.properties \"${scope}\" ${currentJsonFile} ${outputDir}/report ${saveOutput}"            
            } catch (all) {
                echo "A test failed"
                status = false
            }
        }
        num++
    }
    if (!status) {
        throw new Exception("At least one test failed")
    }
}

pipeline {
    agent { label 'snap-test' }
    
    options {
        buildDiscarder(logRotator(daysToKeepStr: '30', artifactDaysToKeepStr: '30'))
        timeout(time: 20, unit: 'HOURS')
    }

    environment {
        branchVersion = sh(returnStdout: true, script: "echo ${env.GIT_BRANCH} | cut -d '/' -f 2").trim()
        outputDir = "/home/snap/output/${branchVersion}/${env.BUILD_NUMBER}"
    }
    parameters {
        string(name: 'dockerTagName', defaultValue: "snap:master", description: 'Snap version to use to launch tests')
        string(name: 'testScope', defaultValue: 'REGULAR', description: 'Scope of the tests to launch (REGULAR, DAILY, WEEKLY, RELEASE)')
        booleanParam(name: 'saveOutput', defaultValue: false, description: 'Save output of failed tests (if scope is not [REGULAR, DAILY, WEEKLY, RELEASE])')
        booleanParam(name: 'parallel', defaultValue: true, description: 'Execute the test jobs in parallel')
        string(name: 'reportsDB', defaultValue: "sqlite:///report/db/statistics.db", description: "database to use for saving outputs and performances (sqlite://path or mysql://user:root@host:port/db)")
    }
   
    stages {
        stage('Build project') {
            agent {
                docker {
                    image "snap-build-server.tilaa.cloud/maven:3.6.0-jdk-8"
                    label 'snap-test'
                    args "-e MAVEN_CONFIG=/var/maven/.m2 -v /opt/maven/.m2/settings.xml:/var/maven/.m2/settings.xml -v docker_gpt_test_results:/home/snap/output/"
                }
            }
            steps {
                echo "Build project from ${env.JOB_NAME} from ${env.GIT_BRANCH} with commit ${env.GIT_COMMIT} using docker image snap-build-server.tilaa.cloud/${params.dockerTagName}"
                sh "mkdir -p ${outputDir}"
                sh "mvn -Duser.home=/var/maven clean package install"

                echo "Copy build to working directory..."
                sh "cp -r ./gpt-tests-executer/target/ ${outputDir}/gptExecutorTarget"
                sh "ls  ${outputDir}/gptExecutorTarget"
                sh "cp -R ./pygpt/ ${outputDir}/pygpt" // << Copy profiler and libraries
                sh "cp -R ./pygpt/templates ${outputDir}/templates" 
                sh "cp -R ./pygpt/statics ${outputDir}/statics" 
            }
        }
        stage('Execute Tests') {
            agent {
                docker {
                    label 'snap'
                    image "snap-build-server.tilaa.cloud/${dockerTagName}"
                    args '-v /data/ssd/testData/:/data/ssd/testData/ -v /data/ssd/testData/report:/report/ -v /opt/snap-gpt-tests/gpt-tests-executer.properties:/opt/snap-gpt-tests/gpt-tests-executer.properties -v docker_gpt_test_results:/home/snap/output/'
                }
            }
            steps {
                echo "Checkin json test integrity..."
                sh "python3 -u ./pygpt/check_jsons.py ./gpt-tests-resources/tests"
                
                echo "Filtering json files..."
                sh "python3 -u ./pygpt/filter_json.py ./gpt-tests-resources/tests \"${params.testScope}\" ${outputDir}"
                sh "more ${outputDir}/JSONTestFiles.txt"
                sh "more ${outputDir}/JSONTestFilesSeq.txt"
                
                script {
                    jsonString = sh(returnStdout: true, script: "cat ${outputDir}/JSONTestFiles.txt").trim()
                    jsonStringSeq = sh(returnStdout: true, script: "cat ${outputDir}/JSONTestFilesSeq.txt").trim()
                }
           
                script {
                    if (params.parallel == false) {
                        echo "Launch seq Jobs from ${env.JOB_NAME} from ${env.GIT_BRANCH} with commit ${env.GIT_COMMIT} using docker image snap-build-server.tilaa.cloud/${params.dockerTagName}"
                        launchJobsSeq("${jsonString}", "${testScope}", "${outputDir}", params.saveOutput)
                    } else {
                        echo "Launch parallel Jobs from ${env.JOB_NAME} from ${env.GIT_BRANCH} with commit ${env.GIT_COMMIT} using docker image snap-build-server.tilaa.cloud/${params.dockerTagName}"
                        launchJobs("${jsonString}", "${testScope}", "${outputDir}", params.saveOutput)
                    }
                }
                echo "Launch seq Jobs from ${env.JOB_NAME} from ${env.GIT_BRANCH} with commit ${env.GIT_COMMIT} using docker image snap-build-server.tilaa.cloud/${params.dockerTagName}"
                // echo "List of json files : ${jsonString}"
                launchJobsSeq("${jsonStringSeq}", "${testScope}", "${outputDir}", params.saveOutput)
                // parallel jobs
            }
            post {
                always{

                    sh "rm -rf $WORKSPACE/report"
                    sh "mkdir $WORKSPACE/report && mkdir $WORKSPACE/report/output"
                    sh "cp -r ${outputDir}/report/* $WORKSPACE/report/output/"
                    sh "cp -r ${outputDir}/statics/* $WORKSPACE/report/" 

                    sh "cat $WORKSPACE/report/output/Report_*.txt > $WORKSPACE/report/output/report.txt"
                    sh "mv $WORKSPACE/report/output/json $WORKSPACE/report/ && mv $WORKSPACE/report/output/performances $WORKSPACE/report/ && mv $WORKSPACE/report/output/images $WORKSPACE/report/"
                
                    sh "ls $WORKSPACE/report/json/"
                   
                    echo "Updating database"
                    sh "python3 -u ./pygpt/stats_db.py /report/db/statistics.db ${dockerTagName} ${params.testScope} $WORKSPACE/report ${env.BUILD_NUMBER} ${env.GIT_BRANCH}"
                   
                    echo "Generate report"
                    sh "python3 -u ./pygpt/report_utils.py ${outputDir}/templates $WORKSPACE/report \"${params.testScope}\" ${dockerTagName} ${params.reportsDB}"
                   
                    archiveArtifacts artifacts: "report/**/*.*", fingerprint: true
                    sh "rm -rf report" 
                }
            }
        }
    }
    post {
         failure {
             script {
                     // send mail only on main job
                     if ("${params.testScope}" == 'REGULAR' || "${params.testScope}" == 'DAILY' || "${params.testScope}" == 'WEEKLY' || "${params.testScope}" == 'RELEASE') {
                       sh "echo `ERROR!`"
                     } else if ("${params.saveOutput}" == 'true') {
                         emailext(
                                 subject: "[SNAP] JENKINS - SAVED OUTPUTS: ${currentBuild.result ?: 'SUCCESS'} : Job '${env.JOB_NAME} [${env.BUILD_NUMBER}]'",
                                 body: """Build status : ${currentBuild.result ?: 'SUCCESS'}: Job '${env.JOB_NAME} [${env.BUILD_NUMBER}]':
Check console output at ${env.BUILD_URL}
${env.JOB_NAME} [${env.BUILD_NUMBER}]""",
                                 attachLog: false,
                                 compressLog: false,
                                 to: 'omar.barrilero@c-s.fr,martino.ferrari@c-s.fr,jean.seyral@c-s.fr')
                     }
             }
         }

    }
}
