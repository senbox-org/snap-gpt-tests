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
def launchJobs(jsonString, scope, outputDir) {

    def jobs = [:]
    println "List of Json file : " + jsonString
    jsonString = jsonString.trim()
    jsonList = jsonString.split("\n")
    num = 0
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
                        [$class: 'StringParameterValue', name: 'outputReportDir', value: "${outputDir}"]
                    ],
                    quietPeriod: 0,
                    propagate: false,
                    wait: true).result
                if(b == 'FAILURE') {
                    echo "The job " + item + "failed."
                    currentBuild.result = 'FAILURE'
                }
            }
        }
        num++
    }
    // return jobs
    parallel jobs
}

def launchJobsSeq(jsonString, scope, outputDir) {

    def jobs = [:]
    println "List of Json file : " + jsonString
    jsonString = jsonString.trim()
    jsonList = jsonString.split("\n")
    num = 0
    for (int i=0; i < jsonList.size(); i++) {
        item = jsonList[i]
        def currentJsonFile = "" + item
        if (currentJsonFile.trim() != "") {
            echo "Schedule job for json file : " + item

                b = build(job: "gpt-executor", parameters: [
                        // build job: "test", parameters: [
                        [$class: 'StringParameterValue', name: 'gptBranchVersion', value: "${branchVersion}"],
                        [$class: 'StringParameterValue', name: 'dockerTagName', value: "${dockerTagName}"],
                        [$class: 'StringParameterValue', name: 'jsonPath', value: currentJsonFile],
                        [$class: 'StringParameterValue', name: 'testScope', value: "${scope}"],
                        [$class: 'StringParameterValue', name: 'outputReportDir', value: "${outputDir}"]
                ],
                        quietPeriod: 0,
                        propagate: false,
                        wait: true).result

            if(b == 'FAILURE') {
                echo "The job " + item + "failed."
                currentBuild.result = 'FAILURE'
            }
            
        }
        num++
    }
}

pipeline {

    options {
        buildDiscarder(logRotator(daysToKeepStr: '30', artifactDaysToKeepStr: '30'))
        timeout(time: 20, unit: 'HOURS')
    }

    environment {
        branchVersion = sh(returnStdout: true, script: "echo ${env.GIT_BRANCH} | cut -d '/' -f 2").trim()
        outputDir = "/home/snap/output/${branchVersion}/${env.BUILD_NUMBER}"
    }
    agent { label 'snap-test' }
    parameters {
        string(name: 'dockerTagName', defaultValue: "snap:master", description: 'Snap version to use to launch tests')
        string(name: 'testScope', defaultValue: 'REGULAR', description: 'Scope of the tests to launch (REGULAR, DAILY, WEEKLY, RELEASE)')
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
            }
        }
        stage('Filter JSON') {
            agent {
                docker {
                    image "snap-build-server.tilaa.cloud/scripts:1.0"
                    label 'snap-test'
                    args  "-v docker_gpt_test_results:/home/snap/output/"
                }
            }
            steps {
                echo "Filtering json files..."
                sh "python3 ./gpt-tests-executer/target/classes/filter_json.py ./gpt-tests-resources/tests \"${params.testScope}\" ${outputDir}"
                sh "more ${outputDir}/JSONTestFiles.txt"
                sh "more ${outputDir}/JSONTestFilesSeq.txt"
                sh "cp -r ./gpt-tests-executer/target/ ${outputDir}/gptExecutorTarget"
                sh "cp ./gpt-tests-executer/target/classes/*.py ${outputDir}/" // << Copy profiler and libraries
                sh "cp -R ./gpt-tests-executer/target/classes/templates ${outputDir}/templates" 
                sh "cp -R ./gpt-tests-executer/target/classes/statics ${outputDir}/statics" 
            }
        }
        stage('Launch Jobs') {
            agent {
                docker {
                    image "snap-build-server.tilaa.cloud/scripts:1.0"
                    label 'snap-test'
                    args  "-v docker_gpt_test_results:/home/snap/output/"
                }
            } 
            steps {
                script {
                    jsonString = sh(returnStdout: true, script: "cat ${outputDir}/JSONTestFiles.txt").trim()
                    jsonStringSeq = sh(returnStdout: true, script: "cat ${outputDir}/JSONTestFilesSeq.txt").trim()
                }

                echo "Launch parallel Jobs from ${env.JOB_NAME} from ${env.GIT_BRANCH} with commit ${env.GIT_COMMIT} using docker image snap-build-server.tilaa.cloud/${params.dockerTagName}"
                // echo "List of json files : ${jsonString}"
                launchJobs("${jsonString}", "${testScope}", "${outputDir}")

                echo "Launch seq Jobs from ${env.JOB_NAME} from ${env.GIT_BRANCH} with commit ${env.GIT_COMMIT} using docker image snap-build-server.tilaa.cloud/${params.dockerTagName}"
                // echo "List of json files : ${jsonString}"
                launchJobsSeq("${jsonStringSeq}", "${testScope}", "${outputDir}")

                // parallel jobs
            }
            post {
                always {
                    sh "rm -rf $WORKSPACE/report"
                    sh "mkdir $WORKSPACE/report && mkdir $WORKSPACE/report/output"
                    sh "cp -r ${outputDir}/report/* $WORKSPACE/report/output/"
                    sh "cp -r ${outputDir}/statics/* $WORKSPACE/report/" 

                    sh "cat $WORKSPACE/report/output/Report_*.txt > $WORKSPACE/report/output/report.txt"
                    sh "mv $WORKSPACE/report/output/json $WORKSPACE/report/ && mv $WORKSPACE/report/output/perfs $WORKSPACE/report/ && mv $WORKSPACE/report/output/images $WORKSPACE/report/"
                    echo "Generate html index"
                    // sh "java -jar ${outputDir}/gptExecutorTarget/IndexGenerator.jar $WORKSPACE/report \"${params.testScope}\""
                    sh "python3 ${outputDir}/report_utils.py ${outputDir}/templates $WORKSPACE/report \"${params.testScope}\" ${dockerTagName}"
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
                 }
             }
         }
    }
}
