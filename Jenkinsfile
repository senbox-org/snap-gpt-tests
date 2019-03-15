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
    agent { label 'snap-test' }
    parameters {
        string(name: 'dockerTagName', defaultValue: 's2tbx:testJenkins_validation', description: 'Snap version to use to launch tests')
        string(name: 'testScope', defaultValue: 'PUSH', description: 'Scope of the tests to launch (PUSH, NIGHTLY, WEEKLY, RELEASE)')
        string(name: 'jsonPath', defaultValue: '', description: 'Command to launch (gpt command including required parameters)')
        // string(name: 'project', defaultValue: 's2tbx', description: 'Scope of the tests to launch (PUSH, NIGHTLY, WEEKLY, RELEASE)')
    }
    stages {
        stage('Filter JSON') {
            when {
                expression {
                    return "${params.jsonPath}" == '';
                }
            }
            agent {
                docker {
                    image "snap-build-server.tilaa.cloud/${params.dockerTagName}"
                    args '-v /data/ssd/testData/:/data/ssd/testData/'
                }
            }
            steps {
                echo "Launch GPT Tests from ${env.JOB_NAME} from ${env.GIT_BRANCH} with commit ${env.GIT_COMMIT} using docker image snap-build-server.tilaa.cloud/${params.dockerTagName}"
                sh "mvn clean install"
                sh "java -jar target/filterJson.jar ${params.testScope} ${params.dockerTagName}"
            }
        }
    }
    stages {
        stage('Json Executer') {
            when {
                expression {
                    return "${params.jsonPath}" == '';
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
                sh 'mvn install'
                sh 'java -jar target/snap-gpt-tests.jar ${params.testScope} ${params.dockerTagName}'
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
