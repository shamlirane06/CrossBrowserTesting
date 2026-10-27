```groovy
pipeline {
    agent any

    environment {
        PYTHON = 'C:\\Users\\Shamli Rane\\AppData\\Local\\Python\\pythoncore-3.15-64\\python.exe'
        DOCKER = 'C:\\Users\\Shamli Rane\\AppData\\Local\\Programs\\DockerDesktop\\resources\\bin\\docker.exe'
    }

    options {
        timestamps()
    }

    stages {
        stage('Install Dependencies') {
            steps {
                bat '"%PYTHON%" -m pip install -r requirements.txt'
                bat 'if not exist reports mkdir reports'
            }
        }

        stage('Start Selenium Grid') {
            steps {
                bat '"%DOCKER%" compose up -d'
                bat '"%PYTHON%" wait_grid.py'
                bat '"%DOCKER%" compose ps'
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
                            bat '"%PYTHON%" -m pytest -v -s test_booking.py --junitxml=reports/chrome.xml'
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
                            bat '"%PYTHON%" -m pytest -v -s test_booking.py --junitxml=reports/firefox.xml'
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
                script: '"%DOCKER%" compose down',
                returnStatus: true
            )
        }
    }
}
```