```groovy
pipeline {
    agent any

    options {
        timestamps()
    }

    stages {
        stage('Install Dependencies') {
            steps {
                bat 'python -m pip install -r requirements.txt'
                bat 'if not exist reports mkdir reports'
            }
        }

        stage('Start Selenium Grid') {
            steps {
                bat 'docker compose up -d'
                bat 'python wait_grid.py'
                bat 'docker compose ps'
            }
        }

        stage('Cross-Browser Tests') {
            parallel {
                stage('Chrome Tests') {
                    steps {
                        withEnv([
                            'BROWSER=chrome',
                            'SCREENSHOT_DIR=screenshots/chrome'
                        ]) {
                            bat 'python -m pytest -v -s test_booking.py --junitxml=reports/chrome.xml'
                        }
                    }
                    post {
                        always {
                            junit(
                                testResults: 'reports/chrome.xml',
                                allowEmptyResults: true
                            )
                        }
                    }
                }

                stage('Firefox Tests') {
                    steps {
                        withEnv([
                            'BROWSER=firefox',
                            'SCREENSHOT_DIR=screenshots/firefox'
                        ]) {
                            bat 'python -m pytest -v -s test_booking.py --junitxml=reports/firefox.xml'
                        }
                    }
                    post {
                        always {
                            junit(
                                testResults: 'reports/firefox.xml',
                                allowEmptyResults: true
                            )
                        }
                    }
                }
            }
        }
    }

    post {
        always {
            archiveArtifacts(
                artifacts: 'screenshots/**/*.png,reports/*.xml',
                allowEmptyArchive: true,
                fingerprint: true
            )

            bat(
                script: 'docker compose down',
                returnStatus: true
            )
        }
    }
}
```