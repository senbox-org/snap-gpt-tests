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

// Take the string and echo it.
def transformIntoStep(item, jsonString, scope, outputDir) {
    // We need to wrap what we return in a Groovy closure, or else it's invoked
    // when this method is called, not when we pass it to parallel.
    // To do this, you need to wrap the code below in { }, and either return
    // that explicitly, or use { -> } syntax.
    return {
        build job: "test", parameters: [
                [$class: 'StringParameterValue', name: 'jsonPath', value: "${item}"],
                [$class: 'StringParameterValue', name: 'testScope', value: "${scope}"],
                [$class: 'StringParameterValue', name: 'outputReportDir', value: "${outputDir}"]
            ],
            quietPeriod: 5,
            propagate: true,
            wait: true
    }
}

def launchJobs(jsonString, scope, outputDir) {

    def jobs = [:]
    println "List of Json file : " + jsonString
    jsonList = jsonString.split("\n")
    num = 0
    for (int i=0; i < jsonList.size(); i++) {
    //jsonList.each { item ->
        item = jsonList[i]
        echo "Schedule job for json file : " + item
        // path = item - "["
        // path = path - "]"
        jobs["GPT Test ${num}"] = {
            build job: "test", parameters: [
                    [$class: 'StringParameterValue', name: 'jsonPath', value: "${item}"],
                    [$class: 'StringParameterValue', name: 'testScope', value: "${scope}"],
                    [$class: 'StringParameterValue', name: 'outputReportDir', value: "${outputDir}"]
                ],
                propagate: true,
                wait: true
        }
        num++
    }
    // return jobs
    parallel jobs
}

pipeline {

    environment {
        branchVersion = sh(returnStdout: true, script: "echo ${env.GIT_BRANCH} | cut -d '/' -f 2").trim()
        outputDir = "/home/snap/output/${branchVersion}/${env.BUILD_NUMBER}"
    }
    agent { label 'snap-test' }
    parameters {
        string(name: 'dockerTagName', defaultValue: 's2tbx:testJenkins_validation', description: 'Snap version to use to launch tests')
        string(name: 'testScope', defaultValue: 'REGULAR', description: 'Scope of the tests to launch (PUSH, DAILY, REGULAR, WEEKLY, RELEASE)')
        string(name: 'propertiesPath', defaultValue: '', description: 'Command to launch (gpt command including required parameters)')
        string(name: 'outputReportDir', defaultValue: '/home/snap/', description: 'Path to directory where gpt test will write report')
        string(name: 'jsonPath', defaultValue: '', description: 'Command to launch (gpt command including required parameters)')
        // string(name: 'LabelParameterValue', defaultValue: 'snap-test', description: 'Label to use to launch gpt tests')
        // string(name: 'project', defaultValue: 's2tbx', description: 'Scope of the tests to launch (PUSH, NIGHTLY, WEEKLY, RELEASE)')
    }
    stages {
        stage('Filter JSON') {
            when {
                expression {
                    // run this stage only when json path is NOT specified
                    return "${params.jsonPath}" == '';
                }
            }
            agent {
                docker {
                    image "snap-build-server.tilaa.cloud/maven:3.6.0-jdk-8"
                    args "-e MAVEN_CONFIG=/var/maven/.m2 -v /opt/maven/.m2/settings.xml:/var/maven/.m2/settings.xml -v docker_gpt_test_results:/home/snap/output/"
                }
            }
            steps {
                echo "Launch Filter JSON from ${env.JOB_NAME} from ${env.GIT_BRANCH} with commit ${env.GIT_COMMIT} using docker image snap-build-server.tilaa.cloud/${params.dockerTagName}"
                sh "mkdir -p ${outputDir}"
                // sh "mvn -Duser.home=/var/maven clean package install"
                sh "java -jar ./gpt-tests-executer/target/FilterTestJSON.jar ./gpt-tests-resources/tests ${params.testScope} ${outputDir}"
                sh "more ${outputDir}/JSONTestFiles.txt"
                sh "cp -r ./gpt-tests-executer/target/ ${outputDir}/gptExecutorTarget"
                // sh "/opt/launchGpt.sh ${propertiesFilePath} ${outputDir}/FilterJson.vsofig ${scope}"
            }
        }
        stage('Launch Jobs') {
            when {
                expression {
                    // run this stage only when json path is NOT specified
                    return "${params.jsonPath}" == '';
                }
            }
            agent {
                docker {
                    image "snap-build-server.tilaa.cloud/scripts:1.0"
                    args "-v docker_gpt_test_results:/home/snap/output/"
                }
            } 
            steps {
                script {
                    jsonString = sh(returnStdout: true, script: "cat ${outputDir}/JSONTestFiles.txt").trim()
                    //println "jsonString " + jsonString
                    //jsonList = jsonString.split("\n")
                    //jsonList.each { item->
                    //    println "loop " + item
                    //}
                    // def jobs = launchJobs(jsonString, testScope, outputDir)
                }
                echo "Launch Jobs from ${env.JOB_NAME} from ${env.GIT_BRANCH} with commit ${env.GIT_COMMIT} using docker image snap-build-server.tilaa.cloud/${params.dockerTagName}"
                // echo "List of json files : ${jsonString}"
                launchJobs("${jsonString}", "${testScope}", "${outputDir}")
                // parallel jobs
            }
        }
        stage('Json Executer') {
            when {
                expression {
                    return "${params.jsonPath}" != '';
                }
            }
            agent  {
                docker {
                    label 'snap'
                    image "snap-build-server.tilaa.cloud/${dockerTagName}"
                    args '-v /data/ssd/testData/:/data/ssd/testData/ -v /opt/snap-gpt-tests/gpt-tests-executer.properties:/opt/snap-gpt-tests/gpt-tests-executer.properties -v docker_gpt_test_results:/home/snap/output/'
                }
            }
            steps {
                echo "Launch GPT Tests from ${env.JOB_NAME} from ${env.GIT_BRANCH} with commit ${env.GIT_COMMIT}"
                sh "mkdir -p ${outputReportDir}/report"
                sh "mkdir -p /home/snap/tmpDir"
                sh "/home/snap/snap/jre/bin/java -jar ${outputReportDir}/gptExecutorTarget/SnapGPTTest-jar-with-dependencies.jar /opt/snap-gpt-tests/gpt-tests-executer.properties ${params.testScope} ${params.jsonPath} ${outputReportDir}/report"
            }
        }
    }
    /*post {
        failure {
            step (
                emailext(
                    subject: "[SNAP] JENKINS-NOTIFICATION: ${currentBuild.result ?: 'SUCCESS'} : Job '${env.JOB_NAME} [${env.BUILD_NUMBER}]'",
                    body: """Build status : ${currentBuild.result ?: 'SUCCESS'}: Job '${env.JOB_NAME} [${env.BUILD_NUMBER}]':
Check console output at ${env.BUILD_URL}
${env.JOB_NAME} [${env.BUILD_NUMBER}]""",
                    attachLog: true,
                    compressLog: true,
                    recipientProviders: [[$class: 'CulpritsRecipientProvider'], [$class:'DevelopersRecipientProvider']]
                )
            )
        }
    }*/
}
