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

pipeline {
    environment {
        branchVersion = sh(returnStdout: true, script: "echo ${env.GIT_BRANCH} | cut -d '/' -f 2").trim()
        outputDir = "/home/snap/output/${branchVersion}/${env.BUILD_NUMBER}/"
    }
    agent { label 'snap-test' }
    parameters {
        string(name: 'dockerTagName', defaultValue: 's2tbx:testJenkins_validation', description: 'Snap version to use to launch tests')
        string(name: 'testScope', defaultValue: 'REGULAR', description: 'Scope of the tests to launch (PUSH, DAILY, REGULAR, WEEKLY, RELEASE)')
        string(name: 'propertiesPath', defaultValue: '', description: 'Command to launch (gpt command including required parameters)')
        string(name: 'outputReportDir', defaultValue: '/home/snap/', description: 'Path to directory where gpt test will write report')
        string(name: 'jsonPath', defaultValue: '', description: 'Command to launch (gpt command including required parameters)')
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
                    args "-e MAVEN_CONFIG=/var/maven/.m2 -v /opt/maven/.m2/settings.xml:/var/maven/.m2/settings.xml -v docker_gpt_test_results:${outputDir}"
                }
            }
            steps {
                echo "Launch Filter JSON from ${env.JOB_NAME} from ${env.GIT_BRANCH} with commit ${env.GIT_COMMIT} using docker image snap-build-server.tilaa.cloud/${params.dockerTagName}"
                sh "mkdir -p ${outputDir}"
                sh "mvn -X -Duser.home=/var/maven clean package install"
                sh "java -jar ./gpt-tests-executer/target/FilterTestJSON.jar ./gpt-tests-resources/tests ${params.testScope} ${outputDir}"
                sh "more ${outputDir}/JSONTestFiles.txt"
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
            agent { label 'snap-test' }
            steps {
                script {
                    jsonList = sh(returnStdout: true, script: "cat ${params.jsonPath}").trim()
                }
                echo "Launch Jobs from ${env.JOB_NAME} from ${env.GIT_BRANCH} with commit ${env.GIT_COMMIT} using docker image snap-build-server.tilaa.cloud/${params.dockerTagName}"
                println "${jsonList}"
                echo "${jsonList}"
                
                // sh "mkdir -p ${outputDir}"
                // sh "mvn -Duser.home=/var/maven clean package install"
                // sh "/opt/launchGpt.sh ${propertiesFilePath} ${outputDir}/FilterJson.vsofig ${scope}"
            }
        }
        stage('Json Executer') {
            when {
                expression {
                    return "${params.jsonPath}" != '';
                }
            }
            agent { label 'snap-execution' } {
                docker {
                    image "snap-build-server.tilaa.cloud/${params.dockerTagName}"
                    args '-v /data/ssd/testData/:/data/ssd/testData/'
                }
            }
            steps {
                echo "Launch GPT Tests from ${env.JOB_NAME} from ${env.GIT_BRANCH} with commit ${env.GIT_COMMIT} using docker image snap-build-server.tilaa.cloud/${params.dockerTagName}"
                sh "mkdir -p ${outputDir}/report"
                sh "mkdir -p ${outputDir}/tmpDir"
                sh 'mvn install'
                sh 'java -jar ./gpt-tests-executer/target/SnapGPTTest.jar ${params.properties} ${params.testScope} ${params.jsonPath} ${outputReportDir}/report'
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
