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


def launchJobsSeq(jsonString, scope, outputDir, saveOutput, debug) {
    println "List of sequentials Json file : " + jsonString
    jsonString = jsonString.trim()
    jsonList = jsonString.split("\n")
    num = 0
    status = true
    sh script:"mkdir -p ${outputDir}/report", label: "create report directory"
    for (int i=0; i < jsonList.size(); i++) {
        item = jsonList[i]
        def currentJsonFile = "" + item
        if (currentJsonFile.trim() != "") {
            try {
                sh script:"export LD_LIBRARY_PATH=. && python3 -u ${outputDir}/pygpt/snap_gpt_test.py '/home/snap/snap/jre/bin/java' '-cp ${outputDir}/gptExecutorTarget/TestOutput.jar' 'org.esa.snap.test.TestOutput' /opt/snap-gpt-tests/gpt-tests-executer.properties \"${scope}\" ${currentJsonFile} ${outputDir}/report ${saveOutput} --debug=${debug}", label: "Execute testset \"${currentJsonFile}\""
            } catch (all) {
                echo "A test from the testset \"${currentJsonFile}\" failed"
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
        booleanParam(name: 'debug', defaultValue: false, description: 'Save gpt debug output')
        string(name: 'reportsDB', defaultValue: "conf:///opt/snap-gpt-tests/snap-db.conf", description: "database to use for saving outputs and performances (sqlite://path or mysql://user:root@host:port/db)")
    }
   
    stages {
        stage('Build project') {
            agent {
                docker {
                    image "snap-build-server.tilaa.cloud/snap-ci:master"
                    label 'snap-test'
                    args "-e MAVEN_CONFIG=/var/maven/.m2 -v /opt/maven/.m2/settings.xml:/var/maven/.m2/settings.xml -v docker_gpt_test_results:/home/snap/output/"
                }
            }
            steps {
                echo "Build project from ${env.JOB_NAME} from ${env.GIT_BRANCH} with commit ${env.GIT_COMMIT} using docker image snap-build-server.tilaa.cloud/${params.dockerTagName}"
                sh script:"mkdir -p ${outputDir}/report", label: "initialize environment"
                sh script:"mvn -Duser.home=/var/maven clean package install -U", label: "build product check java tool"

                echo "Copy build to working directory..."
                sh script:"cp -r ./gpt-tests-executer/target/ ${outputDir}/gptExecutorTarget", label: "copy java tool"
                sh script:"cp -R ./pygpt/ ${outputDir}/pygpt", label: "copy python execution tools"
                sh script:"cp -R ./pygpt/templates ${outputDir}/templates && cp -R ./pygpt/statics ${outputDir}/statics", label: "copy report templates resources"
            }
        }
        stage('Execute Tests') {
            agent {
                docker {
                    label 'snap'
                    image "snap-build-server.tilaa.cloud/${dockerTagName}"
                    args '-v /data/ssd/testData/:/data/ssd/testData/ -v /data/ssd/testData/report:/report/ -v /opt/snap-gpt-tests/:/opt/snap-gpt-tests/ -v docker_gpt_test_results:/home/snap/output/'
                }
            }
            steps {
                sh script:"python3 -u ./pygpt/check_jsons.py ./gpt-tests-resources/tests", label: "Check JSON tests integrity"
    
                sh script:"python3 -u ./pygpt/filter_json.py ./gpt-tests-resources/tests \"${params.testScope}\" ${outputDir}", label: "Filter tests with test-scope: \"${params.testScope}\""
                sh script:"more ${outputDir}/JSONTestFiles.txt", label: "List tests that will be executed"
                
                script {
                    jsonString = sh(returnStdout: true, script: "cat ${outputDir}/JSONTestFiles.txt").trim()
                }
                
                echo "Launch long Jobs from ${env.JOB_NAME} from ${env.GIT_BRANCH} with commit ${env.GIT_COMMIT} using docker image snap-build-server.tilaa.cloud/${params.dockerTagName}"
                launchJobsSeq("${jsonString}", "${testScope}", "${outputDir}", params.saveOutput, params.debug)
            }
            post {
                always{

                    sh script:"rm -rf $WORKSPACE/report", label: "clean-up old report"
                    sh script:"mkdir $WORKSPACE/report && mkdir $WORKSPACE/report/output", label: "initialize final report directory"
                    sh script:"cp -r ${outputDir}/report/* $WORKSPACE/report/output/", label: "copy gnerated log files"
                    sh script:"cp -r ${outputDir}/statics/* $WORKSPACE/report/", label: "copy report resources"

                    sh script:"cat $WORKSPACE/report/output/Report_*.txt > $WORKSPACE/report/output/report.txt", label: "join execution status logs"
                    sh script:"mv $WORKSPACE/report/output/json $WORKSPACE/report/ && mv $WORKSPACE/report/output/performances $WORKSPACE/report/ && mv $WORKSPACE/report/output/images $WORKSPACE/report/", label: "re-orginize copied logs"
                
                    echo "Updating database"
                    sh script:"python3 -u ./pygpt/stats_db.py ${params.reportsDB} ${dockerTagName} ${params.testScope} $WORKSPACE/report ${env.BUILD_NUMBER} ${env.GIT_BRANCH}", label: "update \"reports\" remote database"
                   
                    echo "Generate report"
                    sh script:"python3 -u ./pygpt/report_utils.py ${outputDir}/templates $WORKSPACE/report \"${params.testScope}\" ${dockerTagName} ${params.reportsDB}", label: "generate local HTML report"
                   
                    archiveArtifacts artifacts: "report/**/*.*", fingerprint: true
                    sh script:"rm -rf report && rm -rf ${outputDir}/*", label: "clean-up files"
                }
            }
        }
    }
    post {
         failure {
             script {
                     // send mail only on main job
                     if ("${params.testScope}" == 'REGULAR' || "${params.testScope}" == 'WEEKLY' || "${params.testScope}" == 'RELEASE') {
                        echo "The test failed!"
                     } else if("${params.testScope}" == 'DAILY'){
                        emailext(
                                 subject: "[SNAP] JENKINS - SAVED OUTPUTS: ${currentBuild.result ?: 'SUCCESS'} : Job '${env.JOB_NAME} [${env.BUILD_NUMBER}]'",
                                 body: """Build status : ${currentBuild.result ?: 'SUCCESS'}: Job '${env.JOB_NAME} [${env.BUILD_NUMBER}]':
Check console output at ${env.BUILD_URL}
${env.JOB_NAME} [${env.BUILD_NUMBER}]""",
                                 attachLog: false,
                                 compressLog: false,
                                 to: 'stb-internal@step-email.net,stb-developers@step-email.net')
                     }
             }
         }

    }
}
